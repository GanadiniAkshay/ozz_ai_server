def generate(string,sub_string,values):
    new_string = string.replace(sub_string, "*_*")
    new_strings = [string]
    for value in values:
        new = new_string.replace('*_*',value)
        new_strings.append(new)
    return new_strings

print(generate('Somewhere in new york','new york',['NYC','nyc','new york city','the big apple']))

