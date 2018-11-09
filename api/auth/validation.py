from functools import wraps

from flask import request, jsonify

from ..helper.error_message import moov_errors


def validate_empty_string(value):
    if value == "" or value.strip() == "":
        return True
    return False

def validate_type(item, input_type):
    return type(item) is input_type

def validate_input_data(data, keys, resource=None):
    if not set(list(data.keys())) <= set(keys):
        return moov_errors('No invalid field(s) allowed', 400)

def validate_request():
    """ This method validates the Request payload.
    Args
        expected_args(tuple): where i = 0 is type and i > 0 is argument to be
                            validated
    Returns
      f(*args, **kwargs)
    """

    def real_validate_request(f):
        @wraps(f)
        def decorated(*args,**kwargs):
            if not request.json:
                return {"status": "fail",
                        "data": {"message": "Request must be a valid JSON"}
                       }, 400

            return f(*args, **kwargs)

        return decorated

    return real_validate_request
