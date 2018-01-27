import json
from pprint import pprint


new_json = {
    "ozz_data":{
        "entities":[],
        "intents":[]
    }
}

new_intents = []

qdata = json.load(open('./data/persona/professional/persona_professional.json'))
intents = qdata["ozz_data"]["intents"]

rdata = json.load(open('./data/persona/professional/professional.json'))

for intent_obj in intents:
    new_int_obj = {}
    name = intent_obj["name"]
    new_int_obj["name"] = name
    new_int_obj["utterances"] = intent_obj["utterances"]

    if name in rdata:
        new_int_obj["responses"] = rdata[name]
    else:
        new_int_obj["responses"] = []
    new_intents.append(new_int_obj)

new_json["ozz_data"]["intents"] =  new_intents

with open('./data/persona/professional/import_persona_professional.json','w') as outFile:
    json.dump(new_json, outFile)