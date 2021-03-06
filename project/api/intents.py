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

intents_blueprint = Blueprint('intents', __name__, template_folder='./templates')

@intents_blueprint.route('/api/intents_is_folder/<bot_guid>/<intent_name>', methods=['GET'])
def intent_is_folder(bot_guid,intent_name):
    bot = Bot.query.filter_by(bot_guid=bot_guid).first()
    if bot:
        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
        if intent:
            app.logger.info('GET /api/intents_is_folder/'+bot_guid+ '/'+ intent_name+ ' successfully returned intent is folder status')
            return jsonify({"is_folder": intent.is_folder})
        else:
            folders = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(intent_name+".%")).all()
            if folders:
                app.logger.info('GET /api/intents_is_folder/'+bot_guid+ '/'+ intent_name+ ' successfully returned intent is folder status')
                return jsonify({"is_folder": True})
            else:
                app.logger.warning('GET /api/intents_is_folder/'+bot_guid+ '/'+ intent_name+ ' intent does not exist')
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
                            intent_obj['utterances'].append({"utterance":utterance,"entities":[]})
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('GET /api/intents/'+bot_guid+ '/'+ intent_name+ ' ' + str(e))
                            return jsonify({"success":False,'errors':str(e)}),400
                        app.logger.info('GET /api/intents/'+bot_guid+ '/'+ intent_name+ ' successfully returned intent information')
                        return jsonify(intent_obj)
                else:
                   app.logger.warning('/api/intents/'+bot_guid+ '/'+ intent_name+ ' intent does not exist')
                   return jsonify({"error":"Intent Doesn't exist"}),404 
            else:
                app.logger.warning('/api/intents/'+bot_guid+ '/'+ intent_name+ ' not authorized')
                return jsonify({"error":"Not Authorized"}),401
        else:
            app.logger.warning('/api/intents/'+bot_guid+ '/'+ intent_name+ ' bot does not exist')
            return jsonify({"error":"Bot Doesn't exist"}),404
    elif code == 400:
        app.logger.warning('/api/intents/'+bot_guid+ '/'+ intent_name+ ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/intents/'+bot_guid+ '/'+ intent_name+ ' authorization token not sent')
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
                            if not base_pattern == '/':
                                folder_name = folders[len(base_pattern[:-2].split('.'))]
                            else:
                                folder_name = folders[0]
                            if folders[-1] == folder_name:
                                is_folder = intent.is_folder
                            else:
                                is_folder = True
                            if not folder_name in folder_list:
                                if base_pattern == '/':
                                    pattern = folder_name +'.%'
                                else:
                                    pattern = base_pattern[:-1] + folder_name + '.%'
                                contents = Intent.query.filter_by(bot_guid=bot_guid).filter_by(is_folder=False).filter(Intent.name.like(pattern)).all()
                                folder_list[folder_name] = intent.modified
                                intent_obj['name'] = folder_name
                                intent_obj['is_folder'] = is_folder
                                intent_obj['count'] = len(contents)
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
                    app.logger.info('GET /api/intents/'+bot_guid+ ' successfully returned list of intents')
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
                            app.logger.error('POST /api/intents/'+bot_guid+ ' ' + str(e))
                            return jsonify({"success":False,"errors":str(e)})
                        app.logger.info('POST /api/intents/'+bot_guid+ ' successfully added intent')
                        return jsonify({"success":True})
                elif request.method == 'PUT':
                    put_data = request.get_json()
                    if not put_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        app.logger.warning('PUT /api/intents/'+bot_guid+ ' invalid put object')
                        return jsonify(response_object), 400
                    else:
                        old_name = put_data['old_name']
                        new_name = put_data['new_name']

                        if old_name[-1] == "%":
                            intents = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(old_name)).all()
                            for intent in intents:
                                name = intent.name
                                intent.name = name.replace(old_name[:-1],new_name)
                                intent.modified = datetime.datetime.utcnow()
                                try:
                                    db.session.commit()
                                except Exception as e:
                                    app.logger.error('PUT /api/intents/'+bot_guid+ ' ' + str(e))
                                    return jsonify({"success":False})
                            app.logger.info('PUT /api/intents/'+bot_guid+ ' successfully updated intent')
                            return jsonify({"success":True})
                        else:
                            intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=old_name).first()
                            if intent:
                                intent.name = new_name
                                intent.modified = datetime.datetime.utcnow()
                                try:
                                    db.session.commit()
                                except Exception as e:
                                    app.logger.error('PUT /api/intents/'+bot_guid+ ' ' + str(e))
                                    return jsonify({"success":False})
                                app.logger.info('GET /api/intents/'+bot_guid+ ' successfully updated intent')
                                return jsonify({"success":True})
                            else:
                                app.logger.warning('PUT /api/intents/'+bot_guid+ ' intent does not exist')
                                return jsonify({"success":False,"errors":"Intent doesn't exist"})
                elif request.method == 'DELETE':
                    intent_name = request.args['intent']
                    if intent_name[0] == '.':
                        intent_name = intent_name[1:]
                    if intent_name[-1] == '%':
                        try:
                            query = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(intent_name))
                            query.delete(synchronize_session=False)
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('DELETE /api/intents/'+bot_guid+ ' ' + str(e))
                            return jsonify({"success":False,"errors":str(e)})
                        app.logger.info('DELETE /api/intents/'+bot_guid+ ' successfully deleted intent')
                        return jsonify({"success":True})
                    else:
                        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                        if intent:
                            db.session.delete(intent)
                            try:
                                db.session.commit()
                            except Exception as e:
                                app.logger.error('DELETE /api/intents/'+bot_guid+ ' ' + str(e))
                                return jsonify({"success":False,"errors":str(e)})
                            app.logger.info('DELETE /api/intents/'+bot_guid+ ' successfully deleted intent')
                            return jsonify({"success":True})
                        else:
                            app.logger.warning('DELETE /api/intents/'+bot_guid+ ' intent does not exist')
                            return jsonify({"success":False,"errors":"intent doesn't exist"})
    elif code == 400:
        app.logger.warning('/api/intents/'+bot_guid+ ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/intents/'+bot_guid+ ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401


@intents_blueprint.route('/api/folders/<bot_guid>', methods=['DELETE'])
def folders(bot_guid):
    code,user_id = checkAuth(request)
    print(code)
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'DELETE':
                    folders = request.args.getlist('folders[]')
                    base = request.args['base']
                    print(base)
                    try:
                        for folder in folders:
                            pres = '.'.join(base.split('/')[1:])
                            if base != '/':
                                folder = pres + '.' + folder
                        
                            intent_name = folder + '%'
                            query = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like(intent_name))
                            query.delete(synchronize_session=False)
                        db.session.commit()
                    except Exception as e:
                        app.logger.error('DELETE /api/folders/'+bot_guid+ ' ' + str(e))
                        return jsonify({"success":False,"errors":str(e)})
                    app.logger.info('DELETE /api/folders/'+bot_guid+ ' successfully deleted folder')
                    return jsonify({"success":True})
                else:
                    app.logger.warning('/api/folders/'+bot_guid+ ' method not allowed')
                    return jsonify({"error":"Method Not Allowed"}),405
            else:
                app.logger.warning('/api/folders/'+bot_guid+ ' not authorized')
                return jsonify({"error":"Not Authorized"}),401
        else:
            app.logger.warning('/api/folders/'+bot_guid+ ' bot not found')
            return jsonify({"error":"Bot Not Found"}),404
    elif code == 400:
        app.logger.warning('/api/folders/'+bot_guid+ ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/folders/'+bot_guid+ ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401


