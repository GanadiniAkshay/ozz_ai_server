import datetime
import json

from flask import Blueprint, jsonify, request, render_template

from project.api.models.entities import Entity 
from project.api.models.bots import Bot
from project import db, app
from sqlalchemy import exc
from sqlalchemy.orm.attributes import flag_modified

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

entities_blueprint = Blueprint('entities', __name__, template_folder='./templates')

@entities_blueprint.route('/api/entities/<bot_guid>/<entity_name>', methods=['GET','POST','PUT','DELETE'])
def entity(bot_guid,entity_name):
    code,user_id = checkAuth(request)
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'GET':
                    entity= Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                    if entity:
                        if type(entity.examples) == str:
                            entity.examples = json.loads(entity.examples)
                        app.logger.info('GET /api/entities/'+bot_guid+'/'+entity_name+' successfully returned entity examples')
                        return jsonify({"examples":entity.examples})
                elif request.method == 'POST':
                    post_data = request.get_json()
                    if not post_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        app.logger.warning('POST /api/entities/'+bot_guid+'/'+entity_name+' invalid post object')
                        return jsonify(response_object), 400
                    else:
                        entity= Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                        if entity:
                            if type(entity.examples) == str:
                                entity.examples = json.loads(entity.examples)
                            new_example = post_data['new_example']
                            entity.examples[new_example] = []
                            flag_modified(entity, "examples")
                            try:
                                db.session.commit()
                            except Exception as e:
                                app.logger.error('POST /api/entities/'+bot_guid+'/'+entity_name+' '+str(e))
                                return jsonify({"success":False,"error":str(e)})
                            app.logger.info('POST /api/entities/'+bot_guid+'/'+entity_name+' successfully added entity')
                            return jsonify({"success":True})
                elif request.method == 'DELETE':
                    entity= Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                    if entity:
                        old_example = request.args['old_example']
                        entity.examples.pop(old_example,0)
                        flag_modified(entity, "examples")
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('DELETE /api/entities/'+bot_guid+'/'+entity_name+' '+str(e))
                            return jsonify({"success":False,"error":str(e)})
                        app.logger.info('POST /api/entities/'+bot_guid+'/'+entity_name+' successfully deleted entity')
                        return jsonify({"success":True})
    elif code == 400:
        app.logger.warning('/api/entities/'+bot_guid+'/'+entity_name+' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/entities/'+bot_guid+'/'+entity_name+' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401

@entities_blueprint.route('/api/entities/<bot_guid>', methods=['GET','POST','PUT','DELETE'])
def entities(bot_guid):
    code,user_id = checkAuth(request)
    if code == 200:
        bot = Bot.query.filter_by(bot_guid=bot_guid).first()
        if bot:
            if bot.user_id == user_id:
                if request.method == 'GET':
                    entities = Entity.query.filter_by(bot_guid=bot_guid)
                    entities_obj = []
                    for entity in entities:
                        if type(entity.examples) == str:
                            entity.examples = json.loads(entity.examples)
                        entity_obj = {}
                        entity_obj['name'] = entity.name
                        entity_obj['examples'] = entity.examples
                        entity_obj['num_examples'] = len(entity.examples)
                        entities_obj.append(entity_obj)
                    app.logger.warning('GET /api/entities/'+bot_guid+ ' successfully returned entities')
                    return jsonify({"entities":entities_obj})
                elif request.method == 'POST':
                    post_data = request.get_json()
                    if not post_data:
                        response_object = {
                            'status': 'fail',
                            'message': 'Invalid payload.'
                        }
                        app.logger.warning('POST /api/entities/'+bot_guid+ ' invalid post object')
                        return jsonify(response_object), 400
                    else:
                        name = post_data.get('name')
                        examples = post_data.get('examples')
                        
                        entity = Entity.query.filter_by(name=name).first()
                        if entity:
                            entity.examples = examples
                        else:
                            entity = Entity(
                                name = name.lower(),
                                bot_guid=bot_guid,
                                examples=examples
                            )
                            db.session.add(entity)
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('POST /api/entities/'+bot_guid+ ' ' + str(e))
                            return jsonify({"success":False,"error":str(e)})
                        app.logger.info('POST /api/entities/'+bot_guid+ ' successfully returned entities')
                        return jsonify({"success":True})
                elif request.method == 'DELETE':
                    entity_name = request.args['entity']
                    entity = Entity.query.filter_by(bot_guid=bot_guid).filter_by(name=entity_name).first()
                    if entity:
                        db.session.delete(entity)
                        try:
                            db.session.commit()
                        except Exception as e:
                            app.logger.error('DELETE /api/entities/'+bot_guid+ ' ' + str(e))
                            return jsonify({"success":False,"error":str(e)})
                        app.logger.info('DELETE /api/entities/'+bot_guid+ ' successfully deleted entity')
                        return jsonify({"success":True})
                    else:
                        app.logger.warning('DELETE /api/entities/'+bot_guid+ ' bot does not exist')
                        return jsonify({"success":False,"error":"Entity doesn't exsit"}),404
    elif code == 400:
        app.logger.warning('/api/entities/'+bot_guid+ ' invalid authorization token')
        return jsonify({"error":"Invalid Authorization Token"}),400
    elif code == 401:
        app.logger.warning('/api/entities/'+bot_guid+ ' no authorization token sent')
        return jsonify({"error":"No Authorization Token Sent"}),401


