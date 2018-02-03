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

@intents_blueprint.route('/api/intents_is_folder/<bot_guid>/<intent_name>', methods=['GET'])
def intent_is_folder(bot_guid,intent_name):
    bot = Bot.query.filter_by(bot_guid=bot_guid).first()
    if bot:
        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
        if intent:
            return jsonify({"is_folder": intent.is_folder})
        else:
            folders = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(intent_name+".%")).all()
            if folders:
                return jsonify({"is_folder": True})
            else:
                return jsonify({"error":"Intent Doesn't exist"}),404 

@intents_blueprint.route('/api/intents/<bot_guid>/<intent_name>', methods=['GET','PUT'])
def intent(bot_guid,intent_name):
    code,user_id = checkAuth(request)
    if code == 200:
        global interpreters
        nlus = interpreters
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                if intent:
                    model = bot.active_model
                    if model:
                        nlu = nlus[model]
                    else:
                        nlu = None
                    if request.method == 'GET':
                        intent_obj = {}
                        intent_obj['is_folder'] = False
                        intent_obj['responses'] = intent.responses
                        intent_obj['utterances'] = []
                        for utterance in intent.utterances:
                            if nlu:
                                int, entities, confidence = nlu.parse(utterance)
                            else:
                                entities = []
                            intent_obj['utterances'].append({"utterance":utterance,"entities":entities})
                        try:
                            db.session.commit()
                        except Exception as inst:
                            error = type(inst).__name__
                            return jsonify({'errors':error}),400
                        return jsonify(intent_obj)
                else:
                   return jsonify({"error":"Intent Doesn't exist"}),404 
            else:
                return jsonify({"error":"Not Authorized"}),401
        else:
            return jsonify({"error":"Bot Doesn't exist"}),404
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401


@intents_blueprint.route('/api/intents/<bot_guid>', methods=['GET','POST','PUT','DELETE'])
def intents(bot_guid):
    code,user_id = checkAuth(request)
    if code == 200:
        global interpreters
        nlus = interpreters
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        base = request.args.get('base')
        if not base:
            base = '/'
        if bot:
            if bot.user_id == user_id:
                if request.method == 'GET':
                    if base == '/':
                        intents = Intent.query.filter_by(bot_guid=bot_guid)
                        base_pattern = '/'
                    else:
                        base_pattern = '.'.join(base[1:].split('/')) + '.%'
                        intents = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(base_pattern)).all()
                    intents_obj = []
                    empty_folders = []
                    folder_list = {}
                    for intent in intents:
                        intent_obj = {}
                        folders = intent.name.split('.')
                        if len(folders) > 1:
                            pattern = '.'.join(folders[:-1])+'.%'
                            if not base_pattern == '/':
                                folder_name = folders[len(base_pattern[:-2].split('.'))]
                            else:
                                folder_name = folders[0]
                            if folders[-1] == folder_name:
                                is_folder = intent.is_folder
                            else:
                                is_folder = True
                            if not folder_name in folder_list:
                                folder_list[folder_name] = intent.modified
                                matched_intents = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(pattern)).all()
                                intent_obj['name'] = folder_name
                                intent_obj['is_folder'] = is_folder
                                intent_obj['count'] = len(matched_intents)
                                intent_obj['utterances'] = len(intent.utterances)
                                intent_obj['responses'] = len(intent.responses)
                                intent_obj['patterns'] = len(intent.patterns)
                                intent_obj['calls'] = intent.calls
                                intent_obj['modified'] = intent.modified
                                intents_obj.append(intent_obj)
                        else:
                            intent_obj['is_folder'] = intent.is_folder
                            intent_obj['name'] = intent.name
                            intent_obj['count'] = 0
                            intent_obj['utterances'] = len(intent.utterances)
                            intent_obj['responses'] = len(intent.responses)
                            intent_obj['patterns'] = len(intent.patterns)
                            intent_obj['calls'] = intent.calls
                            intent_obj['modified'] = intent.modified
                            if not intent.is_folder:
                                intents_obj.append(intent_obj)
                            else:
                                empty_folders.append(intent_obj)
                    for folder in empty_folders:
                        if not (folder['name'] in folder_list):
                            intents_obj.append(folder)
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
                        if base == '/':
                            prefix = ''
                        else: 
                            prefix = '.'.join(base[1:].split('/'))+'.'
                        name = prefix + post_data.get('name')
                        utterances = post_data.get('utterances')
                        responses = post_data.get('responses')
                        has_entities = post_data.get('has_entities')
                        is_folder = post_data.get('is_folder')

                        
                        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=name).filter_by(is_folder=is_folder).first()
                        if intent:
                            return jsonify({"success":False,"error":"An intent with that name already exists"})
                        else:
                            intent = Intent(
                                name = name,
                                bot_guid=bot_guid,
                                utterances=utterances,
                                has_entities=has_entities,
                                responses = responses,
                                is_folder=is_folder,
                                patterns=[]
                            )
                            db.session.add(intent)
                        try:
                            db.session.commit()
                        except Exception as e:
                            return jsonify({"success":False})
                        return jsonify({"success":"true"})
                elif request.method == 'PUT':
                    put_data = request.get_json()
                    if not put_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        return jsonify(response_object), 400
                    else:
                        old_name = put_data['old_name']
                        new_name = put_data['new_name']
                        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=old_name).first()
                        if intent:
                            intent.name = new_name
                            try:
                                db.session.commit()
                            except Exception as e:
                                return jsonify({"success":"false"})
                            return jsonify({"success":"true"})
                        else:
                            return jsonify({"success":"false"})
                elif request.method == 'DELETE':
                    intent_name = request.args['intent']
                    intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                    if intent:
                        db.session.delete(intent)
                        try:
                            db.session.commit()
                        except Exception as e:
                            return jsonify({"success":"false"})
                        return jsonify({"success":"true"})
                    else:
                        return jsonify({"success":"false"})
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401


