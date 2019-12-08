import requests
import constants

# validates id_token. Returns name if valid, "Invalid Token" if not valid
def validate_token(token):
    
    if 'Bearer' in token:
        token = token[7:]

    response = requests.get('https://oauth2.googleapis.com/tokeninfo?id_token=' + token)
    
    if response.status_code != 200:
        return "Invalid Token"
    
    r_json = response.json()
    
    return r_json["name"], r_json["sub"]


def user_exists(client, account_id):
    query = client.query(kind=constants.users)
    results = list(query.fetch())

    for user in results:
        if user["id"] == account_id:
            return True
    return False