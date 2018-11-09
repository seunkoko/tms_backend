import os
import datetime
from datetime import timedelta
from os.path import join, dirname
from dotenv import load_dotenv

from sqlalchemy import or_, and_
from flask import g, request, jsonify
from flask_restful import Resource
from flask_jwt import jwt

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data, validate_empty_string
    from ...helper.common_helper import is_empty_request_fields, is_user_type_authorized
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.user_helper import get_authentication_type
    from ...helper.school_helper import get_school
    from ...models import (
        User, UserType, Wallet, Transaction, Notification, 
        FreeRide, Icon, DriverInfo, AdmissionType, ForgotPassword
    )
    from ...schema import user_schema, user_login_schema, driver_info_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.common_helper import is_empty_request_fields
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.user_helper import get_authentication_type
    from moov_backend.api.helper.school_helper import get_school
    from moov_backend.api.models import (
        User, UserType, Wallet, Transaction, Notification, 
        FreeRide, Icon, DriverInfo, AdmissionType, ForgotPassword
    )
    from moov_backend.api.schema import user_schema, user_login_schema, driver_info_schema


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class UserResource(Resource):
    
    @token_required
    def get(self):
        _data = {}
        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors('User does not exist', 404)

        user_type = _user.user_type.title
        if user_type == "super_admin" or \
           user_type == "admin" or \
           user_type == "school" or \
           user_type == "car_owner" or \
           user_type == "moov":
            return moov_errors("Unauthorized access", 401)

        # handle driver users
        if user_type == "driver":
            driver_info = DriverInfo.query.filter(DriverInfo.driver_id==_user_id).first()
            driver_info_data, _ = driver_info_schema.dump(driver_info)
            driver_info_data["driver_location"] = [driver_info_data["location_latitude"], driver_info_data["location_longitude"]]
            driver_info_data["driver_destination"] = [driver_info_data["destination_latitude"], driver_info_data["destination_longitude"]]
            for key in ['bank_name', 'account_number', 'driver_id', 'admission_type_id', 'location_latitude', \
            'location_longitude', 'destination_latitude', 'destination_longitude']:
                driver_info_data.pop(key, None)
            _data, _ = user_schema.dump(_user)
            _data["driver_info"] = driver_info_data
        else:
            _data, _ = user_schema.dump(_user)

        _data['wallet_amount'] = _user.wallet_user[0].wallet_amount
        _data["school"] = str(_user.school_information.name)
        _data["user_type"] = user_type
        _data.pop('password', None)
        _data.pop('user_id', None)
        return {
            'status': 'success',
            'data': { 
                        'message': 'User has been successfully retrieved',
                        'user': _data
                    }
        }, 200

    @token_required
    @validate_request()
    def put(self):
        json_input = request.get_json()

        keys = [
                    'user_type',
                    'email',
                    'firstname', 
                    'lastname', 
                    'image_url', 
                    'mobile_number',
                    'authorization_code',
                    'password'
                ]
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        _user_id = g.current_user.id
        _user = User.query.get(_user_id)
        if not _user:
            return moov_errors("User does not exist", 404)

        if is_empty_request_fields(json_input):
            return moov_errors("Empty strings are not allowed, exception for image urls", 400)

        unauthorized_list = ["super_admin", "admin", "school", "car_owner", "moov"]
        if is_user_type_authorized(unauthorized_list, _user.user_type.title):
            return moov_errors("Unauthorized access", 401)

        for key in json_input.keys():
            if key == 'user_type':
                return moov_errors('Unauthorized access, you cannot update user types', 401)
                
            if key == 'email':
                return moov_errors('Unauthorized access, you cannot update emails', 401)

            if key == 'password':
                if _user.check_password(json_input['password']):
                    return moov_errors('Unauthorized, you cannot update with the same password', 401)

            if key == 'authorization_code':
                _user.__setitem__("authorization_code_status", True)

            _user.__setitem__(key, json_input[key])

        _user.save()
        _data, _ = user_schema.dump(_user)
        _data["user_type"] = _user.user_type.title
        _data["school"] = str(_user.school_information.name)
        _data.pop('password', None)
        _data.pop('user_id', None)
        return {
            'status': 'success',
            'data': {
                'user': _data,
                'message': 'User information updated succesfully',
            }
        }, 200
    
    @token_required
    @validate_request()
    def delete(self):
        json_input = request.get_json()
        if "email" not in json_input:
            return moov_errors("Please provide email of user to delete", 400)

        keys = ['email']
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        _current_user_id = g.current_user.id
        _current_user = User.query.get(_current_user_id)
        _user_to_delete = User.query.filter(User.email==json_input["email"]).first()
        if not _current_user or not _user_to_delete:
            return moov_errors("User does not exist", 404)

        if _user_to_delete.user_type.title ==  "super_admin" or \
           _user_to_delete.user_type.title == "admin" or \
           _user_to_delete.user_type.title == "school" or \
           _user_to_delete.user_type.title == "car_owner" or \
           _user_to_delete.user_type.title == "moov":
            return moov_errors("Unauthorized, you cannot create a/an {0}".format(_user_to_delete.user_type.title), 401)

        if str(_current_user.email) != str(_user_to_delete.email) and \
        str(_current_user.user_type.title) not in ["admin", "super_admin"]:
            return moov_errors("Unauthorized access. You cannot delete this user", 401)

        _user_to_delete.delete()
        return {
            'status': 'success',
            'data': None
        }, 200


class UserSignupResource(Resource):
    
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = [
                    'user_type', 
                    'firstname', 
                    'lastname', 
                    'email', 
                    'image_url', 
                    'mobile_number',
                    'password',
                    'authentication_type',
                    'school'
                ]

        _user = {}
        if validate_input_data(json_input, keys, _user):
            return validate_input_data(json_input, keys, _user)

        data, errors = user_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        if validate_empty_string(json_input['password']):
            return moov_errors('Password cannot be empty', 400)

        # verify email
        if User.is_user_data_taken(json_input['email']):
            return moov_errors('User already exists', 400)

        # verify empty request fields
        if is_empty_request_fields(json_input):
            return moov_errors("Empty strings are not allowed, exception for image urls", 400)

        # verify school
        school = get_school(str(json_input['school']).lower())
        if not school:
            return moov_errors('{0} (school) does not exist'.format(str(json_input['school'])), 400)

        user_type = UserType.query.filter(UserType.title==data['user_type'].lower()).first()
        user_type_id = user_type.id if user_type else None

        unauthorized_list = ["super_admin", "admin", "school", "car_owner", "moov"]
        if is_user_type_authorized(unauthorized_list, data['user_type'].lower()):
            return moov_errors("Unauthorized, you cannot create a/an {0}".format(data['user_type']), 401)
        if not user_type_id:
            return moov_errors("User type can only be student or driver", 400)

        moov_email = os.environ.get("MOOV_EMAIL")
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors(moov_email)

        _transaction_icon = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"
        transaction_icon = Icon.query.filter(Icon.operation_type=="moov_operation").first()
        if transaction_icon:
            _transaction_icon_id = transaction_icon.id

        authentication_type = "email" if "authentication_type" not in json_input else json_input['authentication_type']
        authentication_type = get_authentication_type(authentication_type)
            
        new_user = User(
            password=data['password'],
            school_id=school.id,
            user_type_id=user_type_id,
            authentication_type=authentication_type,
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            image_url=data['image_url'] if json_input.get('image_url') else \
                        "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png",
            mobile_number=data['mobile_number'] if json_input.get('mobile_number') else ""
        )
        new_user.save()

        user_wallet = Wallet(
            wallet_amount= 0.00,
            user_id = new_user.id,
            description = "{0} {1}'s Wallet".format((new_user.lastname).title(), (new_user.firstname).title())
        )
        user_wallet.save()

        user_notification = Notification(
            message="Welcome to MOOV app.",
            recipient_id=new_user.id,
            sender_id=moov_user.id,
            transaction_icon_id=_transaction_icon_id
        )
        user_notification.save()

        token_date = datetime.datetime.utcnow()
        payload = {
                    "id": new_user.id,
                    "stamp": str(token_date)
                }
        _token = jwt.encode(payload, os.getenv("TOKEN_KEY"), algorithm='HS256')

        message = "The profile with email {0} has been created succesfully".format(new_user.email)

        _data, _ = user_schema.dump(new_user)
        _data["wallet_amount"] = user_wallet.wallet_amount
        _data["school"] = str(new_user.school_information.name)
        _data["user_type"] = new_user.user_type.title
        _data.pop('password', None)
        _data.pop('user_id', None)

        if user_type.title.lower() == "driver":
            new_driver_info = DriverInfo(
                driver_id=new_user.id
            )
            new_driver_info.save()
            user_notification = Notification(
                message="Thank you for registering to be a MOOV driver. \
                            Your request is waiting approval, we will get back to you soon",
                recipient_id=new_user.id,
                sender_id=moov_user.id,
                transaction_icon_id=_transaction_icon_id
            )
            user_notification.save()

        return {
            'status': 'success',
            'data': {
                'user': _data,
                'message': message,
                'token': _token
            }
        }, 201

    
class UserLoginResource(Resource):
        
    @validate_request()
    def post(self):
        set_temporary_password = False
        json_input = request.get_json()

        keys = ['email', 'password']
        if validate_input_data(json_input, keys):
            return validate_input_data(json_input, keys)

        data, errors = user_login_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        _user = User.query.filter(User.email.like(json_input['email'])).first()
        if not _user:
            return moov_errors('User does not exist', 404)

        if _user.reset_password:
            temp_password = ForgotPassword.query.filter(
                ForgotPassword.user_id==_user.id
            ).order_by(
                ForgotPassword.created_at.desc()
            ).first()

            # Precautions
            if (not temp_password) or (temp_password and temp_password.temp_password != json_input['password']):
                return moov_errors("Invalid password", 400)
            if temp_password.used:
                return moov_errors("Sorry, this password has been used to reset forgotten password details", 400)
            if not datetime.datetime.utcnow() <= (temp_password.created_at + timedelta(days=1)):
                return moov_errors("Temporary password expired", 400)

            set_temporary_password = True
            temp_password.used = True
            _user.reset_password = False
            temp_password.save()
            _user.save()
        else:
            if not _user.check_password(json_input['password']):
                return moov_errors("Invalid email/password", 401)

        _user_wallet = Wallet.query.filter(Wallet.user_id==_user.id).first()

        token_date = datetime.datetime.utcnow()
        payload = {
                    "id": _user.id,
                    "stamp": str(token_date)
                }
        _token = jwt.encode(payload, os.getenv("TOKEN_KEY"), algorithm='HS256')

        _data, _ = user_schema.dump(_user)
        _data["wallet_amount"] = _user_wallet.wallet_amount if _user_wallet else "Unavailable"
        _data["school"] = str(_user.school_information.name)
        _data["user_type"] = _user.user_type.title
        _data["set_temporary_password"] = set_temporary_password
        _data.pop('password', None)
        _data.pop('user_id', None)
        return jsonify({"status": "success",
                        "data": {
                            "data": _data,
                            "message": "Login successful",
                            "token": str(_token)
                        }
                    })


class UserAuthorizationResource(Resource):
        
    @token_required
    def get(self):
        _current_user_id = g.current_user.id

        _current_user = User.query.get(_current_user_id)
        if not _current_user:
            return moov_errors("User does not exist", 404)

        _data = {}
        _data['user_id'] = _current_user_id
        _data['authorization_code'] = _data['authorization_code'] = _current_user.authorization_code
        _data['authorization_code_status'] = _current_user.authorization_code_status
        _data.pop('password', None)
        _data.pop('user_id', None)

        return jsonify({"status": "success",
                        "data": {
                            "data": _data
                        }
                    })
