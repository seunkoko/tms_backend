try:
    from .error_message import moov_errors
    from ..models import Wallet
    from ..helper.user_helper import get_user
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import Wallet
    from moov_backend.api.helper.user_helper import get_user

# get any user wallet by id or user_email
def get_wallet(user_id=None, email=None):
    _user_id = user_id

    if email:
        _user = get_user(email)
        if not _user:
            return _user
        _user_id = _user.id

    return Wallet.query.filter(Wallet.user_id==_user_id).first()
