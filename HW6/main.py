import json
import flask
import requests
import uuid
import time

app = flask.Flask(__name__)
app.secret_key = b'7ec0ebca067547c999505ab3935846eb'

CLIENT_ID = '796815400065-upu8g3805u4f4n6qj5jesaj40vruhnkk.apps.googleusercontent.com'
CLIENT_SECRET = 'dOwYyQLEKzMUyAbV6N9e0hLT'
REDIRECT_URI = 'https://hw-06-wilsoan6.appspot.com/oauth2callback'
SCOPES = 'email profile'

@app.route('/')
def index():
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

        headers = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
        req_uri = 'https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses'
        r = requests.get(req_uri, headers=headers).json()
        s = flask.session['oauth_state']

        flask.session.pop('oauth_state', None)
        flask.session.pop('credentials', None)

        return flask.render_template("userinfo.html", fname = r["names"][0]["givenName"], 
                                     lname = r["names"][0]["familyName"], state = s)
        

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

if __name__ == '__main__':
    app.debug = False
    app.run()        