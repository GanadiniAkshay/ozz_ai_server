import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON
        
class Logs(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String())
    bot_guid = db.Column(db.String(),ForeignKey("bots.bot_guid",ondelete="CASCADE"))
    url = db.Column(db.String())
    pat = db.Column(db.String())
    pid = db.Column(db.String())
    user_data = db.Column(JSON)
    is_human = db.Column(db.Integer)
    source = db.Column(db.String())
    created = db.Column(db.DateTime(timezone=True))

    def __init__(self,message="",bot_guid="",pat="",pid="",url="",user_data={},is_human=1,source="web"):
        self.message = message
        self.bot_guid = bot_guid
        self.pat = pat
        self.pid = pid
        self.url = url
        self.user_data = user_data
        self.is_human = is_human
        self.source = source
        self.created = datetime.datetime.now()

    def __repr__(self):
        return '<message {}>'.format(self.message)
