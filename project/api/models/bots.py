import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

        
class Bot(db.Model):
    __tablename__ = 'bots'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), unique=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = db.Column(db.String())
    platforms = db.Column(JSON)
    active_model = db.Column(db.String())
    team = db.Column(JSON)
    words = db.Column(db.String())
    created = db.Column(db.DateTime(timezone=False))
    used = db.Column(db.DateTime(timezone=False))

    def __init__(self, user_id, name, words={},platforms={}):
        self.bot_guid = str(uuid.uuid1())
        self.user_id = user_id
        self.name = name
        self.platforms = platforms
        self.created = datetime.datetime.now()
        self.used = datetime.datetime.now()
        self.active_model = ""
        self.words = words
        self.team = {"admins":[{"user_id":user_id}],"developers":[]}

    def __repr__(self):
        return '<name {}>'.format(self.name)
