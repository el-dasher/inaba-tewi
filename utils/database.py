from firebase_admin.firestore import firestore

from config.firebase.database import TEWI_DB

# Collection of binded users for every binded discord_id
# noinspection PyTypeChecker
BINDED_DOCUMENT: firestore.DocumentReference = TEWI_DB.collection('OSU!DROID').document('BINDED_USERS')

# Collection of users with their respective data for every binded osu!droid uid
# noinspection PyTypeChecker
USERS_DOCUMENT: firestore.DocumentReference = TEWI_DB.collection('OSU!DROID').document('USERS_DATA')

# The most recent beatmap calculated collection
# noinspection PyTypeChecker
RECENT_CALC_DOCUMENT: firestore.DocumentReference = TEWI_DB.collection('OSU!DROID').document("RECENT_CALC")
