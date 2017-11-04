import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.logs import Logs 
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project import db,redis_db
from project.keys import super_secret

session_blueprint = Blueprint('session', __name__, template_folder='./templates')

@session_blueprint.route('/api/session', methods=['POST'])
def session():
    post_data = request.get_json()
    print(post_data)
    return jsonify({"success":"true"})
                   

