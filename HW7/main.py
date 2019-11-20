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

app = flask.Flask(__name__)
app.secret_key = b'7ec0ebca067547c999505ab3935846eb'

CLIENT_ID = '105875411913-2gnpj66tpqc3p6knudpgriihkm5qeauh.apps.googleusercontent.com'
CLIENT_SECRET = 'ImFR4fJgRT0qLzeMG0-Lu_2T'
REDIRECT_URI = 'https://hw-07-wilsoan6.appspot.com/oauth2callback'
SCOPES = 'openid email profile'

client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats or /home to use this API"\

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

        flask.session.pop('oauth_state', None)
        flask.session.pop('credentials', None)

        return flask.render_template("userinfo.html", token = jwt)
        
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
        query = client.query(kind=constants.boats)
        
        #get all the boats
        results = list(query.fetch())

        #add id and self urls, remove owner id
        for boat in results:
            boat["id"] = str(boat.key.id)
            boat["self"] = request.url+"/"+str(boat.key.id)
            boat.pop("owner_id", None)
        return jsonify(results), 200

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
                            "owner": owner_name,
                            "owner_id": owner_id,
                            "length": content["length"]})
        client.put(new_boat)

        # add id and self url to display object 
        new_boat.update({   "id" : str(new_boat.key.id), 
                            "self": request.url+"/"+str(new_boat.key.id)})
        
        # remove owner id from display object and return
        new_boat.pop("owner_id", None)
        return jsonify(new_boat), 201
    
    else:
        return 'Method not recogonized'        

@app.route('/users/<user_id>/boats', methods=['GET'])
def get_boats_belonging_to_user(user_id):  
# my id: 103017034770342567702

    if 'Authorization' not in request.headers:
        return jsonify({"Error": "No token detected"}), 401
    
    token = request.headers['Authorization']
    validation_result = helpers.validate_token(token)

    if validation_result == "Invalid Token":
        return jsonify({"Error": "Invalid token"}), 401

    owner_id = validation_result[1]

    if owner_id != user_id:
        return jsonify({"Error": "Token and URL id mismatch"}), 401

    # LIST ALL BOATS MATCHING USER
    if request.method == 'GET':
        query = client.query(kind=constants.boats)
        query.add_filter('owner_id', '=', user_id)
        
        #get all the boats
        results = list(query.fetch())

        #add id and self urls, remove owner id
        for boat in results:
            boat["id"] = str(boat.key.id)
            boat["self"] = request.url+"/"+str(boat.key.id)
            boat.pop("owner_id", None)
        return jsonify(results), 200              

@app.route('/boats/<boat_id>', methods=['DELETE'])
def delete_boat_belonging_to_user(boat_id):  
# my id: 103017034770342567702

    if 'Authorization' not in request.headers:
        return jsonify({"Error": "No token detected"}), 401
    
    token = request.headers['Authorization']
    validation_result = helpers.validate_token(token)

    if validation_result == "Invalid Token":
        return jsonify({"Error": "Invalid token"}), 401

    owner_id = validation_result[1]

    # find boat corresponding to ID
    specific_boat_key = client.key(constants.boats, int(boat_id))
    specific_boat = client.get(specific_boat_key)    

    # if there is no such boat, error
    if not specific_boat:
        return jsonify({"Error": "No boat with this boat_id exists"}), 403    

    # if token bearer doesn't match boat owner, error
    if specific_boat["owner_id"] != owner_id:
        return jsonify({"Error": "You do not own this boat"}), 403 

    # if all is good, delete and return
    client.delete(specific_boat_key)
    return "", 204


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)