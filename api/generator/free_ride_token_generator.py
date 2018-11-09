import uuid
from datetime import datetime, timedelta

try:
    from ..models import FreeRide
except:
    from moov_backend.api.models import FreeRide


# free-ride token generator 
def generate_free_ride_token(user_email):
    free_ride_token = None
    count = 1

    # runs until a unique token is generated
    while not free_ride_token:
        payload = "{0} {1} {2}".format(user_email, str(datetime.now()), count)
        generated_token = uuid.uuid5(uuid.NAMESPACE_DNS, payload)
        _token_found = FreeRide.query.filter(FreeRide.token==str(generated_token)).first()
        count += 1

        if not _token_found:
            free_ride_token = str(generated_token)

    return free_ride_token
