from datetime import datetime, timedelta

from sqlalchemy import desc, and_

try:
    from ..models import FreeRide, Transaction
    from ..generator.free_ride_token_generator import generate_free_ride_token
    from ..schema import free_ride_schema
except ImportError:
    from moov_backend.api.models import FreeRide
    from moov_backend.api.generator.free_ride_token_generator import generate_free_ride_token
    from moov_backend.api.schema import free_ride_schema


def check_past_week_rides(user_id):
    day = datetime.today() - timedelta(days=7)
    past_week_rides = Transaction.query.filter(and_(
                            Transaction.sender_id==user_id,
                            Transaction.type_of_operation=="ride_type",
                            Transaction.transaction_date>=day
                        )).order_by(desc(Transaction.transaction_date)).limit(20).all()
    return past_week_rides

def check_latest_free_ride(user_id):
    latest_free_ride = FreeRide.query.filter(FreeRide.user_id==user_id).\
                            order_by(desc(FreeRide.created_at)).\
                            limit(1).first()
    return latest_free_ride

def get_free_ride_token(user):
    free_ride_token = None
    past_week_rides = check_past_week_rides(user.id)
    number_of_rides = len(past_week_rides)

    # set limit for rides in a week
    minimum_rides = 20
    if number_of_rides >= minimum_rides:
        latest_free_ride = check_latest_free_ride(user.id)

        # case of which the user has not gotten a free ride before
        if not latest_free_ride:
            free_ride_token = generate_free_ride_token(user.email)

        # case of the user has gotten a free ride and the last free ride
        # date is beyond the last week
        if latest_free_ride and (latest_free_ride.created_at < \
        past_week_rides[number_of_rides-1].transaction_date):
            free_ride_token = generate_free_ride_token(user.email)

    return free_ride_token

def save_free_ride_token(free_ride_type, token, description, user_id):
    new_free_ride = FreeRide(
                        free_ride_type=free_ride_type,
                        token=token,
                        token_status=True,
                        description=description,
                        user_id=user_id
                    )
    new_free_ride.save()
    return free_ride_schema.dump(new_free_ride)

def has_free_ride(user_id, free_ride_type):
    return FreeRide.query.filter(and_(
                FreeRide.user_id==user_id,
                FreeRide.free_ride_type==free_ride_type
            )).first()
