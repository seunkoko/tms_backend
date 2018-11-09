from flask import g, request, jsonify, json, current_app, url_for, Response
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...helper.error_message import moov_errors
    from ...models import SchoolInfo, User
    from ...schema import school_info_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import SchoolInfo, User
    from moov_backend.api.schema import school_info_schema


class SchoolResource(Resource):
    
    def get(self):
        _schools = SchoolInfo.query.order_by(SchoolInfo.name).all()
        school_count = len(_schools)

        schools = []
        for _school in _schools:
            _data, _ = school_info_schema.dump(_school)
            _data['name'] = _data['name'].upper()
            for item in ['account_number', 'bank_name', 'email', 'password', 'admin_status', 'reset_password']:
                _data.pop(item, None)
            schools.append(_data)

        return {
            'status': 'success',
            'data': { 
                'message': 'Schools successfully retrieved',
                'all_count': school_count,
                'schools': schools,
            }
        }, 200
