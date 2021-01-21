from os import getenv

_private_key: str = getenv('FIREBASE_PRIVATE_KEY')
_client_email: str = getenv('FIREBASE_CLIENT_EMAIL')

FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": "inaba-tewi",
    "private_key_id": '50273fec344800ddde96a7a404ae169f83772e0d',
    "private_key": _private_key,
    "client_email": _client_email,
    "client_id": "113776714437717713937",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{_client_email}"
}
