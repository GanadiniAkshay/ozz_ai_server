from __future__ import absolute_import
from __future__ import print_function

from flask import Blueprint, request, jsonify
from project.helpers.parser import NLUParser
from subprocess import call

from rasa_nlu.converters import load_data
from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer

import mitie
import os
import json
import sys
import urllib
import tarfile
import shutil

nlu_blueprint = Blueprint('nlu', __name__, template_folder='./templates')

config = './project/config.json'

with open(config,"r") as jsonFile:
    data = json.load(jsonFile)
    if "active_model" in data.keys():
        model = data["active_model"]

@nlu_blueprint.route('/parse', methods=['GET'])
def parse():
    message = request.args.get('q')
    if type(message) != str:
        message = message.decode('utf-8')
    with open(config,"r") as jsonFile:
        data = json.load(jsonFile)
        model = data["active_model"]
    nlu = NLUParser(model, config)
    intent, entities = nlu.parse('hello')
    return jsonify({"intent":intent,"entities":entities})


@nlu_blueprint.route('/train', methods=['GET'])
def train():
    try:
        path = os.path.join(os.getcwd(), 'data')
        training_data = load_data(os.path.join(path, 'demo-rasa.json'))
        trainer = Trainer(RasaNLUConfig(os.path.join(os.getcwd(),'project', 'config.json')))
        trainer.train(training_data)
        model_directory = trainer.persist('models')

        with open(os.path.join(os.getcwd(),'project', 'config.json'),"r") as jsonFile:
            data = json.load(jsonFile)

        data["active_model"] = str(model_directory)
        with open(os.path.join(os.getcwd(),'project', 'config.json'),"w") as jsonFile:
            json.dump(data, jsonFile)
    except:
        return jsonify({"success":False})
    
    return jsonify({"success":True})

@nlu_blueprint.route('/retrain',methods=['GET'])
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