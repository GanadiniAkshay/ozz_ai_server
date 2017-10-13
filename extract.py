from bs4 import BeautifulSoup
import sys
from urllib import request
import json

# html = ['http://www.expertasig.ro/dictionar/car_terms.php']

# for link in html:
#     webpage = request.urlopen(link).read()
#     soup = BeautifulSoup(webpage,"lxml")
    
#     # kill all script and style elements
#     for script in soup(["script", "style"]):
#         script.extract()    # rip it out
    
#     text = soup.get_text()
#     lines = (line.strip() for line in text.splitlines())

#     for line in lines:
#         print(line)

data = {}
with open('file1.txt','r') as file:
    key = True
    key_val = ""
    for line in file:
        if key:
            key_val = line.strip()
            key = not key
        else:
            data[key_val] = [line.strip()]
            key = not key

print(data)

with open('file1.txt','r') as file:
    key = True
    key_val = ""
    for line in file:
        if key:
            key_val = line.strip()
            key = not key
        else:
            if key_val in data:
                data[key_val].append(line.strip())
            else:
                data[key_val] = [line.strip()]
            key = not key

json.dump(data, output)

