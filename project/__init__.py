import os
import time
import spacy
import redis
import logging
import requests
import json
import rq_dashboard

from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from rq import Queue, Connection, Worker

from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer
from rasa_nlu.components import ComponentBuilder

from werkzeug.contrib.cache import SimpleCache
from cachetools import LRUCache
from duckling import Duckling

from project.config import DevelopmentConfig


# instantiate the db
db = SQLAlchemy()
# instantiate the redis db
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_db = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
# instantiate flask migrate
migrate = Migrate()
# instantiate a cache
# cache = SimpleCache()
cache = LRUCache(maxsize=100)
#set up spacy nlp
nlp = spacy.load('en')
# set up duckling
d = Duckling()
d.load()
# set up redis queue
q = Queue(connection=redis_db)


interpreters = {}

#load the stop words
stopWords = ['d', 'down', 'they', 'during', 'no', 'yourselves', 'most', 'needn', 'which', 'yours', 'you', 've', 'once', 'own', 'does', 'weren', 'myself', 'will', 'mustn', 'm', 'couldn', 'from', 'their', 'ain', 'off', 'isn', 'wasn', 'doesn', 'll', 'about', 'where', 'only', 'an', 'nor', 'shouldn', 'by', 'themselves', 'should', 'him', 'ours', 'to', 'hasn', 'for', 'why', 'until', 'y', 'when', 'her', 'aren', 'didn', 'that', 'there', 'at', 'same', 'herself', 'below', 'it', 'under', 'how', 'more', 'whom', 'not', 'both', 'don', 'against', 'further', 'hers', 'just', 'each', 'being', 'your', 'now', 'then', 'if', 'have', 'is', 'be', 'but', 'shan', 'the', 'before', 'over', 's', 'his', 'mightn', 'as', 'can', 'yourself', 'up', 'between', 'i', 'on', 'few', 'having', 'and', 'himself', 'this', 'again', 'he', 'am', 'theirs', 'who', 'these', 'has', 'or', 'with', 't', 'here', 'such', 'through', 'won', 'above', 'did', 'she', 'had', 'our', 'my', 'all', 'were', 'its', 'hadn', 'other', 'doing', 'are', 'them', 'wouldn', 'while', 'because', 'into', 'itself', 'too', 'haven', 're', 'so', 'out', 'been', 'very', 'any', 'those', 'o', 'in', 'do', 'after', 'a', 'ourselves', 'we', 'ma', 'me', 'of', 'some', 'what', 'was', 'than']


#set up the trainer
print("Setting up trainer")
config = os.path.join(os.getcwd(),'project', 'config.json')
builder = ComponentBuilder(use_cache=True) 
trainer = Trainer(RasaNLUConfig(config),builder)

# instantiate the app
app = Flask(__name__)

# enable CORS
CORS(app)


def count_words_at_url(url):
    resp = requests.get(url)
    print(len(resp.text.split()))
    return len(resp.text.split())


def create_app():

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    # set up rq dashboard
    app.config.from_object(rq_dashboard.default_settings)
    app.config.update(
        REDIS_HOST = REDIS_HOST,
        REDIS_PORT = REDIS_PORT,
        REDIS_PASSWORD = None,
        REDIS_DB = 0,
        RQ_POLL_INTERVAL = 2500,  #: Web interface poll period for updates in ms
        DEBUG = False,
        WEB_BACKGROUND = "black",
        DELETE_JOBS = False)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


    # set up extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    from project.api.users import users_blueprint
    from project.api.bots  import bots_blueprint
    from project.api.nlu   import nlu_blueprint
    from project.api.intents import intents_blueprint
    from project.api.entities import entities_blueprint
    from project.api.utterances import utterances_blueprint
    from project.api.responses import responses_blueprint
    from project.api.synonyms import syn_blueprint
    from project.api.scheduler import schedule_blueprint
    from project.api.patterns import patterns_blueprint
    from project.api.logs import logs_blueprint
    from project.api.analytics import analytics_blueprint
    from project.api.knowledge import knowledge_blueprint
    from project.api.session import session_blueprint
    
    app.register_blueprint(users_blueprint)
    app.register_blueprint(bots_blueprint)
    app.register_blueprint(nlu_blueprint)
    app.register_blueprint(intents_blueprint)
    app.register_blueprint(entities_blueprint)
    app.register_blueprint(utterances_blueprint)
    app.register_blueprint(responses_blueprint)
    app.register_blueprint(syn_blueprint)
    app.register_blueprint(schedule_blueprint)
    app.register_blueprint(patterns_blueprint)
    app.register_blueprint(logs_blueprint)
    app.register_blueprint(analytics_blueprint)
    app.register_blueprint(knowledge_blueprint)
    app.register_blueprint(session_blueprint)

    if not os.path.exists('/var/lib/ozz/logs'):
        os.mkdir('/var/lib/ozz/logs')

    # initialize the log handler
    logHandler = RotatingFileHandler('/var/lib/ozz/logs/info.log', maxBytes=10240, backupCount=10)

    logHandler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    
    # set the log handler level
    logHandler.setLevel(logging.INFO)

    # set the app logger level
    app.logger.setLevel(logging.INFO)

    app.logger.addHandler(logHandler)
    app.logger.info('Server started')

    @app.route('/task/<job_name>')
    def start_task(job_name):
        event = {}
        event["url"] = "http://nvie.com"
        redis_db.delete(job_name) #remove old keys
        redis_db.hmset(job_name, event)
        redis_db.expire(job_name, 19500)
        result = q.enqueue(count_words_at_url, 'http://nvie.com')
        return "task started"

    @app.route('/status/<job_id>')
    def job_status(job_id):
        job = q.fetch_job(job_id)
        if job is None:
            response = {'status': 'unknown'}
        else:
            status = job.get_status()
            if status == 'finished':
                if job.result:
                    result = json.loads(job.result)
                else:
                    print(job)
                    result = None
            else:
                result = None
            response = {
                'status': status,
                'result': result
            }
            if job.is_failed:
                response['message'] = job.exc_info.strip().split('\n')[-1]
        return jsonify(response)

    @app.route("/log")
    def logTest():
        app.logger.warning('testing warning log')
        app.logger.error('testing error log')
        app.logger.info('testing info log')
        return "Code Handbook !! Log testing."

    @app.route('/demo/steve')
    def steve():
        return render_template('steve.html')

    # register default route
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def index(path):
        return render_template('index.html',cdn=DevelopmentConfig.CDN_URL)

    time1 = time.time()
    print("creating interpreters")
    create_interpreters(db)
    time2 = time.time()
    print(time2-time1)

    return app

def create_interpreters(db):
    from project.helpers.parser import NLUParser
    if os.path.exists('/var/lib/ozz/models'):
        directories =os.listdir('/var/lib/ozz/models')
        config = './project/config.json'
        for directory in directories:
            active_model = '/var/lib/ozz/models/' + directory
            print(active_model)
            interpreters[active_model] = NLUParser(active_model,config, builder)
