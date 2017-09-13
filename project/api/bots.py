import datetime

from flask import Blueprint, jsonify, request, render_template

from project.api.models.users import User
from project.api.models.bots import Bot
from project import db
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

bots_blueprint = Blueprint('bots', __name__, template_folder='./templates')

@bots_blueprint.route('/api/bots/<int:id>', methods=['PUT'])
def update_bots(id):
    code, user_id = checkAuth(request)
    if code == 200:
        bot = Bot.query.filter_by(user_id=user_id).first()
        if not bot:
            return jsonify({"error":"Bot Not Found"}),404
        if bot.user_id == user_id:
            bot.used = datetime.datetime.now()
            try:
                db.session.commit()
            except Exception as inst:
                error = type(inst).__name__
                return jsonify({'errors':error}),400
            return jsonify({"success":True})
        else:
            return jsonify({"error":"Unauthorized"}),401
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
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
                bot_obj['used'] = (bot.used - datetime.datetime(1970, 1, 1)).total_seconds()

                bots_obj.append(bot_obj)
            return jsonify({"bots":bots_obj})
        elif code == 400:
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            return jsonify({"error":"No Authorization Token Sent"}),401
    elif request.method == 'POST':
        code,user_id = checkAuth(request)
        post_data = request.get_json()
        if not post_data:
            response_object = {
                'status': 'fail',
                'message': 'Invalid payload.'
            }
            return jsonify(response_object), 400
        name = post_data.get('name')

        if code == 200:
            bot = Bot(
                    user_id=user_id,
                    name=name
                )
            db.session.add(bot)
            db.session.commit()
            return jsonify({'success':True}),200
        elif code == 400:
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            return jsonify({"error":"No Authorization Token Sent"}),401