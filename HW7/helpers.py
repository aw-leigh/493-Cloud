import requests

# validates id_token. Returns name if valid, "Invalid Token" if not valid
def validate_token(token):
    
    response = requests.get('https://oauth2.googleapis.com/tokeninfo?id_token=' + token[7:])
    
    if response.status_code != 200:
        return "Invalid Token"
    
    r_json = response.json()
    
    return r_json["name"], r_json["sub"]