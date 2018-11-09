try:
    from .error_message import moov_errors
    from ..models import SchoolInfo
except ImportError:
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import SchoolInfo


# get any school by name
def get_school(name):
    _school = SchoolInfo.query.filter(SchoolInfo.name==name).first()
    return _school
