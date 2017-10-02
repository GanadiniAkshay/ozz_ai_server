import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.logs import Logs 
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project import db
from project.keys import super_secret

logs_blueprint = Blueprint('logs', __name__, template_folder='./templates')


@logs_blueprint.route('/api/logs', methods=['POST'])
def logs():
    post_data = request.get_json()
    message = post_data['message']
    bot_guid = post_data['bot_guid']
    pat = post_data['pat']
    pid = post_data['pid']
    url = post_data['url']

    log = Logs(message=message,bot_guid=bot_guid,pat=pat,pid=pid,url=url)
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({"success":"false"})
    return jsonify({"success":"true"})
                   

