import datetime
import spacy
import time

from flask import Blueprint, jsonify, request, render_template

from project.api.models.knowledge import Knowledge
from project.api.models.intents import Intent
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d
from sqlalchemy import exc

from project.shared.checkAuth import checkAuth
from project.config import DevelopmentConfig
from project.keys import super_secret

knowledge_blueprint = Blueprint('knowledge', __name__, template_folder='./templates')

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
    