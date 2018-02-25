from __future__ import absolute_import
from __future__ import print_function

from flask import Blueprint, request, jsonify, render_template
from project.helpers.parser import NLUParser
from subprocess import call
from werkzeug import secure_filename

from project.api.models.users import User
from project.api.models.bots import Bot
from project.api.models.intents import Intent
from project.api.models.entities import Entity
from project.api.models.analytics import Analytics
from project.api.models.knowledge import Knowledge
from project import db, cache, interpreters, trainer, nlp, d, q, redis_db, stopWords, app
from sqlalchemy import exc
from sqlalchemy.orm.attributes import flag_modified

from project.shared.checkAuth import checkAuth
from project.helpers.trainer import load_train_data
from project.helpers.eliza import Eliza

from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer, Metadata, Interpreter

import mitie
import os
import json
import sys
import urllib
import tarfile
import shutil
import time
import random
import re
import operator
import csv
import codecs
import ast

nlu_blueprint = Blueprint('nlu', __name__, template_folder='./templates')


@nlu_blueprint.route('/api/parse/<bot_guid>', methods=['GET','POST'])
def parse(bot_guid):
    start_time = time.time()
    global interpreters
    nlus = interpreters
    config = './project/config.json'

    if request.method == 'GET':
        message = request.args.get('q')
    elif request.method == 'POST':
        post_data = request.get_json()
        message = post_data['q']
    if type(message) != str:
        message = message.decode('utf-8')

    bot = Bot.query.filter_by(bot_guid=bot_guid).first()
    if bot:
        model = bot.active_model
        words_json = json.loads(bot.words)
        key = bot_guid+"_"+message
        if redis_db.exists(key):
            event = redis_db.hgetall(key)
            intent = str(event[b'intent'],'utf-8')
            print('redis')
            print(intent)
            is_ozz = intent.split('.')[0] == 'ozz'
            if not is_ozz:
                entities = ast.literal_eval(str(event[b'entities'],'utf-8'))
                response = ""
                intent_obj = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent).first()
                if intent_obj:
                    intent_obj.calls += 1
                    if (len(intent_obj.responses) > 0):
                        response = random.choice(intent_obj.responses)
                end_time =time.time()
                print(str(end_time - start_time))
                app.logger.info('/api/parse/'+ bot_guid + ' parsed intents and entities ' + str(end_time - start_time))
                return jsonify({"intent":intent,"entities":entities,"response":response})

        if type(words_json) == str:
            words_json = {}
        if model:
            nlu = nlus[model]
        else:
            app.logger.error('/api/parse/'+ bot_guid + ' bot not trained')
            return jsonify({"error":"Please train the bot before testing"})
    else:
        app.logger.warning('/api/parse/'+ bot_guid + ' bot does not exist')
        return jsonify({"error":"Bot doesn't exist"}),404

    message = message.lower()

    regex_match = False
    intents = Intent.query.filter_by(bot_guid=bot_guid)
    entities = []
    response = ""
    is_matched = False
    for intent_obj in intents:
        if is_matched:
            break
        patterns = intent_obj.patterns
        for pattern in patterns:
            pattern = json.loads(pattern)
            if (intent_obj.name[:5] == 'eliza'):
                regex = pattern["regex"]
            else:
                regex = pattern["regex"].lower().strip()
            if len(regex) > 0:
                express = re.compile(regex,re.IGNORECASE)
                match = express.match(message)
            else:
                match = False
            if match:
                is_matched = True
                intent = intent_obj.name
                print("regex")
                print(intent)
                intent_obj.calls += 1
                db.session.commit()
                regex_match = True
                entity_start = 0
                entity_end = -1
                parameters = pattern['entities']
                ents ={}
                for parameter in parameters:
                    if parameter['first'] != -1:
                        entity_start = parameter['first']
                        if parameter['post'] and parameter['post'] in message:
                            entity_end = entity_start + message[entity_start:].index(parameter['post'])
                        if entity_end == -1:
                            entity_value = message[entity_start:]
                        else:
                            entity_value = message[entity_start:entity_end]
                        ents[parameter['entity'][1:]] = entity_value
                        entities.append({"entity":parameter['entity'][1:],"value":entity_value,"type":"regex","start":entity_start, "end":entity_start + len(entity_value)})
                    else:
                        mid_expression= message[entity_end:]
                        if parameter['prior'] and parameter['prior'] in mid_expression:
                            entity_start = mid_expression.index(parameter['prior']) + len(parameter['prior']) + 1
                        if parameter['post'] and parameter['post'] in mid_expression:
                            entity_end = mid_expression.index(parameter['post'])
                        else:
                            entity_end = -1
                        if entity_end == -1:
                            entity_value = mid_expression[entity_start:]
                        else:
                            entity_value = mid_expression[entity_start:entity_end]
                        start = message.index(entity_value)
                        entities.append({"entity":parameter['entity'][1:],"value":entity_value,"type":"regex","start":start,"end":start + len(entity_value)})
                if len(intent_obj.responses) > 0:
                    response = random.choice(intent_obj.responses)
                    resp_words = response.split(" ")
                    for word in resp_words:
                        if len(word)>0 and word[0] == '@':
                            ent = word[1:]

                            if ent[-1] == '?' or ent[-1] == '.':
                                ent = ent[:-1]
                                word = word[:-1]
                            if ent in ents:
                                response = response.replace(word,ents[ent])
                            else:
                                response = response.replace(word,"undefined")
                else:
                    response = ""
                break
    if not regex_match:
        intent, entities, confidence = nlu.parse(message)
        print("nlu")
        print(intent)
        response = ""
        # print(intent)
        print(confidence)
        if bot.persona and (bot.persona != -1 or bot.persona !=4):
            #print('here')
            persona_bot = Bot.query.filter_by(name='ozzpersonainternal7856').first()
            if persona_bot:
                persona_model = persona_bot.active_model
                persona_nlu = nlus[persona_model]

                ozz_intent, ozz_entities, ozz_confidence = persona_nlu.parse(message)
                print('persona')
                print(ozz_intent)
                print(ozz_confidence)
                if bot.persona == 1 and ozz_confidence > confidence:
                    intent, entities = ozz_intent, ozz_entities
                    with open(os.getcwd() + '/data/persona/millenial/millenial.json') as jsonFile:
                        responses = json.loads(jsonFile.read())
                    if intent in responses and len(responses[intent]) > 0:
                        response = random.choice(responses[intent])
                    else:
                        response = ""
                elif bot.persona == 2 and ozz_confidence > confidence:
                    intent, entities = ozz_intent, ozz_entities
                    with open(os.getcwd() + '/data/persona/average/average.json') as jsonFile:
                        responses = json.loads(jsonFile.read())
                    if intent in responses and len(responses[intent]) > 0:
                        response = random.choice(responses[intent])
                    else:
                        response = ""
                elif bot.persona == 3 and ozz_confidence > confidence:
                    intent, entities = ozz_intent, ozz_entities
                    with open(os.getcwd() + '/data/persona/professional/professional.json') as jsonFile:
                        responses = json.loads(jsonFile.read())
                    if intent in responses and len(responses[intent]) > 0:
                        response = random.choice(responses[intent])
                    else:
                        response = ""
        if intent != 'None':
            intent_obj = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent).first()
            if intent_obj:
                intent_obj.calls += 1
                if (len(intent_obj.responses) > 0):
                    response = random.choice(intent_obj.responses)
                db.session.commit()
        else:
            intent = "None"
            message_words = message.split(" ")
            scores = {}
            for word in message_words:
                if word in stopWords:
                    continue
                elif word in words_json:
                    intents = words_json[word]
                    for intent_key in intents:
                        if intent_key in scores:
                            scores[intent_key] += intents[intent_key]
                        else:
                            scores[intent_key] = intents[intent_key]

            scores = sorted(scores.items(),key = operator.itemgetter(1),reverse = True)

            if len(scores) > 0:
                intent = scores[0][0]
                print("words")
                print(intent)
                intent_obj = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent).first()
                if intent_obj:
                    intent_obj.calls += 1
                    if (len(intent_obj.responses) > 0):
                        response = random.choice(intent_obj.responses)
                    db.session.commit()
                    # else:
                    #     eliza = Eliza()
                    #     response = eliza.analyze(message)
    end_time = time.time()
    runtime = str(end_time - start_time)
    if intent == 'None':
        confident = False
    else:
        confident = True
    row = Analytics(
                message = message,
                bot_guid=bot_guid,
                intent=intent,
                response_time = runtime,
                confident=confident,
                entities= entities
            )
    db.session.add(row)
    db.session.commit()
    # redis_db.hmset(bot_guid + "_" + message,intent)
    key=bot_guid+"_"+message
    event = {}
    event["intent"] = intent
    event["entities"] = entities
    event["response"] = response
    redis_db.delete(key) #remove old keys
    redis_db.hmset(key, event)
    redis_db.expire(key, 259200)
    app.logger.info('/api/parse/'+ bot_guid + ' bot successfully parsed')
    return jsonify({"intent":intent,"entities":entities,"response":response})
    


@nlu_blueprint.route('/api/train/<bot_guid>', methods=['GET'])
def train(bot_guid):
    code,user_id = checkAuth(request)
    # code = 200
    # user_id = 16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                for key in redis_db.scan_iter(match=bot_guid+'_*'):
                    redis_db.delete(key)
                print('training')
                rasa_data = {
                                "rasa_nlu_data": 
                                    {   
                                        "common_examples": [
                                            {"text": "Nomnffl", "intent": "None", "entities": []}, 
                                            {"text": "Nekdg", "intent": "None", "entities": []}, 
                                            {"text": "Fesf", "intent": "None", "entities": []}, 
                                            {"text": "this is the this", "intent": "None", "entities": []}, 
                                            {"text": "likesdike mike", "intent": "None", "entities": []}
                                        ],
                                        "entity_synonyms": [],
                                        "regex_features":[]
                                    }
                            }
                intents = Intent.query.filter_by(bot_guid=bot_guid).filter(~Intent.name.like('eliza.%')).all()
                entities = Entity.query.filter_by(bot_guid=bot_guid)
                ent_data = {}
                words_json = {}
                for entity in entities:
                    ent_data[entity.name] = []
                    if type(entity.examples) == str:
                        entity.examples = json.loads(entity.examples)
                    for example_key in entity.examples:
                        ent_data[entity.name].extend(entity.examples[example_key])
                        rasa_data['rasa_nlu_data']['entity_synonyms'].append({"value":example_key,"synonyms":entity.examples[example_key]})
                for intent in intents:
                    for utterance in intent.utterances:
                        utt_copy = utterance
                        intent_name = intent.name
                        for word in stopWords:
                            utt_copy = utt_copy.replace(word," ")
                        
                        utt_words = utt_copy.split(" ")
                        
                        
                        for word in utt_words:
                            if word in words_json:
                                if intent_name in words_json[word]:
                                    words_json[word][intent_name] += 1
                                else:
                                    words_json[word][intent_name] = 1
                            else:
                                words_json[word] = {intent_name:1}

                        terminals = [] 
                        common_example = {}
                        common_example['text'] = utterance.lower()
                        common_example['intent'] = intent.name
                        common_example['entities'] = []
                        new_examples = []
                        new_values = []
                        for entity in entities:
                            if type(entity.examples) == str:
                                entity.examples = json.loads(entity.examples)
                            for example_key in entity.examples:
                                utterance = utterance.lower()
                                ent_examples = entity.examples[example_key]
                                # Used to consider key as well - but key is automatically added (not verified) when retreiving so these steps are not needed 
                                # if example_key.lower() not in ent_examples:
                                #     if example_key in ent_examples:
                                #         ent_examples.remove(example_key)
                                #     ent_examples.append(example_key.lower())
                                for example in ent_examples:
                                    example = example.lower()
                                    test_utterance = ' ' + utterance + ' '
                                    test_example  =' ' + example + ' '
                                    if test_example in test_utterance:
                                        #print("here")
                                        start = utterance.find(example)
                                        end = start + len(example)
                                        is_valid = True
                                        if len(terminals) > 0:
                                            mod_terminals = [x for x in terminals]
                                            for term_start, term_end, name, value in terminals:
                                                if term_start <= start and term_end >= end:
                                                    is_valid = False
                                                    continue
                                                
                                                if start <= term_start and end >= term_end:
                                                    mod_terminals.remove((term_start,term_end, name, value))
                                                    continue
                                            terminals = [x for x in terminals]
                                        if is_valid:
                                            terminals.append((start,end,entity.name,example))
                        for terminal in terminals:
                            common_example['entities'].append({"start":terminal[0],"end":terminal[1],"entity":terminal[2],"value":terminal[3]})
                            remaining_examples = ent_data[terminal[2]]
                            if terminal[3] in remaining_examples:
                                remaining_examples.remove(terminal[3])
                            values = generate(utterance,terminal[3],remaining_examples,intent.name,entities)
                            new_values += values
                        rasa_data['rasa_nlu_data']['common_examples'].append(common_example)
                        # rasa_data['rasa_nlu_data']['common_examples'] += new_values
                        # print(type(new_values))
                        # print(len(new_values))
                        # child_count = 0
                        # for val in new_values:
                        #     if type(val) == dict:
                        #         child_count += 1
                        # print(child_count)
                #print(rasa_data['rasa_nlu_data']['common_examples'])
                job = q.enqueue(train_bot,bot,rasa_data,words_json)
                print(job.get_id())
                app.logger.info('GET /api/train/'+ bot_guid + ' bot training started')
                return jsonify({"success":True})
                #train_bot(bot,rasa_data, words_json)
            else:
                app.logger.warning('GET /api/train/'+ bot_guid + ' not authorized')
                return jsonify({"error":"Not Authorized"}),401
        else:
            app.logger.warning('GET /api/train/'+ bot_guid + ' bot does not exist')
            return jsonify({"error":"Bot doesn't exist"}),404
    elif code == 400:
        app.logger.warning('GET /api/train/'+ bot_guid + ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('GET /api/train/'+ bot_guid + ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

@nlu_blueprint.route('/api/retrain',methods=['GET'])
def retrain():
    message = request.args.get('q')
    intent = request.args.get('i')
    if type(message) != str:
        message = message.decode('utf-8')
    path = os.path.join(os.getcwd(), 'data')
    with open(os.path.join(path, 'demo-data.json'),"r") as jsonFile:
        data = json.load(jsonFile)
    new_entity_example = {'text':message,'intent':intent, 'entities':[]}
    new_intent_example = {'text':message,'intent':intent}
    data["rasa_nlu_data"]["entity_examples"].append(new_entity_example)
    data["rasa_nlu_data"]["intent_examples"].append(new_intent_example)
    with open(os.path.join(path, 'demo-data.json'),"w") as jsonFile:
            json.dump(data, jsonFile)
    try:
        nlu.train()
    except Exception as e:
        app.logger.error('GET /api/retrain/'+ bot_guid + ' ' + str(e))
        return jsonify({"success":False,"error":str(e)})
    app.logger.info('GET /api/retrain/'+ bot_guid + ' bot successfully retrained')
    return jsonify({"success":True})

@nlu_blueprint.route('/api/download/<bot_guid>', methods=['GET'])
def download(bot_guid):
    code, user_id = checkAuth(request)
    # code, user_id = 200,16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                ozz_data = {"ozz_data":{"intents":[],"entities":[]}}
                intents = Intent.query.filter_by(bot_guid=bot_guid).all()
                entities = Entity.query.filter_by(bot_guid=bot_guid).all()
                
                for intent in intents:
                    intent_obj = {}
                    intent_obj['name'] = intent.name
                    intent_obj['utterances'] = intent.utterances
                    intent_obj['responses'] = intent.responses
                    intent_obj['patterns'] = intent.patterns
                    ozz_data['ozz_data']['intents'].append(intent_obj)
                
                for entity in entities:
                    ent_obj = {}
                    ent_obj['name'] = entity.name 
                    ent_obj['values'] = []
                    for value in entity.examples:
                        value_obj = {}
                        value_obj['name'] = value
                        value_obj['synonyms'] = entity.examples[value]
                        ent_obj['values'].append(value_obj)
                    
                    ozz_data['ozz_data']['entities'].append(ent_obj)
                app.logger.info('GET /api/download/'+ bot_guid + ' successfully downloaded ozz data')
                return jsonify(ozz_data)
            else:
                app.logger.warning('GET /api/download/'+ bot_guid + ' not authorized')
                return jsonify({"error":"Not Authorized"}),401
        else:
            app.logger.warning('GET /api/download/'+ bot_guid + ' bot does not exist')
            return jsonify({"error":"Bot doesn't exist"}),404
    elif code == 400:
        app.logger.warning('GET /api/download/'+ bot_guid + ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('GET /api/download/'+ bot_guid + ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

@nlu_blueprint.route('/api/import/<bot_guid>/<persona_type>',methods=['GET'])
def imp(bot_guid,persona_type):
    try:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            query = Intent.query.filter_by(bot_guid=bot_guid).filter(Intent.name.like('ozz.persona.%'))
            query.delete(synchronize_session=False)
            if persona_type == 'millenial':
                data = json.load(open(os.getcwd() + '/data/persona/millenial/import_persona_millenial.json'))
            elif persona_type == 'average':
                data = json.load(open(os.getcwd() + '/data/persona/average/import_persona_avg.json'))
            elif persona_type == 'professional':
                data = json.load(open(os.getcwd() + '/data/persona/professional/import_persona_professional.json'))
            load_from_json(data,bot,bot_guid)
            bot.persona = 4
            db.session.commit()
    except Exception as e:
        app.logger.error('GET /api/import/'+ bot_guid + ' ' + str(e))
        return jsonify({"success":False,"error":str(e)})
    app.logger.info('GET /api/import/'+ bot_guid + ' successfully imported ozz persona')
    return jsonify({"success":True})
        
@nlu_blueprint.route('/api/upload/<bot_guid>', methods=['POST'])
def upload(bot_guid):
    code,user_id = checkAuth(request)

    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                #Get the file information
                file = request.files['file']
                filename = secure_filename(file.filename)
                
                data = json.load(file)
                load_from_json(data,bot,bot_guid)
                app.logger.info('POST /api/upload/'+ bot_guid + ' successfully uploaded ozz data')
                return jsonify({"filename":filename,"type":file.content_type})
            else:
                app.logger.warning('POST /api/upload/'+ bot_guid + ' not authorized')
                return jsonify({"error":"Not Authorized"}),401
        else:
            app.logger.warning('POST /api/upload/'+ bot_guid + ' bot does not exist')
            return jsonify({"error":"Bot doesn't exist"}),404
    elif code == 400:
        app.logger.warning('POST /api/upload/'+ bot_guid + ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('POST /api/upload/'+ bot_guid + ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401


@nlu_blueprint.route('/api/upload_csv/<bot_guid>', methods=['POST'])
def uploadexcel(bot_guid):
    if request.method == 'POST':
        code,user_id = checkAuth(request)
        if code == 200:
            bot = Bot.query.filter_by(bot_guid=bot_guid).first()
            if bot:
                if bot.user_id == user_id:
                    tsv_file = request.files['file']
                    filename = secure_filename(tsv_file.filename)
                    tsv_file_read = tsv_file.readlines()
                    for row in tsv_file_read:
                        line = row.decode('utf-8')
                        
                        intent_name,questions,answers = line.split('\t')
                        questions = questions.split('<->')
                        answers = answers.split('<->')

                        questions = [ q for q in questions if len(q) > 0]
                        answers = [a for a in answers if len(a) > 0]

                        if intent_name == 'Intent' or intent_name == 'intent':
                            continue
                        else:
                            intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                            patterns = []
                            for utt_copy in questions:
                                if len(utt_copy) == 0:
                                    continue
                                parameters,regex = get_regex(utt_copy)
                                new_obj = {}
                                new_obj['string'] = utt_copy
                                new_obj['regex']  = regex
                                new_obj['entities'] = parameters
                                new_obj['len'] = len(utt_copy)
                                patterns.append(json.dumps(new_obj))
            
                                for word in stopWords:
                                    utt_copy = utt_copy.replace(word," ")
                                
                                utt_words = utt_copy.split(" ")

                                words_json = json.loads(bot.words) 
                                if type(words_json) == str:
                                    words_json = {}
                                for word in utt_words:
                                    if word in words_json:
                                        if intent_name in words_json[word]:
                                            words_json[word][intent_name] += 1
                                        else:
                                            words_json[word][intent_name] = 1
                                    else:
                                        words_json[word] = {intent_name:1}
                            try:
                                if intent:
                                    intent.utterances = questions
                                    intent.responses += answers
                                    intent.patterns = patterns
                                    flag_modified(intent, "utterances")
                                    flag_modified(intent, "responses")
                                    flag_modified(intent, "patterns")
                                    db.session.commit()
                                else:
                                    name = intent_name
                                    utterances = questions
                                    responses = answers
                                    has_entities = False
                                    intent = Intent(
                                        name = name,
                                        bot_guid=bot_guid,
                                        utterances=utterances,
                                        has_entities=has_entities,
                                        responses = responses,
                                        patterns=patterns
                                    )
                                    db.session.add(intent)
                                    db.session.commit()
                            except Exception as e:
                                app.logger.error('POST /api/upload_csv/'+ bot_guid + ' ' + str(e))
                                return jsonify({"success":False,"errors":str(e)})
                    app.logger.info('POST /api/upload_csv/'+ bot_guid + ' uploaded bot data from csv')
                    return jsonify({"success":True})
                else:
                    app.logger.warning('POST /api/upload_csv/'+ bot_guid + ' not authorized')
                    return jsonify({"error":"Not Authorized"}),401
            else:
                app.logger.warning('POST /api/upload_csv/'+ bot_guid + ' bot does not exist')
                return jsonify({"error":"Bot doesn't exist"}),404
        elif code == 400:
            app.logger.warning('POST /api/upload_csv/'+ bot_guid + ' invalid authorization token')
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            app.logger.warning('POST /api/upload_csv/'+ bot_guid + ' no authorization token sent')
            return jsonify({"error":"No Authorization Token Sent"}),401
    return render_template('file.html')


def train_bot(bot,rasa_data, words_json):
    try:
        config = './project/config.json'
        
        training_data = load_train_data(rasa_data)
        trainer.train(training_data)
        model_directory = trainer.persist('/var/lib/ozz/models')

        print(model_directory)

        result = {}
        result["words"] = json.dumps(words_json)
        result["active_model"] = str(model_directory)
        result["bot_guid"] = bot.bot_guid

        return json.dumps(result)
    except Exception as e:
        app.logger.error('GET /api/train/'+ bot.bot_guid + ' ' + str(e))

def generate(string,sub_string,values, intent_name, entities):
    new_values = []
    for value in values:
        utterance = string.replace(sub_string,value)
        common_example = {}
        common_example['text'] = utterance.lower()
        common_example['intent'] = intent_name
        common_example['entities'] = []
        for entity in entities:
            for example_key in entity.examples:
                utterance = utterance.lower()
                ent_examples = entity.examples[example_key]
                for example in ent_examples:
                    example = example.lower()
                    if example in utterance and example in utterance.split(' '):
                        start = utterance.find(example)
                        end = start + len(example)
                        value = example_key
                        ent_name = entity.name
                        common_example['entities'].append({"start":start,"end":end,"value":value,"entity":ent_name})
        new_values.append(common_example)
    return new_values

def load_from_json(data,bot,bot_guid):
    intent_data = {}
    intents = data['ozz_data']['intents']

    for intent_obj in intents:
        patterns = []
        intent_name = intent_obj["name"]
        intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
        
        for utt_copy in intent_obj["utterances"]:
            parameters,regex = get_regex(utt_copy)
            new_obj = {}
            new_obj['string'] = utt_copy
            new_obj['regex']  = regex
            new_obj['entities'] = parameters
            new_obj['len'] = len(utt_copy)
            patterns.append(json.dumps(new_obj))
            for word in stopWords:
                utt_copy = utt_copy.replace(word," ")
            
            utt_words = utt_copy.split(" ")

            words_json = json.loads(bot.words) 
            if type(words_json) == str:
                words_json = {}
            for word in utt_words:
                if word in words_json:
                    if intent_name in words_json[word]:
                        words_json[word][intent_name] += 1
                    else:
                        words_json[word][intent_name] = 1
                else:
                    words_json[word] = {intent_name:1}
        
        if intent:
            intent.utterances = intent_obj["utterances"]
            intent.responses = intent_obj["responses"]
            intent.patterns = patterns
            flag_modified(intent, "utterances")
            db.session.commit()
        else:
            name = intent_name
            utterances = intent_obj["utterances"]
            responses = intent_obj["responses"]
            has_entities = False
            intent = Intent(
                name = name,
                bot_guid=bot_guid,
                utterances=utterances,
                has_entities=has_entities,
                responses = responses,
                patterns=patterns
            )
            db.session.add(intent)
            db.session.commit()

    entities = data['ozz_data']['entities']

    for entity_obj in entities:
        name = entity_obj['name']
        
        new_examples = {}
        for value in entity_obj['values']:
            new_examples[value["value"]] = value["synonyms"]

        entity = Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=name).first()
        
        if entity:
            entity.examples = json.dumps(new_examples)
        else:
            entity = Entity(
                name = name.lower(),
                bot_guid=bot_guid,
                examples=json.dumps(new_examples)
            )
            db.session.add(entity)
        db.session.commit()


def get_regex(string):
    pattern = string #str(input('Enter the pattern: '))
    pattern_words =  pattern.split(" ")
    
    parameters = []
    regex = []
    
    first = False
    for i in range(len(pattern_words)):
        word = pattern_words[i]
        if len(word) > 0 and word[0] == '@':
            if not first:
                first= len(' '.join(pattern_words[0:i]) + ' ')
            else:
                first=-1
            if i == len(pattern_words) - 1:
                post = None
            else:
                post = pattern_words[i+1]
            regex.append("[\d\D\s]+")
            parameters.append({"entity":word,"first":first,"prior":pattern_words[i-1],"post":post})
        else:
            regex.append(word)

    regex = ' '.join(regex)
    return parameters,regex
