from google.cloud import datastore
from flask import Flask, request, jsonify, make_response
from string import Template 
import json
import constants
import helpers

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats to use this API"\

@app.route('/boats', methods=['POST'])
def boats_get_post():

    # Check that request is json & accepts a json response
    if not request.is_json:
        content = {"Error": "Request content type must be 'application/json'"}
        return jsonify(content), 406      

    if 'application/json' not in request.accept_mimetypes:
        content = {"Error": "'application/json' must be Accepted response format"}
        return jsonify(content), 406             
    
    # ADD BOAT
    if request.method == 'POST':
        content = request.get_json()

        #return 400 if content values are missing/invalid
        if not helpers.attributes_are_valid(content):
            content = {"Error": "The required attributes are missing or invalid"}
            return jsonify(content), 400

        if helpers.name_already_in_use(content["name"], client):
            content = {"Error": "Name already in use"}
            return jsonify(content), 403            

        # if all attributes present and valid, create boat and add to datastore
        new_boat = datastore.Entity(client.key(constants.boats))
        new_boat.update({   "name": content["name"], 
                            "type": content["type"],
                            "length": content["length"]})
        client.put(new_boat)

        # add id and self url to object and return
        new_boat.update({   "id" : str(new_boat.key.id), 
                            "self": request.url+"/"+str(new_boat.key.id)})
        return jsonify(new_boat), 201
    
    else:
        content = {"Error": "Method not allowed"}
        return jsonify(content), 405

@app.route('/boats/<boat_id>', methods=['PUT','PATCH','GET','DELETE'])
def specific_boat_get_edit_delete(boat_id):  

    # save content from request & find boat corresponding to ID
    content = request.get_json()
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 404

    # DELETE SPECIFIC BOAT
    if request.method == 'DELETE':

        client.delete(specific_boat_key)
        return "", 204

    # LIST SPECIFIC BOAT
    elif request.method == 'GET':

        # add id and self URL to display
        specific_boat["id"] = str(specific_boat.key.id)
        specific_boat["self"] = request.url
        
        # return json
        if 'application/json' in request.accept_mimetypes:
            
            return jsonify(specific_boat), 200

        # return html
        elif 'text/html' in request.accept_mimetypes:

            item = Template('$key: $value')

            html_string = "<ul>"
            for key in specific_boat:
                if key == "self":
                    html_string += "<li>self: <a href=\""+ specific_boat[key] +"\">" + specific_boat[key] + "</a></li>"

                else:
                    html_string += "<li>" + item.substitute(key=key,value=specific_boat[key]) + "</li>"
            html_string += "</ul>"

            return html_string, 200

        else:
            
            content = {"Error": "'application/json' or 'text/html' must be Accepted response format"}
            return jsonify(content), 406 
           
    # EDIT
    elif request.method == 'PUT' or request.method == 'PATCH':

        # Check that request is json
        if not request.is_json:
            content = {"Error": "Request content type must be 'application/json'"}
            return jsonify(content), 406 

        # check that request accepts a json response
        if 'application/json' not in request.accept_mimetypes:
            content = {"Error": "'application/json' must be Accepted response format"}
            return jsonify(content), 406 

        # PUT EDIT (edit all attributes)
        if request.method == 'PUT':
            
            #return 400 if content values are missing/invalid
            if not helpers.attributes_are_valid(content):
                content = {"Error": "The required attributes are missing or invalid"}
                return jsonify(content), 400

            if helpers.name_already_in_use(content["name"], client):
                content = {"Error": "Name already in use"}
                return jsonify(content), 403            

            # if all attributes present and valid, create boat and add to datastore
            specific_boat.update({  "name": content["name"], 
                                    "type": content["type"],
                                    "length": content["length"]})
            client.put(specific_boat)

            # add redirect header to response and return
            res = make_response()
            res.headers.set("Location",request.url)
            res.status_code = 303
            return res

        # PATCH EDIT (edit any attribute(s))
        else:
            #return 400 if content values are invalid
            if not helpers.attributes_are_valid_patch(content):
                content = {"Error": "The required attributes are invalid"}
                return jsonify(content), 400

            #if present, check if name is unique
            if "name" in content:
                if helpers.name_already_in_use(content["name"], client):
                    content = {"Error": "Name already in use"}
                    return jsonify(content), 403  

            # if attributes present and valid, create boat and add to datastore
            if "name" in content:
                specific_boat.update({"name": content["name"]})
            if "type" in content:
                specific_boat.update({"type": content["type"]})
            if "length" in content:
                specific_boat.update({"length": content["length"]})
            client.put(specific_boat)       

            # add id and self url to object and return
            specific_boat["id"] = str(specific_boat.key.id)
            specific_boat["self"] = request.url
            return jsonify(specific_boat), 200            

    else:
        content = {"Error": "Method not allowed"}
        return jsonify(content), 405

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)