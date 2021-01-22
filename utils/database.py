from config.firebase.database import TEWI_DB

# noinspection PyTypeChecker
# Collection of binded users for every binded discord_id
binded_collection = TEWI_DB.collection('OSU!DROID').document('BINDED_USERS')

# Collection of users with their respective data for every binded osu!droid uid
users_collection = TEWI_DB.collection('OSU!DROID').document('BINDED_USERS')
