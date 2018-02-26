import datetime
import json
from flask import Blueprint, jsonify, request, render_template

from project.api.models.users import User
from project.api.models.bots import Bot
from project import db, app
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

bots_blueprint = Blueprint('bots', __name__, template_folder='./templates')

@bots_blueprint.route('/api/bots/<string:bot_guid>/persona', methods=['GET','PUT'])
def persona(bot_guid):
    code, user_id = checkAuth(request)
    # code = 200
    # user_id = 16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if not bot:
            return jsonify({"error":"Bot Not Found"}),404
        if bot.user_id == user_id:
            if request.method == 'GET':
                return jsonify({"persona":bot.persona})
            elif request.method == 'PUT':
                put_data = request.get_json()
                try:
                    bot.persona = put_data['persona']
                    db.session.commit()
                except Exception as e:
                    app.logger.error('GET /api/bots/' + bot_guid + '/persona ' + str(e))
                    return jsonify({"success":False,"error":str(e)})
                app.logger.info('GET /api/bots/' + bot_guid + '/persona returned persona')
                return jsonify({"persona":bot.persona})
        else:
            app.logger.warning('/api/bots/' + bot_guid + '/persona Unauthorized')
            return jsonify({"error":"Unauthorized"}),401
    elif code == 400:
        app.logger.warning('/api/bots/' + bot_guid + '/persona Invalid Authorization Token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/bots/' + bot_guid + '/persona No Authorization Token Sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

@bots_blueprint.route('/api/bots/<string:bot_guid>', methods=['PUT','DELETE'])
def update_bots(bot_guid):
    code, user_id = checkAuth(request)
    # code = 200
    # user_id = 16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if not bot:
            app.logger.warning('/api/bots/'+bot_guid+' Bot Not Found')
            return jsonify({"error":"Bot Not Found"}),404
        if bot.user_id == user_id:
            if request.method == 'PUT':
                put_data = request.get_json()
                bot.persona = put_data['persona']
                bot.used = datetime.datetime.utcnow()
                try:
                    db.session.commit()
                except Exception as e:
                    app.logger.error('PUT /api/bots/'+bot_guid+' '+str(e))
                    return jsonify({'errors':str(e)}),400
                app.logger.info('PUT /api/bots/'+bot_guid+' bot updated successfully')
                return jsonify({"success":True})
            elif request.method == 'DELETE':
                try:
                    db.session.delete(bot)
                    db.session.commit()
                except Exception as e:
                    app.logger.error('DELETE /api/bots/'+bot_guid+' '+str(e))
                    return jsonify({'errors':str(e)}),400
                bots = Bot.query.filter_by(user_id=user_id)
                bots_obj = []
                for bot in bots:
                    bot_obj = {}
                    bot_obj['id'] = bot.id
                    bot_obj['bot_guid'] = bot.bot_guid
                    bot_obj['user_id'] = bot.user_id
                    bot_obj['name'] = bot.name
                    bot_obj['used'] = (bot.used - datetime.datetime(1970, 1, 1)).total_seconds()

                    bots_obj.append(bot_obj)
                app.logger.info('DELETE /api/bots/'+bot_guid+' bot deleted successfully')
                return jsonify({"bots":bots_obj})
        else:
            app.logger.warning('/api/bots/'+bot_guid+' unauthorized')
            return jsonify({"error":"Unauthorized"}),401
    elif code == 400:
        app.logger.warning('/api/bots/'+bot_guid+' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/bots/'+bot_guid+' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

@bots_blueprint.route('/api/bots', methods=['GET','POST'])
def bots():
    if request.method == 'GET':
        code,user_id = checkAuth(request)
        if code == 200:
            bots = Bot.query.filter_by(user_id=user_id)
            bots_obj = []
            for bot in bots:
                bot_obj = {}
                bot_obj['id'] = bot.id
                bot_obj['bot_guid'] = bot.bot_guid
                bot_obj['user_id'] = bot.user_id
                bot_obj['name'] = bot.name
                bot_obj['persona'] = bot.persona
                bot_obj['last_trained'] = bot.last_trained
                bot_obj['used'] = (bot.used - datetime.datetime(1970, 1, 1)).total_seconds()

                bots_obj.append(bot_obj)
            app.logger.info('GET /api/bots list of bots returned successfully')
            return jsonify({"bots":bots_obj})
        elif code == 400:
            app.logger.warning('GET /api/bots invalid authorization token')
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            app.logger.warning('GET /api/bots no authorization token sent')
            return jsonify({"error":"No Authorization Token Sent"}),401
    elif request.method == 'POST':
        code,user_id = checkAuth(request)
        post_data = request.get_json()
        if not post_data:
            response_object = {
                'status': 'fail',
                'message': 'Invalid payload.'
            }
            app.logger.warning('POST /api/bots post object invalid')
            return jsonify(response_object), 400
        name = post_data.get('name')

        if code == 200:
            bot = Bot(
                    user_id=user_id,
                    name=name.lower(),
                    words = json.dumps({})
                )
            db.session.add(bot)
            try:
                db.session.commit()
            except Exception as e:
                app.logger.error('POST /api/bots ' + str(e))
                return jsonify({"success":False,"error":str(e)})
            app.logger.info('POST /api/bots bot added successfully')
            return jsonify({'success':True}),200
        elif code == 400:
            app.logger.warning('POST /api/bots invalid authorization token')
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            app.logger.warning('POST /api/bots no authorization token sent')
            return jsonify({"error":"No Authorization Token Sent"}),401