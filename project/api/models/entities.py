import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
        
class Entity(db.Model):
    __tablename__ = 'entities'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), ForeignKey("bots.bot_guid"))
    name = db.Column(db.String())
    examples = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=False))

    def __init__(self,bot_guid, name, examples):
        self.name = name
        self.bot_guid = bot_guid
        self.examples = examples
        self.created = datetime.datetime.now()

    def __repr__(self):
        return '<name {}>'.format(self.name)
