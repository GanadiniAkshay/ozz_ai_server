import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from project.config import DevelopmentConfig

# instantiate the db
db = SQLAlchemy()
 # instantiate flask migrate
migrate = Migrate()


def create_app():

    # instantiate the app
    app = Flask(__name__)

    # enable CORS
    CORS(app)

    # set config
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    # set up extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    from project.api.users import users_blueprint
    from project.api.bots  import bots_blueprint
    from project.api.nlu   import nlu_blueprint
    
    app.register_blueprint(users_blueprint)
    app.register_blueprint(bots_blueprint)
    app.register_blueprint(nlu_blueprint)

    # register default route
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def index(path):
        return render_template('index.html',cdn=DevelopmentConfig.CDN_URL)

    return app