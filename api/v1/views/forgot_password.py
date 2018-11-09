import os

from flask import g, request, jsonify, json, Response
from flask_restful import Resource

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_input_data
    from ...generator.password_generator import generate_password
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.notification_helper import save_notification
    from ...models import User, Notification, Icon, ForgotPassword
    from ...schema import forgot_password_schema
    from ...emails.email_forgot_password import send_forgot_password_mail
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_input_data
    from moov_backend.api.generator.password_generator import generate_password
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.models import User, Notification, Icon, ForgotPassword
    from moov_backend.api.schema import forgot_password_schema
    from moov_backend.api.emails.email_forgot_password import send_forgot_password_mail


class ForgotPasswordResource(Resource):
    
    def post(self):
        json_input = request.get_json()

        keys = ['email']
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)
        
        _user = User.query.filter(User.email==json_input['email']).first()
        if not _user:
            return moov_errors('User does not exist', 404)

        if _user.authentication_type.value != None and \
           _user.authentication_type.value != "email_type":
            return moov_errors('You cannot reset password for authentications other than email', 401)

        generated_password = generate_password()
        new_password = ForgotPassword(
            user_id=_user.id,
            temp_password=generated_password,
            used=False
        )
        new_password.save()
        _user.reset_password = True
        _user.save()

        moov_email = os.environ.get("MOOV_EMAIL")
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors(moov_email)

        _transaction_icon_id = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"
        transaction_icon = Icon.query.filter(Icon.operation_type=="moov_operation").first()
        if transaction_icon:
            _transaction_icon_id = transaction_icon.id

        message = "You reset your password"
        save_notification(
            recipient_id=_user.id, 
            sender_id=moov_user.id, 
            message=message, 
            transaction_icon_id=_transaction_icon_id
        )

        send_mail = send_forgot_password_mail(
                        email=_user.email,
                        firstname=_user.firstname.title(),
                        password=generated_password
                    )
        
        if send_mail["status"]:
            return {
                'status': 'success',
                'data': { 'message': "Password reset successful, check email for temporary password which is valid for 24 hours" }
            }, 200

        return {
                'status': 'fail',
                'data': { 'message': "Email was not sent successfully" }
            }, 503
