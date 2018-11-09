import os

from flask import request, jsonify, json, Response
from flask_restful import Resource
from flask import g, request, jsonify

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data
    from ...generator.free_ride_token_generator import generate_free_ride_token
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.notification_helper import save_notification
    from ...helper.free_ride_helper import save_free_ride_token, has_free_ride
    from ...models import User, FreeRide, Icon, FreeRideType
    from ...schema import free_ride_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.generator.free_ride_token_generator import generate_free_ride_token
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.helper.free_ride_helper import save_free_ride_token, has_free_ride
    from moov_backend.api.models import User, FreeRide, Icon, FreeRideType
    from moov_backend.api.schema import free_ride_schema


class FreeRideResource(Resource):
    
    @token_required
    @validate_request()
    def post(self):
        json_input = request.get_json()

        keys = ['free_ride_type']

        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        _free_ride_type = json_input["free_ride_type"]
        if str(_free_ride_type) not in ["social_share_type"]:
            return moov_errors('Free ride type does not exist', 400)

        if str(_free_ride_type) == "social_share_type":
            if not has_free_ride(user_id=_user_id, free_ride_type=FreeRideType.social_share_type):
                moov_email = os.environ.get("MOOV_EMAIL")
                moov_user = User.query.filter(User.email==moov_email).first()
                if not moov_user:
                    return not_found_errors(moov_email)

                _transaction_icon = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"
                transaction_icon = Icon.query.filter(Icon.operation_type=="free_ride_operation").first()
                if transaction_icon:
                    _transaction_icon_id = transaction_icon.id

                token = generate_free_ride_token(user_email=_user.email)
                description = "{0} generated to {1} for publisicing moov app".format(
                                    token,
                                    _user.email
                                )
                message = "Congrats, you got a free ride token {0} for sharing our app".format(
                                token
                            )

                save_notification(
                    recipient_id=_user_id,
                    sender_id=moov_user.id,
                    message=message,
                    transaction_icon_id=_transaction_icon_id
                )
                _data, _ = save_free_ride_token(
                                free_ride_type=FreeRideType.social_share_type,
                                token=token,
                                description=description,
                                user_id=_user_id
                            )
                return {
                    'status': 'success',
                        'data': {
                            'free_ride': _data
                        }
                    }, 201
                        

        # cases that don't meet any of the free ride conditions
        # cases that the user has collected a free ride for a particular free_ride_type
        return moov_errors("Free ride collection denied", 400)
