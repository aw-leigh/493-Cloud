from google.cloud import datastore
from flask import Flask, request, jsonify
import json
import constants
import helpers

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats or /slips to use this API"\

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    # ADD BOAT
    if request.method == 'POST':
        content = request.get_json()

        #return 400 if content values are missing
        if helpers.check_attributes_validity(content, constants.boats) == -1:
            content = {"Error": "The request object is missing at least one of the required attributes"}
            return jsonify(content), 400

        # if all attributes present, create boat and add to datastore
        new_boat = datastore.Entity(client.key(constants.boats))
        new_boat.update({   "name": content["name"], 
                            "type": content["type"],
                            "length": content["length"]})
        client.put(new_boat)

        # add id and self url to object and return
        new_boat.update({   "id" : str(new_boat.key.id), 
                            "self": request.url+"/"+str(new_boat.key.id)})
        return jsonify(new_boat), 201

    # LIST ALL BOATS
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        
        #get all the boats
        results = list(query.fetch())

        #add id and self urls
        for boat in results:
            boat["id"] = str(boat.key.id)
            boat["self"] = request.url+"/"+str(boat.key.id)
        return jsonify(results), 200
    
    else:
        return 'Method not recogonized'

@app.route('/boats/<boat_id>', methods=['PATCH','GET','DELETE'])
def specific_boat_get_patch_delete(boat_id):
    
    # save content from request & find boat corresponding to ID
    content = request.get_json()
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 404

    # LIST SPECIFIC BOAT
    if request.method == 'GET':

        # add id and self URL to display
        specific_boat["id"] = str(specific_boat.key.id)
        specific_boat["self"] = request.url
        return jsonify(specific_boat), 200
        
    # EDIT SPECIFIC BOAT
    elif request.method == 'PATCH':
        
        # return 400 if content values are missing
        if helpers.check_attributes_validity(content, constants.boats) == -1:
            content = {"Error": "The request object is missing at least one of the required attributes"}
            return jsonify(content), 400
        
        # otherwise, update entity
        specific_boat.update({"name": content["name"], 
                            "type": content["type"],
                            "length": content["length"]})   
        client.put(specific_boat)

        # add id and self URL to response
        specific_boat["id"] = str(specific_boat.key.id)
        specific_boat["self"] = request.url
        return jsonify(specific_boat), 200
    
    # DELETE SPECIFIC BOAT
    elif request.method == 'DELETE':

        # if boat was at a slip, remove it from slip
        query = client.query(kind=constants.slips)
        results = list(query.fetch())
        for slip in results:
            if slip["current_boat"] == str(specific_boat.key.id):
                specific_slip_key = client.key(constants.slips, slip.key.id)
                specific_slip = client.get(specific_slip_key)
                specific_slip.update({"current_boat": None})
                client.put(specific_slip)

        client.delete(specific_boat_key)
        return "", 204

    else:
        return 'Method not recogonized'

@app.route('/slips', methods=['POST','GET'])
def slips_get_post():
    # ADD SLIP
    if request.method == 'POST':
        content = request.get_json()

        #return 400 if content values are missing
        if helpers.check_attributes_validity(content, constants.slips) == -1:
            content = {"Error": "The request object is missing the required number"}
            return jsonify(content), 400

        # if all attributes present, create slip and add to datastore
        new_slip = datastore.Entity(client.key(constants.slips))
        new_slip.update({"number": content["number"], "current_boat": None})
        client.put(new_slip)

        # add id and self url to object and return
        new_slip.update({   "id" : str(new_slip.key.id), 
                            "self": request.url+"/"+str(new_slip.key.id)})
        return jsonify(new_slip), 201

    # LIST ALL SLIPS
    elif request.method == 'GET':
        query = client.query(kind=constants.slips)
        
        #get all the slips
        results = list(query.fetch())

        #add id and self urls
        for slip in results:
            slip["id"] = str(slip.key.id)
            slip["self"] = request.url+"/"+str(slip.key.id)
        return jsonify(results), 200

    else:
        return 'Method not recogonized'

@app.route('/slips/<slip_id>', methods=['GET','DELETE'])
def specific_slip_get_delete(slip_id):
    
    # find slip corresponding to ID
    specific_slip_key = client.key(constants.slips, int(slip_id))
    specific_slip = client.get(specific_slip_key)

    # if there is no such slip, error
    if not specific_slip:
        return jsonify({"Error": "No slip with this slip_id exists"}), 404

    # LIST SPECIFIC SLIP
    if request.method == 'GET':

        # add id and self URL to display
        specific_slip["id"] = str(specific_slip.key.id)
        specific_slip["self"] = request.url
        return jsonify(specific_slip), 200
        
    # DELETE SPECIFIC SLIP   
    elif request.method == 'DELETE':
        client.delete(specific_slip_key)
        return "", 204

    else:
        return 'Method not recogonized'


@app.route('/slips/<slip_id>/<boat_id>', methods=['PUT','DELETE'])
def boat_slip_put_delete(slip_id, boat_id):
    
    # find slip & boat corresponding to IDs
    specific_slip_key = client.key(constants.slips, int(slip_id))
    specific_slip = client.get(specific_slip_key)
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)

    # BOAT ARRIVES AT SLIP
    if request.method == 'PUT':

        # if there is no such slip or boat, error
        if not specific_slip or not specific_boat:
            return jsonify({"Error": "The specified boat and/or slip don’t exist"}), 404
        
        # if slip is occupied, error
        if specific_slip["current_boat"] is not None:
            return jsonify({"Error": "The slip is not empty"}), 403

        # add boat as current boat
        specific_slip.update({"current_boat": str(specific_boat.key.id)})   
        client.put(specific_slip)
        return "", 204
        
    # BOAT DEPARTS SLIP  
    elif request.method == 'DELETE':

        # if boat is not at this slip, error
        if not specific_slip or not specific_boat or specific_slip["current_boat"] != str(specific_boat.key.id):
            return jsonify({"Error": "No boat with this boat_id is at the slip with this slip_id"}), 404

        # remove boat from slip
        specific_slip.update({"current_boat": None})
        client.put(specific_slip)
        return "", 204

    else:
        return 'Method not recogonized'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)