import csv
import psycopg2

from project import db
from project.api.models import User

tsv_file = 'users.tsv'

def add_user(name, email, hashed):
    user = User(
                name=name, 
                email=email, 
                password=hashed
            )
    db.session.add(user)
    db.session.commit()
    return user

def add_all_users():
    with open(tsv_file,'r') as csvfile:
        users = []
        reader = csv.reader(csvfile, delimiter='\t',quotechar='|')
        for row in reader:
            print(row)

add_all_users()