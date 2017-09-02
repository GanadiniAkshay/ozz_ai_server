import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.intents import Intent 
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

intents_blueprint = Blueprint('intents', __name__, template_folder='./templates')

@intents_blueprint.route('/intents/<bot_guid>', methods=['GET','POST'])
def intents(bot_guid):
    # code,user_id = checkAuth(request)
    code = 200
    user_id = 16
    if code == 200:
        global interpreters
        nlus = interpreters
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'GET':
                    intents = Intent.query.filter_by(bot_guid=bot_guid)
                    model = bot.active_model
                    nlu = nlus[model]
                    intents_obj = []
                    for intent in intents:
                        intent_obj = {}
                        intent_obj['name'] = intent.name
                        intent_obj['utterances'] = []
                        for utterance in intent.utterances:
                            int, entities = nlu.parse(utterance)
                            intent_obj['utterances'].append({"utterance":utterance,"entities":entities})
                        intents_obj.append(intent_obj)
                    return jsonify({"intents":intents_obj})
                elif request.method == 'POST':
                    post_data = request.get_json()
                    if not post_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        return jsonify(response_object), 400
                    else:
                        name = post_data.get('name')
                        utterances = post_data.get('utterances')
                        has_entities = post_data.get('has_entities')
                        
                        intent = Intent.query.filter_by(name=name).first()
                        if intent:
                            intent.utterances = utterances
                            intent.has_entities = has_entities
                        else:
                            intent = Intent(
                                name = name,
                                bot_guid=bot_guid,
                                utterances=utterances,
                                has_entities=has_entities
                            )
                            db.session.add(intent)
                        try:
                            db.session.commit()
                        except Exception as e:
                            return jsonify({"success":False})
                        return jsonify({"success":"true"})
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401


