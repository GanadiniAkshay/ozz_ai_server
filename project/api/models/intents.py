import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.types import ARRAY,Boolean
        
class Intent(db.Model):
    __tablename__ = 'intents'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), ForeignKey("bots.bot_guid"))
    name = db.Column(db.String())
    utterances = db.Column(ARRAY(db.String()))
    has_entities = db.Column(Boolean, unique=False, default=False)
    responses = db.Column(ARRAY(db.String()))
    calls = db.Column(db.Integer,default=0)
    created = db.Column(db.DateTime(timezone=False))

    def __init__(self,bot_guid, name, has_entities, utterances=[],responses=[]):
        self.name = name
        self.bot_guid = bot_guid
        self.utterances = utterances
        self.has_entities = has_entities
        self.responses = responses
        self.calls = 0
        self.created = datetime.datetime.now()

    def __repr__(self):
        return '<name {}>'.format(self.name)
