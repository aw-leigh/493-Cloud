from google.cloud import datastore
from flask import Flask, request, jsonify
import json
import constants
import helpers

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats or /loads to use this API"\

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
                            "length": content["length"],
                            "loads": []})
        client.put(new_boat)

        # add id and self url to object and return
        new_boat.update({   "id" : str(new_boat.key.id), 
                            "self": request.url+"/"+str(new_boat.key.id)})
        return jsonify(new_boat), 201

    # LIST ALL BOATS
    elif request.method == 'GET':

        # Add pagination       
        query = client.query(kind=constants.boats)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))      
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)  
        pages = l_iterator.pages
        results = list(next(pages))
        
        #create next url if necessary
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None        

        #add id and self urls
        for boat in results:
            boat["id"] = str(boat.key.id)
            boat["self"] = request.url+"/"+str(boat.key.id)

        # wrap boats in output object, including next url if available
        output = {"boats": results}
        if next_url:
            output["next"] = next_url        
        return jsonify(output), 200
    
    else:
        return 'Method not recogonized'

@app.route('/boats/<boat_id>', methods=['PATCH','GET','DELETE'])
def specific_boat_get_delete(boat_id):
    
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
           
    # DELETE SPECIFIC BOAT
    elif request.method == 'DELETE':

        # if boat had a load, remove boat from their 'carrier' fields
        for load in specific_boat["loads"]:
            specific_load_key = client.key(constants.loads, load["id"])
            specific_load = client.get(specific_load_key)
            specific_load["carrier"] = []
            client.put(specific_load)

        client.delete(specific_boat_key)
        return "", 204

    else:
        return 'Method not recogonized'

@app.route('/loads', methods=['POST','GET'])
def loads_get_post():
    # ADD LOAD
    if request.method == 'POST':
        content = request.get_json()

        #return 400 if content values are missing
        if helpers.check_attributes_validity(content, constants.loads) == -1:
            content = {"Error": "The request object is missing the required number"}
            return jsonify(content), 400

        # if all attributes present, create load and add to datastore
        new_load = datastore.Entity(client.key(constants.loads))
        new_load.update({   "weight": content["weight"],
                            "content": content["content"],
                            "delivery_date": content["delivery_date"],
                            "carrier": []})
        client.put(new_load)

        # add id and self url to object and return
        new_load.update({   "id" : str(new_load.key.id), 
                            "self": request.url+"/"+str(new_load.key.id)})
        return jsonify(new_load), 201

    # LIST ALL LOADS
  
    elif request.method == 'GET':

        # Add pagination       
        query = client.query(kind=constants.loads)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))      
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)  
        pages = l_iterator.pages
        results = list(next(pages))
        
        #create next url if necessary
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None        

        #add id and self urls
        for load in results:
            load["id"] = str(load.key.id)
            load["self"] = request.url+"/"+str(load.key.id)

        # wrap loads in output object, including next url if available
        output = {"loads": results}
        if next_url:
            output["next"] = next_url        
        return jsonify(output), 200        

    else:
        return 'Method not recogonized'

@app.route('/loads/<load_id>', methods=['GET','DELETE'])
def specific_load_get_delete(load_id):
    
    # find load corresponding to ID
    specific_load_key = client.key(constants.loads, int(load_id))
    specific_load = client.get(specific_load_key)

    # if there is no such load, error
    if not specific_load:
        return jsonify({"Error": "No load with this load_id exists"}), 404

    # LIST SPECIFIC LOAD
    if request.method == 'GET':

        # add id and self URL to display
        specific_load["id"] = str(specific_load.key.id)
        specific_load["self"] = request.url
        return jsonify(specific_load), 200
        
    # DELETE SPECIFIC LOAD   
    elif request.method == 'DELETE':

    #Delete load from boat carrying it     
        for carrier in specific_load["carrier"]:
            specific_boat_key = client.key(constants.boats, carrier["id"])
            specific_boat = client.get(specific_boat_key)

            for load in specific_boat["loads"]:
                if load["id"] == specific_load.key.id:
                    idx = specific_boat["loads"].index(load)
                    specific_boat["loads"].pop(idx)
                    client.put(specific_boat)

        client.delete(specific_load_key)
        return "", 204

    else:
        return 'Method not recogonized'

@app.route('/boats/<boat_id>/loads/<load_id>', methods=['PUT','DELETE'])
def boat_load_put_delete(boat_id, load_id):
    
    # find load & boat corresponding to IDs
    specific_load_key = client.key(constants.loads, int(load_id))
    specific_load = client.get(specific_load_key)
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)

    # if there is no such load or boat, error
    if not specific_load or not specific_boat:
        return jsonify({"Error": "The specified load and/or boat don’t exist"}), 404

    # PUT LOAD ON BOAT
    if request.method == 'PUT':

        # if load is already assigned, error 403
        if specific_load["carrier"] != []:
            return jsonify({"Error": "The load is already assigned"}), 403

        # add boat as current carrier
        specific_load["carrier"].append(  
            {"id": int(specific_boat.key.id),
            "name": specific_boat["name"],
            "self": request.url_root+"/boats/"+str(specific_boat.key.id)})
        client.put(specific_load)

        # # add load to boat
        specific_boat["loads"].append(
            {"id": int(specific_load.key.id),
            "self": request.url_root+"/loads/"+str(specific_load.key.id)})
        client.put(specific_boat)
        return "", 204
        
    # REMOVE LOAD FROM BOAT
    elif request.method == 'DELETE':

        # remove load from boat, error if load is not in boat
        for load in specific_boat["loads"]:
            if load["id"] == specific_load.key.id:
                specific_load["carrier"] = []
                client.put(specific_load)

                idx = specific_boat["loads"].index(load)
                specific_boat["loads"].pop(idx)
                client.put(specific_boat)
                return "", 204

        return jsonify({"Error": "No load with this load_id is on the boat with this boat_id"}), 404

    else:
        return 'Method not recogonized'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)