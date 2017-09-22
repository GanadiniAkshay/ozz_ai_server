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
from project import db, cache, interpreters, trainer, nlp, d
from sqlalchemy import exc

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

nlu_blueprint = Blueprint('nlu', __name__, template_folder='./templates')


@nlu_blueprint.route('/api/parse/<bot_guid>', methods=['GET'])
def parse(bot_guid):
    global interpreters
    nlus = interpreters
    config = './project/config.json'
    message = request.args.get('q')
    if type(message) != str:
        message = message.decode('utf-8')
    
    
    bot = Bot.query.filter_by(bot_guid=bot_guid).first()
    if bot:
        model = bot.active_model
        if model:
            nlu = nlus[model]
        else:
            return jsonify({"error":"Please train the bot before testing"})
    else:
        return jsonify({"error":"Bot doesn't exist"}),404
    message = message.lower()
    intent, entities = nlu.parse(message)
    response = ""
    if intent != 'None':
        intent_obj = Intent.query.filter_by(name=intent).first()
        if intent_obj:
            intent_obj.calls += 1
            if (len(intent_obj.responses) > 0):
                response = random.choice(intent_obj.responses)
            db.session.commit()
            
    else:
        eliza = Eliza()
        response = eliza.analyze(message)
    row = Analytics(
                message = message,
                bot_guid=bot_guid,
                intent=intent,
                confident=True,
                entities= entities
            )
    db.session.add(row)
    db.session.commit()
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
                                        "entity_synonyms": []
                                    }
                            }
                intents = Intent.query.filter_by(bot_guid=bot_guid)
                entities = Entity.query.filter_by(bot_guid=bot_guid)
                for entity in entities:
                    for example_key in entity.examples:
                        rasa_data['rasa_nlu_data']['entity_synonyms'].append({"value":example_key,"synonyms":entity.examples[example_key]})
                for intent in intents:
                    if intent.has_entities == False:
                        for utterance in intent.utterances:
                            common_example = {}
                            common_example['text'] = utterance.lower()
                            common_example['intent'] = intent.name.lower()
                            common_example['entities'] = []
                            rasa_data['rasa_nlu_data']['common_examples'].append(common_example)
                    else:
                        for utterance in intent.utterances:
                            common_example = {}
                            common_example['text'] = utterance.lower()
                            common_example['intent'] = intent.name.lower()
                            common_example['entities'] = []
                            new_examples = []
                            new_values = []
                            for entity in entities:
                                for example_key in entity.examples:
                                    utterance = utterance.lower()
                                    ent_examples = entity.examples[example_key]
                                    if example_key.lower() not in ent_examples:
                                        ent_examples.append(example_key.lower())
                                    remaining_examples = ent_examples
                                    for example in ent_examples:
                                        example = example.lower()
                                        if example in utterance and example in utterance.split(' '):
                                            start = utterance.find(example)
                                            end = start + len(example)
                                            value = example_key
                                            ent_name = entity.name
                                            common_example['entities'].append({"start":start,"end":end,"value":value,"entity":ent_name})
                                            remaining_examples.remove(example)
                                            new_values = generate(utterance,example,remaining_examples,intent.name,entities)
                            rasa_data['rasa_nlu_data']['common_examples'].append(common_example)
                            rasa_data['rasa_nlu_data']['common_examples'] += new_values 
                try:
                    # print(rasa_data)
                    config = './project/config.json'
                    user_path = os.path.join(os.getcwd(),'data',str(user_id))
                    bot_path = os.path.join(user_path,bot_guid)
                    
                    training_data = load_train_data(rasa_data)
                    trainer.train(training_data)
                    model_directory = trainer.persist('models')
                    print(model_directory)

                    current_model = bot.active_model

                    if current_model and current_model != "":
                        global interpreters
                        interpreters.pop(current_model,0)
                        if os.path.exists(current_model):
                            shutil.rmtree(current_model)

                    bot.active_model = str(model_directory)
                    interpreters[model_directory] = NLUParser(model_directory,config)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    return jsonify({"success":False})
            else:
                return jsonify({"error":"Not Authorized"}),401
        else:
            return jsonify({"error":"Bot doesn't exist"}),404
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401
    
    return jsonify({"success":True})

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
    nlu.train()
    return jsonify({"success":True})


@nlu_blueprint.route('/api/upload/<bot_guid>', methods=['GET','POST'])
def upload(bot_guid):
    if request.method == 'POST':
        code,user_id = checkAuth(request)

        if code == 200:
            bot = Bot.query.filter_by(bot_guid=bot_guid).first()
            if bot:
                if bot.user_id == user_id:
                    # The folder for all the users data
                    user_path = os.path.join(os.getcwd(),'data',str(user_id))

                    # Create the folder if it doesn't exist
                    if not os.path.exists(user_path):
                        os.makedirs(user_path)

                    # The folder for the bot's data for a given user
                    bot_path = os.path.join(user_path,bot_guid)

                    # Create the folder if it doesn't exist
                    if not os.path.exists(bot_path):
                        os.makedirs(bot_path)

                    #Get the file information
                    file = request.files['file']
                    filename = secure_filename(file.filename)
                    
                    # Save the file
                    file.save(os.path.join(bot_path,'data.json'))
                    return jsonify({"filename":filename,"type":file.content_type})
                else:
                    return jsonify({"error":"Not Authorized"}),401
            else:
                return jsonify({"error":"Bot doesn't exist"}),404
        elif code == 400:
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            return jsonify({"error":"No Authorization Token Sent"}),401
    return render_template('file.html')


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