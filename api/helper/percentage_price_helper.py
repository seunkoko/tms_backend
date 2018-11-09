try:
    from .error_message import moov_errors
    from ..models import PercentagePrice
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import PercentagePrice

# get percentage prices by title
def get_percentage_price(title):
    _percentage_price = PercentagePrice.query.filter(PercentagePrice.title==title).first()
    return _percentage_price
