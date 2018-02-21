import bcrypt
import jwt

from flask import Blueprint, jsonify, request, render_template

from project.api.models.users import User
from project import db,app
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret


users_blueprint = Blueprint('users', __name__, template_folder='./templates')

@users_blueprint.route('/api/users', methods=['POST'])
def add_user():
    post_data = request.get_json()
    if not post_data:
        response_object = {
            'status': 'fail',
            'message': 'Invalid payload.'
        }
        app.logger.error('POST /api/users'+' invalid post payload')
        return jsonify(response_object), 400
    name = post_data.get('name')
    email = post_data.get('email')
    password = post_data.get('password')
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            password = password.encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

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
            app.logger.info('POST /api/users'+' user created successfully')
            return jsonify(response_object), 201
        else:
            app.logger.warning('POST /api/users'+' user exists with that account')
            return jsonify({"email":"An account already exists for that email"}),404
    except exc.IntegrityError as e:
        db.session.rollback()
        app.logger.error('POST /api/users'+' '+str(e))
        return jsonify({"success":False,"errors":str(e)}), 400


@users_blueprint.route('/api/auth',methods=['POST'])
def auth():
    post_data = request.get_json()
    if not post_data:
        response_object = {
            'status': 'fail',
            'message': 'Invalid payload.'
        }
        app.logger.error('POST /api/auth'+' invalid post payload')
        return jsonify(response_object), 400
    
    email = post_data.get('email')
    password = post_data.get('password')  

    user = User.query.filter_by(email=email).first()

    if user:
        password = password.encode('utf-8')
        hashed = user.password.encode('utf-8')
        if bcrypt.hashpw(password,hashed) == hashed:
            token = jwt.encode({'name':user.name,'email':user.email, 'id':user.id},super_secret,algorithm='HS256').decode('utf-8')
            app.logger.info('POST /api/auth'+' successfully logged in')
            return jsonify({"success":"true","token":token})
        else:
            app.logger.warning('POST /api/auth'+' incorrect password')
            return jsonify({"password":"Invalid Password"}),401
    else:
        app.logger.warning('POST /api/auth'+' account does not exist')
        return jsonify({"email":"No account exists for that email"}),404

@users_blueprint.route('/api/users/<user_id>', methods=['GET'])
def get_single_user(user_id):
    """Get single user details"""
    response_object = {
        'status': 'fail',
        'message': 'User does not exist'
    }
    try:
        user = User.query.filter_by(id=int(user_id)).first()
        if not user:
            app.logger.warning('GET /api/users/'+ user_id +' user does not exist')
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
            app.logger.info('GET /api/users/'+ user_id +' successfully returned user info')
            return jsonify(response_object), 200
    except ValueError:
        app.logger.error('POST /api/users/'+ user_id +' ' + str(e))
        return jsonify(response_object), 404



