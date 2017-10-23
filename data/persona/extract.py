import os
import json

files = os.listdir('./Small-Talk/intents')

generated = {"intents":[]}
intents = []

for file in files:
    name = file.split('.')[-2]

    if "_usersays_" not in name:
        continue
    
    else:
        intent_obj = {"name":name,"utterances":[]}
        utterances = []
        with open('./Small-Talk/intents/' + file) as jsonFile:
            jsonData = json.loads(jsonFile.read())
            
            for value in jsonData:
                text = ""
                for example in value['data']:
                    text+=example['text']
                utterances.append(text)
        intent_obj["utterances"] = utterances
        intents.append(intent_obj)

generated["intents"] = intents

with open('extracted.json','w') as outFile:
    json.dump(generated,outFile)