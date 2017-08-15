import bcrypt
import jwt

from flask import Blueprint, jsonify, request, render_template

from project.api.models.users import User
from project import db
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret


users_blueprint = Blueprint('users', __name__, template_folder='./templates')

@users_blueprint.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify({
        'status':'success',
        'message':'pong!'
    })

@users_blueprint.route('/users', methods=['POST'])
def add_user():
    post_data = request.get_json()
    if not post_data:
        response_object = {
            'status': 'fail',
            'message': 'Invalid payload.'
        }
        return jsonify(response_object), 400
    name = post_data.get('name')
    email = post_data.get('email')
    password = post_data.get('password')
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            password = password.encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())

            user = User(
                name=name, 
                email=email, 
                password=hashed
            )

            db.session.add(user)
            db.session.commit()
            
            token = jwt.encode({'name':user.name,'email':user.email, 'id':user.id},super_secret,algorithm='HS256').decode('utf-8')
            print(token)
            response_object = {
                'status': 'success',
                'token': token
            }
            return jsonify(response_object), 201
        else:
            response_object = {
                'status': 'fail',
                'message': 'Sorry. That email already exists.'
            }
            return jsonify(response_object), 400
    except exc.IntegrityError as e:
        db.session.rollback()
        response_object = {
            'status': 'fail',
            'message': 'Invalid payload.'
        }
        return jsonify(response_object), 400

@users_blueprint.route('/users/<user_id>', methods=['GET'])
def get_single_user(user_id):
    """Get single user details"""
    response_object = {
        'status': 'fail',
        'message': 'User does not exist'
    }
    try:
        user = User.query.filter_by(id=int(user_id)).first()
        if not user:
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'success',
                'data': {
                  'username': user.username,
                  'email': user.email,
                  'created_at': user.created_at
                }
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404



