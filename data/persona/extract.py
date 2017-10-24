import os
import json

with open('./persona.json') as jsonFile:
    jsonData = json.loads(jsonFile.read())

    intents = jsonData['ozz_data']['intents']

    responses = {}

    for intent in intents:
        responses[intent['name']] = []

    with open('./millenial/millenial.json','w') as outFile:
        json.dump(responses,outFile, indent=2)
