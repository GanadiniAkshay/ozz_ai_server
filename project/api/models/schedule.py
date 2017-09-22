import datetime
import uuid

from project import db
from sqlalchemy import ForeignKey
        
class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String())
    created = db.Column(db.DateTime(timezone=True))

    def __init__(self,message=""):
        self.message = message
        self.created = datetime.datetime.now()

    def __repr__(self):
        return '<name {}>'.format(self.message)
