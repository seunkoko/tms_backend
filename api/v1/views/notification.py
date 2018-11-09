from flask import g, request, jsonify, json, current_app, url_for, Response
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...helper.error_message import moov_errors
    from ...models import User, Notification, Icon
    from ...schema import notification_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.helper.error_message import moov_errors
    from moov_backend.api.models import User, Notification, Icon
    from moov_backend.api.schema import notification_schema


class NotificationResource(Resource):
    
    @token_required
    def get(self):
        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        _page = request.args.get('page')
        _limit = request.args.get('limit')
        page = int(_page or current_app.config['DEFAULT_PAGE'])
        limit = int(_limit or current_app.config['PAGE_LIMIT'])

        _notifications = Notification.query.filter(Notification.recipient_id==_user_id).order_by(
                            Notification.created_at.desc()
                        )
        notification_count = len(_notifications.all())
        _notifications = _notifications.paginate(
            page=page, per_page=limit, error_out=False)

        notifications = []
        for _notification in _notifications.items:
            _data, _ = notification_schema.dump(_notification)
            notifications.append(_data)

        previous_url = None
        next_url = None

        if _notifications.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _notifications.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return {
            'status': 'success',
            'data': { 
                        'message': 'Notifications successfully retrieved',
                        'all_count': notification_count,
                        'current_count': len(notifications),
                        'notifications': notifications,
                        'next_url': next_url,
                        'previous_url': previous_url,
                        'current_page': _notifications.page,
                        'all_pages': _notifications.pages
                    }
        }, 200
