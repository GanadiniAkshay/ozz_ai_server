from __future__ import absolute_import
from __future__ import print_function

import os
import json
import sys
import urllib
import tarfile
import shutil

from subprocess import call

from rasa_nlu.converters import load_data
from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer

path = os.path.join(os.getcwd(), 'data')
training_data = load_data(os.path.join(path, 'demo-rasa.json'))
trainer = Trainer(RasaNLUConfig(os.path.join(os.getcwd(),'project', 'config.json')))
trainer.train(training_data)
model_directory = trainer.persist('models')

with open(os.path.join(os.getcwd(),'project', 'config.json'),"r") as jsonFile:
            data = json.load(jsonFile)

data["active_model"] = str(model_directory)
with open(os.path.join(os.getcwd(),'project', 'config.json'),"w") as jsonFile:
            json.dump(data, jsonFile)