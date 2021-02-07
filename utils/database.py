from firebase_admin.firestore import firestore

from config.firebase.database import TEWI_DB

# noinspection PyTypeChecker
OSU_DROID_COLLECTION: firestore.CollectionReference = TEWI_DB.collection('OSU!DROID')

# Collection of binded users for every binded discord_id
BINDED_DOCUMENT: firestore.DocumentReference = OSU_DROID_COLLECTION.document('BINDED_USERS')

# Collection of users with their respective data for every binded osu!droid uid
USERS_DOCUMENT: firestore.DocumentReference = OSU_DROID_COLLECTION.document('USERS_DATA')

# The most recent beatmap calculated collection
RECENT_CALC_DOCUMENT: firestore.DocumentReference = OSU_DROID_COLLECTION.document("RECENT_CALC")

# BR PLAYERS UIDS
BR_UIDS_DOCUMENT: firestore.DocumentReference = OSU_DROID_COLLECTION.document("BR_UIDS")
