import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.types import Boolean
        
class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), ForeignKey("bots.bot_guid",ondelete="CASCADE"))
    message = db.Column(db.String())
    intent = db.Column(db.String())
    entities = db.Column(JSON)
    confident = db.Column(Boolean, unique=False, default=False)
    response_time = db.Column(db.String(),unique=False, default="0")
    created = db.Column(db.DateTime(timezone=False))

    def __init__(self,bot_guid, message="", intent=None, entities={}, confident=False, response_time="0"):
        self.bot_guid = bot_guid
        self.message = message
        self.intent = intent
        self.entities = entities
        self.response_time = response_time
        self.confident = confident
        self.created = datetime.datetime.now()

    def __repr__(self):
        return '<name {}>'.format(self.message)
