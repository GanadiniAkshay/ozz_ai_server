import datetime

from project import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        self.created_at = datetime.datetime.utcnow()