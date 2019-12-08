from google.cloud import datastore
from google.oauth2 import id_token
from google.auth.transport import requests
from flask import Flask, request, jsonify, make_response
from string import Template 
import json
import flask
import requests
import uuid
import time
import constants
import helpers
import secrets

app = flask.Flask(__name__)
app.secret_key = secrets.secret_key

CLIENT_ID = '426572973463-qitv62kthvs62hbuo85accc7um76hp1q.apps.googleusercontent.com'
CLIENT_SECRET = secrets.client_secret
REDIRECT_URI = 'https://hw-09-wilsoan6.appspot.com/oauth2callback'
SCOPES = 'openid email profile'

client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats to use this API or /home to register an account"\

######### AUTHENTICATION #########

@app.route('/home')
def home():
    return flask.render_template("index.html")

@app.route('/userinfo')
def userinfo():

    if 'credentials' not in flask.session:
        flask.session['oauth_state'] = str(uuid.uuid4())
        flask.session.modified = True
        return flask.redirect(flask.url_for('oauth2callback'))

    credentials = json.loads(flask.session['credentials'])

    if credentials['expires_in'] <= 0:
        flask.session['oauth_state'] = str(uuid.uuid4())
        flask.session.modified = True
        return flask.redirect(flask.url_for('oauth2callback'))        

    else:
        credentials = json.loads(flask.session['credentials'])
        jwt = credentials['id_token']
        person_info = helpers.validate_token(jwt)
        account_id = person_info[1]
        account_name = person_info[0]

        # if user doesn't exist in datastore, create new user
        # in either case, display id, token, and greeting
        if helpers.user_exists(client, account_id):
            message = "Welcome back " 
        else:
            new_user = datastore.Entity(client.key(constants.users))
            new_user.update({"id": account_id, 
                            "name": account_name})
            client.put(new_user)
            message = "Nice to meet you "

        flask.session.pop('oauth_state', None)
        flask.session.pop('credentials', None)

        return flask.render_template("userinfo.html", token = jwt, id = account_id, 
                                                      name = account_name, message = message)

        
@app.route('/oauth2callback')
def oauth2callback():

    time.sleep(.5) # without this it gives errors about 30% of the time

    if 'code' not in flask.request.args:
        auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                    '&client_id={}&redirect_uri={}&scope={}&state={}').format(CLIENT_ID, REDIRECT_URI, SCOPES, flask.session['oauth_state'])
        return flask.redirect(auth_uri)
    else:
        # Validate state
        if flask.request.args.get('state') != flask.session['oauth_state']:
             return flask.jsonify('Invalid state parameter.'), 401
        
        auth_code = flask.request.args.get('code')
        data = {'code': auth_code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'}
        r = requests.post('https://oauth2.googleapis.com/token', data=data)
        flask.session['credentials'] = r.text
        return flask.redirect(flask.url_for('userinfo'))

######### API #########

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():         
    
    # LIST ALL BOATS
    if request.method == 'GET':

        # Add pagination       
        query = client.query(kind=constants.boats)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))      
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)  
        pages = l_iterator.pages
        results = list(next(pages))
        total_num = len(list(query.fetch()))
        
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
        output["total_num_boats"] = total_num
        if next_url:
            output["next"] = next_url        
        return jsonify(output), 200

    # ADD BOAT
    elif request.method == 'POST':
        
        if 'Authorization' not in request.headers:
            return jsonify({"Error": "No token detected"}), 401
        
        token = request.headers['Authorization']
        validation_result = helpers.validate_token(token)

        if validation_result == "Invalid Token":
            return jsonify({"Error": "Invalid token"}), 401
        
        owner_name = validation_result[0]
        owner_id = validation_result[1]
        
        content = request.get_json()          

        # if all attributes present and valid, create boat and add to datastore
        new_boat = datastore.Entity(client.key(constants.boats))
        new_boat.update({   "name": content["name"], 
                            "type": content["type"],
                            "length": content["length"],
                            "owner": owner_name,
                            "owner_id": owner_id,
                            "slip": None})
        client.put(new_boat)

        # add id and self url to display object 
        new_boat.update({   "id" : str(new_boat.key.id), 
                            "self": request.url+"/"+str(new_boat.key.id)})
        
        # return boat to display
        return jsonify(new_boat), 201
    
    else:
        return jsonify({"Error": "Method not allowed"}), 405     

@app.route('/slips', methods=['POST','GET'])
def slips_get_post():         
    
    # LIST ALL SLIPS
    if request.method == 'GET':

        # Add pagination       
        query = client.query(kind=constants.slips)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))      
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)  
        pages = l_iterator.pages
        results = list(next(pages))
        total_num = len(list(query.fetch()))
        
        #create next url if necessary
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None        

        #add id and self urls
        for slip in results:
            slip["id"] = str(slip.key.id)
            slip["self"] = request.url+"/"+str(slip.key.id)

        # wrap slips in output object, including next url if available
        output = {"slips": results}
        output["total_num_slips"] = total_num
        if next_url:
            output["next"] = next_url        
        return jsonify(output), 200

    # ADD SLIP
    elif request.method == 'POST':
        
        if 'Authorization' not in request.headers:
            return jsonify({"Error": "No token detected"}), 401
        
        token = request.headers['Authorization']
        validation_result = helpers.validate_token(token)

        if validation_result == "Invalid Token":
            return jsonify({"Error": "Invalid token"}), 401
        
        owner_name = validation_result[0]
        owner_id = validation_result[1]
        
        content = request.get_json()          

        # if all attributes present and valid, create slip and add to datastore
        new_slip = datastore.Entity(client.key(constants.slips))
        new_slip.update({   "number": content["number"], 
                            "width": content["width"], 
                            "length": content["length"], 
                            "owner": owner_name,
                            "owner_id": owner_id,
                            "boat": None})
        client.put(new_slip)

        # add id and self url to display object 
        new_slip.update({   "id" : str(new_slip.key.id), 
                            "self": request.url+"/"+str(new_slip.key.id)})
        
        # return slip to display
        return jsonify(new_slip), 201
    
    else:
        return jsonify({"Error": "Method not allowed"}), 405     

@app.route('/users/<user_id>/boats', methods=['GET'])
def get_boats_belonging_to_user(user_id):  

    # LIST ALL BOATS OWNED BY USER
    
    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    if owner_id != user_id:
        return jsonify({"Error": "Token and URL id mismatch"}), 401

    # if auth good, make request

    if request.method == 'GET':
        query = client.query(kind=constants.boats)
        query.add_filter('owner_id', '=', user_id)
        
        #get all the boats
        results = list(query.fetch())

        #add id and self urls
        for boat in results:
            boat["id"] = str(boat.key.id)
            boat["self"] = request.url+"/"+str(boat.key.id)
        return jsonify(results), 200              

@app.route('/users/<user_id>/slips', methods=['GET'])
def get_slips_belonging_to_user(user_id):  

    # LIST ALL SLIPS OWNED BY USER
    
    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    if owner_id != user_id:
        return jsonify({"Error": "Token and URL id mismatch"}), 401

    # if auth good, make request
    
    if request.method == 'GET':
        query = client.query(kind=constants.slips)
        query.add_filter('owner_id', '=', user_id)
        
        #get all the slips
        results = list(query.fetch())

        #add id and self urls
        for slip in results:
            slip["id"] = str(slip.key.id)
            slip["self"] = request.url+"/"+str(slip.key.id)
        return jsonify(results), 200              

@app.route('/boats/<boat_id>', methods=['PATCH','PUT'])
def edit_boat_belonging_to_user(boat_id):  

    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    # find boat corresponding to ID
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)    

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 404    

    # if token bearer doesn't match boat owner, error
    if specific_boat["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this boat"}), 403 

    # if all is good, edit and return
    content = request.get_json()
    
    if request.method == 'PUT':
        
        # update entity
        specific_boat.update({"name": content["name"], 
                            "type": content["type"],
                            "length": content["length"]})   
        client.put(specific_boat)
    
    elif request.method == 'PATCH':
        
        # update entity
        for key, value in content.items():
            if key in specific_boat.keys():
                specific_boat[key] = value

        client.put(specific_boat)

    # add id and self URL to response
    specific_boat["id"] = str(specific_boat.key.id)
    specific_boat["self"] = request.url
    return jsonify(specific_boat), 200


@app.route('/boats/<boat_id>', methods=['DELETE'])
def delete_boat_belonging_to_user(boat_id):  

    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    # find boat corresponding to ID
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)    

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 404    

    # if token bearer doesn't match boat owner, error
    if specific_boat["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this boat"}), 403 

    # if all is good, delete and return
    client.delete(specific_boat_key)
    return "", 204

@app.route('/slips/<slip_id>', methods=['PATCH','PUT'])
def edit_slip_belonging_to_user(slip_id):  

    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    # find slip corresponding to ID
    specific_slip_key = client.key(constants.slips, int(slip_id))
    specific_slip = client.get(specific_slip_key)    

    # if there is no such slip, error
    if not specific_slip:
        return jsonify({"Error": "No slip with this slip_id exists"}), 404    

    # if token bearer doesn't match slip owner, error
    if specific_slip["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this slip"}), 403 

    # if all is good, edit and return
    content = request.get_json()
    
    if request.method == 'PUT':
        
        # update entity
        specific_slip.update({"number": content["number"], 
                            "width": content["width"], 
                            "length": content["length"]})                              
        client.put(specific_slip)
    
    elif request.method == 'PATCH':
        
        # update entity
        for key, value in content.items():
            if key in specific_slip.keys():
                specific_slip[key] = value

        client.put(specific_slip)

    # add id and self URL to response
    specific_slip["id"] = str(specific_slip.key.id)
    specific_slip["self"] = request.url
    return jsonify(specific_slip), 200

@app.route('/slips/<slip_id>', methods=['DELETE'])
def delete_slip_belonging_to_user(slip_id):  

    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401

    # find slip corresponding to ID
    specific_slip_key = client.key(constants.slips, int(slip_id))
    specific_slip = client.get(specific_slip_key)    

    # if there is no such slip, error
    if not specific_slip:
        return jsonify({"Error": "No slip with this slip_id exists"}), 404    

    # if token bearer doesn't match slip owner, error
    if specific_slip["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this slip"}), 403 

    # if all is good, delete and return
    client.delete(specific_slip_key)
    return "", 204

@app.route('/boats/<boat_id>/slips/<slip_id>/', methods=['PUT','DELETE'])
def boat_slip_put_delete(boat_id, slip_id):

    owner_id = helpers.authorize_user(request)

    if (int(owner_id) < 0):
        if int(owner_id) == -1:
            return jsonify({"Error": "No token detected"}), 401
        return jsonify({"Error": "Invalid token"}), 401    
    
    # find slip & boat corresponding to IDs
    specific_slip_key = client.key(constants.slips, int(slip_id))
    specific_slip = client.get(specific_slip_key)
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)

    # if there is no such slip, error
    if not specific_slip:
        return jsonify({"Error": "No slip with this slip_id exists"}), 404    

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 404    

    # if token bearer doesn't match boat owner, error
    if specific_boat["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this boat"}), 403       

    # if token bearer doesn't match slip owner, error
    if specific_slip["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this slip"}), 403     


    # BOAT ARRIVES AT SLIP
    if request.method == 'PUT':
        
        # if slip is occupied, error
        if specific_slip["boat"] is not None:
            return jsonify({"Error": "The slip is not empty"}), 403
        
        # if boat is already in a slip, error
        if specific_boat["slip"] is not None:
            return jsonify({"Error": "The boat is already at a slip"}), 403

        # add boat as current boat
        specific_slip.update({"boat": str(specific_boat.key.id)})   
        client.put(specific_slip)

        # add slip as current slip
        specific_boat.update({"slip": str(specific_slip.key.id)})   
        client.put(specific_boat)

        return "", 204
        
    # BOAT DEPARTS SLIP  
    elif request.method == 'DELETE':

        # if boat is not at this slip, error
        if specific_slip["boat"] != str(specific_boat.key.id) or specific_boat["slip"] != str(specific_slip.key.id):
            return jsonify({"Error": "No boat with this boat_id is at the slip with this slip_id"}), 404

        # remove boat from slip
        specific_slip.update({"boat": None})
        client.put(specific_slip)

        # remove slip from boat
        specific_boat.update({"slip": None})
        client.put(specific_boat)

        return "", 204

if __name__ == '__main__':
    app.debug = False
    app.run()        