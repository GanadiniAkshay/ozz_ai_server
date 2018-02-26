import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

        
class Training(db.Model):
    __tablename__ = 'training'

    id = db.Column(db.Integer, primary_key=True)
    bot_guid = db.Column(db.String(), ForeignKey("bots.bot_guid", ondelete="CASCADE"))
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE"))
    trained_at = db.Column(db.DateTime(timezone=False))
    train_time = db.Column(db.Integer)
    

    def __init__(self, bot_guid, user_id, trained_at, train_time):
        self.bot_guid = bot_guid
        self.user_id = user_id
        self.trained_at = trained_at
        self.train_time = train_time
        

    def __repr__(self):
        return '<bot_guid {}>'.format(self.bot_guid)
