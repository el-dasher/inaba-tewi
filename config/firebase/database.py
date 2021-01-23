import firebase_admin
from firebase_admin import firestore
from firebase_admin.credentials import Certificate

from .firebase_sdk_config import FIREBASE_CONFIG

firebase_credential: Certificate = Certificate(FIREBASE_CONFIG)

TEWI_FIREBASE_APP: firebase_admin.App = firebase_admin.initialize_app(firebase_credential)
TEWI_DB: firestore.firestore.Client = firestore.client(TEWI_FIREBASE_APP)
