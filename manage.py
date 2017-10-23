import unittest
import csv

from flask_script import Manager

from project import create_app, db
from project.api.models.users import User
from project.api.models.bots import Bot
from project.api.models.intents import Intent
from project.api.models.entities import Entity
from project.api.models.analytics import Analytics
from project.api.models.schedule import Schedule
from project.api.models.logs import Logs
from project.api.models.knowledge import Knowledge

app = create_app()
manager = Manager(app)
user_tsv_file = 'users.tsv'
bots_tsv_file = 'bots.tsv'

manager.add_command('db', MigrateCommand)

def add_user(name, email, hashed):
    user = User(
                name=name, 
                email=email, 
                password=hashed
            )
    db.session.add(user)
    db.session.commit()
    return user

@manager.command
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover('project/tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1

@manager.command
def recreate_db():
    """Recreates a database."""
    db.drop_all()
    db.create_all()
    db.session.commit()

@manager.command
def add_all_users():
    with open(user_tsv_file,'r') as csvfile:
        users = []
        reader = csv.reader(csvfile, delimiter='\t',quotechar='|')
        for row in reader:
            name = row[1]
            email = row[2]
            hashed = row[3]

            print("Creating account for " + name)
            add_user(name,email,hashed)

@manager.command
def connect_bots():
    users = User.query.all()
    new_mapping = {}
    for user in users:
        new_mapping[user.email] = user.id
    old_mapping = {}
    old_mapping_inverse = {}
    with open(user_tsv_file,'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t',quotechar='|')
        for row in reader:
            old_mapping[row[2]] = row[0]
            old_mapping_inverse[row[0]] = row[2]
    with open(bots_tsv_file,'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t',quotechar='|')
        for row in reader:
            old_id = row[2]
            if old_id not in old_mapping_inverse.keys():
                continue
            else:
                old_email = old_mapping_inverse[old_id]
                bot_name = row[3]

                new_id = new_mapping[old_email]
                print("Connecting " +bot_name + ' created by ' + old_email + " with old_id as "+ str(old_id) + " and new_id as " + str(new_id))
                bot = Bot(
                    user_id=new_id,
                    name=bot_name
                )
                db.session.add(bot)
                db.session.commit()

if __name__ == '__main__':
    manager.run()