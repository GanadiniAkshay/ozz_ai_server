from __future__ import absolute_import
from __future__ import print_function

import os

from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Metadata, Interpreter

from project import db, cache, interpreters, trainer, nlp, d

class NLUParser(object):
    def __init__(self, model, config, builder=None, percentage=0.65):
        self.model = model
        self.metadata = Metadata.load(self.model)
        self.config = config
        self.percentage = percentage
        if builder:
            self.interpreter = Interpreter.load(self.metadata, RasaNLUConfig(config),builder)
        else:
            self.interpreter = Interpreter.load(self.metadata, RasaNLUConfig(config))

    def parse(self, message):
        parsed_data = self.interpreter.parse(message)
        print(parsed_data)
        confidence = parsed_data['intent']['confidence']
        if confidence < self.percentage:
            intent = 'None'
        else:
            intent = parsed_data['intent']['name']
        entities = []
        for ent in parsed_data['entities']:
            entities.append({"entity":ent['entity'],"value":ent['value'],"start":ent['start'],"end":ent['end'],'type':'builtin'})
        duckling_entities = d.parse(message)
        for ent in duckling_entities:
            if ent['dim'] == 'time':
                if ent['value']['type'] == 'interval':
                    entities.append({"entity":'interval','type':'duckling',"start":ent['start'],"end":ent['end'],"value":[{"from":ent['value']['from']['value'], "to":ent['value']['to']['value']}]})
                elif ent['value']['type'] == 'value':
                    entities.append({"entity":"date",'type':'duckling',"start":ent['start'],"end":ent['end'],"value":ent['value']['value']})
        doc = nlp(message.title())
        spacy_entities = []
        for ent in doc.ents:
            if ent.label_ == 'GPE':
                start = message.title().find(ent.text)
                end = start + len(ent.text)
                entities.append({"entity": ent.label_, "start": start, "end": end,"value":ent.text,'type':'spacy'})
        return intent,entities,confidence