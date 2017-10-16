import datetime
import spacy
import time
import json
import sys
import os
import operator
from bson import ObjectId

from flask import Blueprint, jsonify, request, render_template

from project.api.models.knowledge import Knowledge
from project.api.models.intents import Intent
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.shared.checkAuth import checkAuth
from project.config import DevelopmentConfig
from project.keys import super_secret

from random import randint
from cachetools import LRUCache


units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

def text2int(textnum, numwords={}):
    if not numwords:

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

knowledge_blueprint = Blueprint('knowledge', __name__, template_folder='./templates')

@knowledge_blueprint.route('/api/kquery', methods=['POST'])
def k_query():
    hey = ['hi','hey','hello','hola','heya','hello there','hola buddy','hola amigo']
    post_data = request.get_json()
    query = post_data['query']

    if query.lower() in hey:
        return jsonify({"answer":"Hi"})
    tags = ['javascript', 'jquery', 'html', 'css', 'angularjs', 'php', 'ajax', 'node.js', 'json', 'html5', 'arrays', 'asp.net', 'reactjs', 'regex', 'twitter-bootstrap', 'c#', 'forms', 'google-chrome', 'd3.js', 'dom', 'google-maps', 'java', 'canvas', 'ruby-on-rails', 'jquery-ui', 'android', 'angular', 'iframe', 'function', 'express', 'asp.net-mvc', 'cordova', 'mysql', 'css3', 'backbone.js', 'internet-explorer', 'javascript-events', 'google-maps-api-3', 'object', 'svg', 'typescript', 'mongodb', 'wordpress', 'firefox', 'meteor', 'validation', 'google-chrome-extension', 'ecmascript-6', 'image', 'knockout.js', 'mongoose', 'pug', 'passport.js', 'socket.io', 'session', 'ejs', 'mean-stack', 'rest', 'heroku', 'http', 'sequelize.js', 'cookies', 'handlebars.js', 'routes', 'sails.js', 'npm', 'multer', 'middleware', 'api', 'authentication', 'asynchronous', 'connect', 'routing', 'post', 'sockets', 'webpack', 'nginx', 'request', 'mocha', 'redis', 'cors', 'body-parser', 'express-session', 'promise', 'jwt', 'postgresql', 'websocket', 'amazon-web-services', 'gulp', 'gruntjs', 'azure', 'callback', 'electron', 'linux', 'windows', 'sass', 'gulp-watch', 'browserify', 'gulp-sass', 'browser-sync', 'bower', 'laravel', 'babeljs', 'laravel-elixir', 'gulp-concat', 'gulp-uglify', 'build', 'gulp-sourcemaps', 'git', 'less', 'visual-studio-2015', 'minify', 'gulp-less', 'livereload', 'gulp-inject', 'karma-runner', 'source-maps', 'visual-studio', 'ionic-framework', 'coffeescript', 'babel','closure','closures', 'nodemon', 'yeoman', 'laravel-5', 'web','homepage', 'gulp-browser-sync','404','regular expression','client']
    with open(os.getcwd() + '/data/paragraphs.json') as data_file:    
        data = json.load(data_file)
    
    with open(os.getcwd() + '/trained/types.json') as data_file:
        types = json.load(data_file)

    with open(os.getcwd() + '/trained/invindex_topics.json') as data_file:    
        inv_topic_index = json.load(data_file)
        
    with open(os.getcwd() + '/trained/invindex_new_para.json') as data_file:    
        inv_index = json.load(data_file)

    with open(os.getcwd() + '/trained/tfidf_new_para.json') as data_file:    
        results = json.load(data_file)

    #Calculate score for a query

    #remove ? symbol
    query = query.replace("?","")

    #turn to lowercase
    query = query.lower()

    definitions = ["what","define","defined","definition","understand","picture","understanding"]
    why_when = ['why','when','reasons','purpose','purposes','reason','benefits','benefit','prefer','preferrance']
    examples = ["how","step","sample","show","process","procedure","see","action","using","use"]
    relationships = ["relation","related","compare","comparison","better","worse","difference"]
    characteristics = ['features','characteristics','qualities','points']

    question_word = query.split(' ')[0]

    if question_word == 'how':
        question_type = ['examples', 'relationships']
    elif question_word == 'what':
        question_type = ['definitions','characteristics']
    elif question_word == 'why' or question_word == 'when':
        question_type = ['why_when']
        

    flag = False
    for tag in tags:
        check_tag = ' ' + tag +' '
        check_query = ' ' + query + ' '
        if check_tag  in check_query:
            if tag in inv_topic_index:
                results = inv_topic_index[tag]
                sorted_results = sorted(results, key=operator.itemgetter(1), reverse=True)
                top_likelies = sorted_results[:5]
                result_set = {"definitions":[],"why_when":[],"relationships":[],"characteristics":[],"examples":[]}
                answer_paras = []
                for likely in top_likelies:
                    que_types = [x[0] for x in types[likely[0]]]
                    for t in que_types:
                        if t in definitions:
                            result_set["definitions"].append(likely)
                        elif t in why_when:
                            result_set["why_when"].append(likely)
                        elif t in examples:
                            result_set["examples"].append(likely)
                        elif t in relationships:
                            result_set["relationships"].append(likely)
                        elif t in relationships:
                            result_set["characteristics"].append(likely)
                    
                    
                    for que_typ in question_type:
                        if len(result_set[que_typ]) > 0:
                            answer_paras += result_set[que_typ]
                
                if len(answer_paras)>0:
                    flag = True
                    sorted_answers = sorted(answer_paras, key=operator.itemgetter(1), reverse=True)
                    
                    answer = data[sorted_answers[0][0]]
        
                    if len(answer) < 300:
                        file = sorted_results[0][0].split('__')[0]
                        folder,file_name = file.split('-')

                        data_file = open(os.path.join(os.getcwd() + "/data/sections/",folder,file_name),mode='r',encoding="utf-8",errors="replace")

                        answer = ' '.join(data_file.readlines()[1:])
                else:
                    flag = False
                

    if not flag:
        #result set as a dictionary of key-value
        res_set = {}

        #get list of words to query over
        words = query.split(" ")
        words = list(set(words))

        #get top 10 documents for each word
        for word in words:
            if not word in inv_index:
                continue
            else:
                responses = inv_index[word][:10]

                for response in responses:
                    file,score = response

                    if file in res_set:
                        res_set[file] += score
                    else:
                        res_set[file] = score


        sorted_results = sorted(res_set.items(), key=operator.itemgetter(1), reverse=True)
        
        answer = data[sorted_results[0][0]]
        
        if len(answer) < 300:
            file = sorted_results[0][0].split('__')[0]
            folder,file_name = file.split('-')
            
            data_file = open(os.path.join(os.getcwd() + "/data/sections/",folder,file_name),mode='r',encoding="utf-8",errors="replace")
        
            answer = ' '.join(data_file.readlines()[1:])
    return jsonify({"answer":answer})

@knowledge_blueprint.route('/api/knowledge/<bot_guid>', methods=['POST'])
def analytics(bot_guid):
    bot = Bot.query.filter_by(bot_guid=bot_guid).first()
    if bot:
        post_data = request.get_json()
        print(post_data)
        kid = post_data['kid']

        if kid:
            knowledge = Knowledge(
                bot_guid=bot_guid,
                kid=kid
            )
            db.session.add(knowledge)
            db.session.commit()
        return jsonify({"success":True})
    else:
        return jsonify({"error":"Bot Doesn't exist"}),404


@knowledge_blueprint.route('/api/context', methods=['POST'])
def context():
    post_data = request.get_json()
    message = post_data['message'].title()

    form = {'_id': ObjectId('594f33b24b8ed20cc9c0f2d6'), 'result': '', 'form_type': '', 'intent': 'activate_findHackathons', 'type': 'smart', 'bot_name': 'AngelHack', 'guid': '26c5d2b7-3394-efd9-f326-8dbee7c14508', 'email': 'akshaykulkarni.2104@gmail.com', 'name': 'findHackathons', 'fields': [{'name': 'city', 'prompt': 'Which city are you looking for?', '_id': ObjectId('594f42c84b8ed20cc9c0f2d7'), 'answers': ['Hyderabad,Mumbai,Chennai,Bangalore,Delhi,Nyc,NYC,New York,Sacremento,Seattle']}, {'name': 'duration', 'prompt': 'How long should the hackathon be?', '_id': ObjectId('594f42db4b8ed20cc9c0f2d8'), 'answers': ['1 Day, 2 Days, 3 Days','1','2','3','4','5','6']}, {'name': 'theme', 'prompt': 'which theme are you interested in?', '_id': ObjectId('594f43004b8ed20cc9c0f2d9'), 'answers': ['AI, IOT, Artificial Intelligence,cloud,ux,bots,UX, bot, iot, vr, VR']}], 'phrases': ['Find a hackathon', 'find a hackathon in hyderabad', 'Find me a hackathon'], '__v': 4}
    flag = False
    intent = replyFromAI(message)
    print(intent)
    for field in form['fields']:
        predictions = field['answers'][0].split(',')
        print(predictions)
        print(message)
        for word in message.split(' '):
            if word in predictions:
                cache[field['name']] = word
                print("word in predictions")
    if form['intent'] == intent:
        flag = True
        for word in message:
            if word in units:
                message.replace(word,text2int(word))
        doc = nlp(message)
        for ent in doc.ents:
            if ent.label == 381:
                cache['city'] = ent.text
            elif ent.label == 387:
                cache['duration'] = ent.text
    else:
        for word in message:
            if word in units:
                message.replace(word,text2int(word))
        doc = nlp(message)
        for ent in doc.ents:
            if ent.label == 381:
                cache['city'] = ent.text
            elif ent.label == 387:
                cache['duration'] = ent.text

    for field in form['fields']:
        try:
            if cache[field['name']]:
                flag = True
        except:
            print(field['name'])
            print(flag)
            return field['prompt']
    string = "Found  " + str(randint(0, 5)) + " " + cache['theme'] +" hackathons in " + cache['city'] + " of duration " + cache['duration']
    return string


def replyFromAI(query):
    ai = apiai.ApiAI('b3aef2c281cc458695cb9db0bf075c6d')
    # Sending a text query to our bot with text sent by the user.
    request = ai.text_request()
    request.query = query
 
    # Receiving the response.
    response = json.loads(request.getresponse().read())
    responseStatus = response['status']['code']
    if (responseStatus == 200):
        # Sending the textual response of the bot.
        try:
            return (response['result']['metadata']['intentName'])
        except:
            return ('None')
 
    else:
        return ("Sorry, I couldn't understand that question")
    