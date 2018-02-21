import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.intents import Intent 
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d, app
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

responses_blueprint = Blueprint('responses', __name__, template_folder='./templates')


@responses_blueprint.route('/api/intents/<bot_guid>/<intent_name>/responses', methods=['POST','PUT','DELETE'])
def response(bot_guid,intent_name):
    code,user_id = checkAuth(request)
    # code = 200
    # user_id = 16
    if code == 200:
        global interpreters
        nlus = interpreters
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                if intent:
                    intent.modified = datetime.datetime.utcnow()
                    if request.method == 'POST':
                        post_data = request.get_json()
                        new_response = post_data['value']

                        if new_response in intent.responses:
                            return jsonify({})
                        else:
                            resps = [new_response] + intent.responses
                            intent.responses = [r for r in resps]
                            try:
                                db.session.commit()
                            except Exception as e:
                                app.logger.error('POST /api/intents/'+ bot_guid + '/' + intent_name + '/responses ' + str(e))
                                return jsonify({"success":False,"errors":str(e)})
                            app.logger.info('POST /api/intents/'+ bot_guid + '/' + intent_name + '/responses successfully added response')
                            return jsonify({"success":True})
                    elif request.method == 'PUT':
                        put_data = request.get_json()
                        old_response = put_data['old_response']
                        new_response = put_data['value']
                        intent.responses = [new_response if u == old_response else u for u in intent.responses]
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('PUT /api/intents/'+ bot_guid + '/' + intent_name + '/responses ' + str(e))
                            return jsonify({"success":False,"errors":str(e)})
                        app.logger.info('PUT /api/intents/'+ bot_guid + '/' + intent_name + '/responses successfully updated response')
                        return jsonify({"success":True})
                    elif request.method == 'DELETE':
                        old_response = request.args['response']
                        new_responses = []
                        for response in intent.responses:
                            if (response != old_response):
                                new_responses.append(response)
                        intent.responses = new_responses
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('DELETE /api/intents/'+ bot_guid + '/' + intent_name + '/responses ' + str(e))
                            return jsonify({"success":False,"errors":str(e)})
                        app.logger.info('DELETE /api/intents/'+ bot_guid + '/' + intent_name + '/responses successfully deleted response')
                        return jsonify({"success":True})
                else:
                    app.logger.warning('/api/intents/'+ bot_guid + '/' + intent_name + '/responses intent does not exist')
                    return jsonify({"error":"Intent Doesn't exist"}),404 
    elif code == 400:
        app.logger.warning('/api/intents/'+ bot_guid + '/' + intent_name + '/responses invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/intents/'+ bot_guid + '/' + intent_name + '/responses no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

