import datetime

from flask import Blueprint, jsonify, request, render_template

from project.api.models.entities import Entity 
from project.api.models.bots import Bot
from project import db
from sqlalchemy import exc
from sqlalchemy.orm.attributes import flag_modified

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

syn_blueprint = Blueprint('synonyms', __name__, template_folder='./templates')

@syn_blueprint.route('/api/entities/<bot_guid>/<entity_name>/<example_name>', methods=['POST','DELETE'])
def syn(bot_guid,entity_name,example_name):
    code,user_id = checkAuth(request)
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'POST':
                    post_data = request.get_json()
                    if not post_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        return jsonify(response_object), 400
                    else:
                        entity= Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                        if entity:
                            synonym = post_data['synonym']
                            if example_name in entity.examples:
                                entity.examples[example_name].append(synonym)
                                flag_modified(entity, "examples")
                            try:
                                db.session.commit()
                            except Exception as e:
                                return jsonify({"success":"false"})
                            return jsonify({"success":"true"})
                elif request.method == 'DELETE':
                    print('here')
                    entity= Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                    if entity:
                        synonym = request.args['synonym']
                        if example_name in entity.examples:
                            entity.examples[example_name].remove(synonym)
                            flag_modified(entity, "examples")
                        try:
                            db.session.commit()
                        except Exception as e:
                            return jsonify({"success":"false"})
                        return jsonify({"success":"true"})
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401