try:
    from .error_message import moov_errors
    from ..models import User, AuthenticationType
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import User, SchoolInfo, AuthenticationType

# get any user by email
def get_user(email):
    _user = User.query.filter(User.email==email).first()
    return _user

# get authentication type
def get_authentication_type(authentication_type):
    if (str(authentication_type) == "facebook"):
        return AuthenticationType.facebook
    if (str(authentication_type) == "google"):
        return AuthenticationType.google
    return AuthenticationType.email
