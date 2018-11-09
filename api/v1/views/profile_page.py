import os

from flask import g, request, jsonify
from flask_restful import Resource
from sqlalchemy import desc

try:
    from ...auth.token import token_required
    from ...helper.error_message import moov_errors
    from ...models import User, Notification
    from ...schema import user_schema, notification_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import User, Notification
    from moov_backend.api.schema import user_schema, notification_schema


class BasicInfoResource(Resource):
    
    @token_required
    def get(self):
        _user_id = g.current_user.id

        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        _notifications = Notification.query.filter(Notification.recipient_id==_user.id).order_by(desc(Notification.created_at)).limit(20).all()
        _notifications_data = []
        if _notifications:
            for _notification in _notifications:
                _notification_to_append, _ = notification_schema.dump(_notification)
                _notification_to_append["icon"] = ""
                if _notification.transaction_icon_id:
                    _notification_to_append["icon"] = str(_notification.notification_icon.icon)
                _notifications_data.append(_notification_to_append)

        _user_type = (_user.user_type.title).lower()
        if _user_type == "admin":
            return moov_errors('Unauthorized access', 401)

        _user_data, _ = user_schema.dump(_user)
        _user_data['wallet_amount'] = _user.wallet_user[0].wallet_amount
        _user_data["school"] = str(_user.school_information.name)
        _user_data["user_type"] = _user_type
        _user_data.pop('password', None)
        _user_data.pop('user_id', None)

        return jsonify({"status": "success",
                        "data": {
                            "message": "Basic information successfully retrieved",
                            "user": _user_data,
                            "notifications": _notifications_data
                        }
                    })
