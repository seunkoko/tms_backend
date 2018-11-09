import os
import math

try:
    from ..auth.validation import validate_request, validate_input_data, validate_empty_string
    from ..models import User, Icon
except ImportError:
    from moov_backend.api.auth.validation import validate_empty_string
    from moov_backend.api.models import User, Icon

# common helper functions

def get_distance(lat1, lon1, lat2, lon2, unit):
  """Get Distance
  This method gets two distance between 2 latitude and longitude in 
  both kilometers and nautical miles
  """
  radlat1 = math.pi * lat1/180
  radlat2 = math.pi * lat2/180
  theta = lon1 - lon2
  radtheta = math.pi * theta/180
  dist = (math.sin(radlat1) * math.sin(radlat2)) + \
          (math.cos(radlat1) * math.cos(radlat2) * math.cos(radtheta))
  dist = math.acos(dist)
  dist = dist * 180/math.pi
  dist = dist * 60 * 1.1515
  
  if unit.lower() == "k":
    dist = dist * 1.609344
    
  if unit.lower() == "n":
    dist = dist * 0.8684
    
  return int(round(dist, 0))


def is_empty_request_fields(json_input):
    """Check empty request fields
    Method returns True if there is an empty field in
    the request body
    """
    for key in json_input.keys():
        if type(json_input[key]) == str or type(json_input[key]) == unicode:
            if validate_empty_string(json_input[key]):
                return True
    return False


def is_user_type_authorized(unauthorized_list, user_type):
    """Check user type authorization
    Method returns True if the user_type is in the 
    unauthorized list
    """
    if user_type in unauthorized_list:
        return True
    return False


def get_moov_user():
    """Get moov user
    Method gets the default moov user
    """
    moov_email = os.environ.get("MOOV_EMAIL")
    moov_user = User.query.filter(User.email==moov_email).first()
    if moov_user:
        return moov_user


def get_icon_id(operation):
    """Get Icon id
    Method gets the icon id of the operation passed in as
    parameter and returns the default icon if not found
    """
    default_icon = Icon.query.filter(Icon.operation_type=="moov_operation").first()
    transaction_icon = Icon.query.filter(Icon.operation_type==operation).first()
    if transaction_icon:
        return transaction_icon.id
    if default_icon:
        return default_icon.id


def remove_unwanted_keys(data, keys_to_remove):
    """Removes unwanted keys
    Method returns data after removing unwanted keys 
    """
    for key in keys_to_remove:
        data.pop(key, None)
    return data
