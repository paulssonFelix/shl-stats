import os
from dotenv import load_dotenv
import requests

load_dotenv()

BASE_URL = 'https://openapi.shl.se'

client_id = os.environ.get('CLIENT_ID') or ''
client_secret = os.environ.get('CLIENT_SECRET') or ''

print(client_id, client_secret)

r = requests.post(BASE_URL + '/oauth2/token',
                  data={'grant_type': 'client_credentials',
                        'client_id': client_id,
                        'client_secret': client_secret})

print(r.json)

# token = r.json()['access_token']
#
# r = requests.get(BASE_URL + '/teams',
#                  headers={'Authorization': 'Bearer ' + token})
#
# print(r.headers)
# print(r.data)
