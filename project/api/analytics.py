import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.analytics import Analytics
from project.api.models.intents import Intent
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.shared.checkAuth import checkAuth
from project.config import DevelopmentConfig
from project.keys import super_secret

analytics_blueprint = Blueprint('analytics', __name__, template_folder='./templates')

@analytics_blueprint.route('/api/analytics/<bot_guid>', methods=['GET'])
def analytics(bot_guid):
    code,user_id = checkAuth(request)
    # code = 200
    # user_id = 16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if request.method == 'GET':
                if bot.user_id == user_id:
                    analytics_logs = Analytics.query.filter_by(bot_guid=bot_guid).all()
                    intents = Intent.query.filter_by(bot_guid=bot_guid).all()

                    intent_count = {}
                    for intent in intents:
                        intent_count[intent.name] = 0
                    
                    calls = 0
                    success_count = 0.0
                    resp_time = 0.0
                    times = []
                    for log in analytics_logs:
                        if log.confident:
                            success_count += 1.0
                        if log.intent in intent_count:
                            intent_count[log.intent] += 1
                        resp_time += float(log.response_time)
                        calls += 1
                        times.append(log.created)
                    avg_resp_time = float("{:.3f}".format(resp_time/calls)) 
                    success_percentage = float("{:.3f}".format((success_count/calls) * 100))
                    return jsonify({"calls":calls,"avg_resp_time":avg_resp_time,"success_percentage":success_percentage,"intent_count":intent_count,"times":times})
                else:
                    return jsonify({"error":"Not Authorized"}),401
            else:
                return jsonify({"error":"Not Authorized"}),401
        else:
            return jsonify({"error":"Bot Doesn't exist"}),404
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401