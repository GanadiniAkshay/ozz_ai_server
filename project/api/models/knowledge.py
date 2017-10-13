import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.types import Boolean
        
class Knowledge(db.Model):
    __tablename__ = 'knowledge'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), ForeignKey("bots.bot_guid",ondelete="CASCADE"))
    kid = db.Column(db.String())

    def __init__(self,bot_guid, kid):
        self.bot_guid = bot_guid
        self.kid = kid

    def __repr__(self):
        return '<name {}>'.format(self.kid)
