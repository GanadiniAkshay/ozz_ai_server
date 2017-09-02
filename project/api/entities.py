import datetime

from flask import Blueprint, jsonify, request, render_template

from project.api.models.entities import Entity 
from project.api.models.bots import Bot
from project import db
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

entities_blueprint = Blueprint('entities', __name__, template_folder='./templates')

@entities_blueprint.route('/entities/<bot_guid>', methods=['GET','POST'])
def entities(bot_guid):
    # code,user_id = checkAuth(request)
    code = 200
    user_id = 16
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'GET':
                    entities = Entity.query.filter_by(bot_guid=bot_guid)
                    entities_obj = []
                    for entity in entities:
                        entity_obj = {}
                        entity_obj['name'] = entity.name
                        entity_obj['examples'] = entity.examples
                        entities_obj.append(entity_obj)
                    return jsonify({"entities":entities_obj})
                elif request.method == 'POST':
                    post_data = request.get_json()
                    if not post_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        return jsonify(response_object), 400
                    else:
                        name = post_data.get('name')
                        examples = post_data.get('examples')
                        
                        entity = Entity.query.filter_by(name=name).first()
                        if entity:
                            entity.examples = examples
                        else:
                            entity = Entity(
                                name = name,
                                bot_guid=bot_guid,
                                examples=examples
                            )
                            db.session.add(entity)
                        try:
                            db.session.commit()
                        except Exception as e:
                            return jsonify({"success":False})
                        return jsonify({"success":"true"})
    elif code == 400:
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        return jsonify({"error":"No Authorization Token Sent"}),401


