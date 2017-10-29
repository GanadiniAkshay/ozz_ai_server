import datetime
import spacy
import time
import re
import json

from flask import Blueprint, jsonify, request, render_template

from project.api.models.intents import Intent 
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

patterns_blueprint = Blueprint('patterns', __name__, template_folder='./templates')


@patterns_blueprint.route('/api/intents/<bot_guid>/<intent_name>/patterns', methods=['GET','POST','PUT','DELETE'])
def pattern(bot_guid,intent_name):
    # code,user_id = checkAuth(request)
    code = 200
    user_id = 16
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
                        patterns_obj = []
                        patterns = intent.patterns
                        for pattern in patterns:
                            pattern = json.loads(pattern)
                            pat_obj = {}
                            pat_obj["string"] = pattern['string']
                            pat_obj["regex"]  = pattern['regex']
                            pat_obj["len"] = pattern['len']
                            pat_obj["entities"] = pattern['entities']
                            patterns_obj.append(pat_obj)
                        patterns_obj = sorted(patterns_obj, key=lambda k: k['len'],reverse=True)
                        return jsonify({"patterns":patterns_obj})
                    if request.method == 'POST':
                        post_data = request.get_json()
                        new_pattern = post_data['value']

                        for pattern in intent.patterns:
                            pattern = json.loads(pattern)
                            if new_pattern == pattern["string"]:
                                return jsonify({"success":False})
                        parameters,regex = get_regex(new_pattern)
                        new_obj = {}
                        new_obj['string'] = new_pattern
                        new_obj['regex']  = regex
                        new_obj['entities'] = parameters
                        new_obj['len'] = len(new_pattern)
                        pats = [json.dumps(new_obj)] + intent.patterns
                        intent.patterns = [p for p in pats]
                        db.session.commit()
                        return jsonify({"pattern":new_obj})
                    elif request.method == 'PUT':
                        put_data = request.get_json()
                        old_pattern = put_data['old_pattern']
                        new_pattern = put_data['new_pattern']
                        parameters,regex = get_regex(new_pattern)

                        new_patterns = []

                        for pattern in intent.patterns:
                            pattern = json.loads(pattern)
                            if pattern["string"] == old_pattern:
                                pattern["string"] = new_pattern
                                pattern["regex"]  = regex
                                pattern["entities"] = parameters
                                pattern["len"] = len(new_pattern)
                            new_patterns.append(json.dumps(pattern))
                        intent.patterns = new_patterns
                        db.session.commit()
                        return jsonify({"success":True})
                    elif request.method == 'DELETE':
                        old_pattern = request.args['pattern']
                        new_patterns = []
                        for pattern in intent.patterns:
                            pattern = json.loads(pattern)
                            if (pattern['string'] != old_pattern):
                                new_patterns.append(json.dumps(pattern))
                        intent.patterns = new_patterns
                        db.session.commit()
                        return jsonify({"success":True})
                else:
                   return jsonify({"error":"Intent Doesn't exist"}),404 
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401


def get_regex(string):
    pattern = string #str(input('Enter the pattern: '))
    pattern_words =  pattern.split(" ")
    
    parameters = []
    regex = []
    
    first = False
    for i in range(len(pattern_words)):
        word = pattern_words[i]
        if word[0] == '@':
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

