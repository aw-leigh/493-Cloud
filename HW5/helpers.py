import constants
import json

# returns true if 
# reference: https://stackoverflow.com/a/18403812
def is_ascii(string):
    try: 
        string.encode('ascii')
    except UnicodeEncodeError: 
        return False
    return True

# returns false if content has null, blank, or invalid "name", "type", and "length" attributes
def attributes_are_valid(content, client):
    if "name" not in content or "type" not in content or "length" not in content:
        return False
    if content["name"] == "" or content["type"] == "" or content["length"] == "":
        return False        
    if len(content["name"]) > 255 or not is_ascii(content["name"]):
        return False
    if len(content["type"]) > 255 or not is_ascii(content["type"]):
        return False       
    if content["length"] < 0 or content["length"] > 10000:
        return False
    return True

# returns false if content has null, blank, or invalid "name", "type", and "length" attributes
def attributes_are_valid_patch(content, client):
    if content["name"] == "" or content["type"] == "" or content["length"] == "":
        return False        
    if len(content["name"]) > 255 or not is_ascii(content["name"]):
        return False
    if len(content["type"]) > 255 or not is_ascii(content["type"]):
        return False       
    if content["length"] < 0 or content["length"] > 10000:
        return False
    return True

# returns true if boat name is already in use, otherwise false
def name_already_in_use(name, client):

    #get all the boats
    query = client.query(kind=constants.boats)
    all_boats = list(query.fetch())

    #check each name
    for boat in all_boats:
        if boat["name"] == name:
            return True
 
    return False