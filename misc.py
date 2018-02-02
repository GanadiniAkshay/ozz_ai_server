import json
from pprint import pprint

import eliza


new_json = {
    "ozz_data":{
        "entities":[],
        "intents":[]
    }
}

new_intents = []


for obj in eliza.psychobabble:
    new_intent_obj = {}

    new_intent_obj['name'] = 'eliza.placeholder'
    phrase = obj[0]
    phrase = phrase.replace('(.*)','@capture')
    phrase = phrase.replace('([^\?]*)','@capture')
    phrase = phrase.replace("\'?","'")
    phrase = phrase.replace("\'","'")

    new_intent_obj['utterances'] = [phrase]

    new_intent_obj['responses']  = []
    answers = obj[1]
    for answer in answers:
        answer = answer.replace('{0}','@capture')
        new_intent_obj['responses'].append(answer)
    
    new_intents.append(new_intent_obj)


new_json['ozz_data']['intents'] = new_intents


with open("eliza.json","w") as jsonFile:
    json.dump(new_json,jsonFile)