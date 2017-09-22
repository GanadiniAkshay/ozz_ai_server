import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.schedule import Schedule 
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

schedule_blueprint = Blueprint('schedule', __name__, template_folder='./templates')


@schedule_blueprint.route('/api/schedule', methods=['POST'])
def schedule():
    post_data = request.get_json()
    message = post_data['message']
    schedule = Schedule(message=message)
    try:
        db.session.add(schedule)
        db.session.commit()
    except:
        return jsonify({"success":"false"})
    return jsonify({"success":"true"})
                   

