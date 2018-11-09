from marshmallow import Schema, fields, validate, pre_load, post_dump, validates_schema, ValidationError
from datetime import datetime as dt


def check_unknown_fields(data, original_data, fields):
    unknown = set(original_data) - set(fields)
    if unknown:
        raise ValidationError('{} is not a valid field'.format(), unknown)


class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    user_type = fields.Str(
        required=True,
        errors={
            'required': 'Please provide the user type. It can either be a driver or student',
            'type': 'Invalid type'
        })
    password = fields.Str(
        required=True,
        errors={
            'required': 'Please provide your password.',
            'type': 'Invalid type'
        })
    firstname = fields.Str(
        required=True,
        errors={
            'required': 'Please provide your firstname.',
            'type': 'Invalid type'
        })
    lastname = fields.Str(
        required=True,
        errors={
            'required': 'Please provide your lastname.',
            'type': 'Invalid type'
        })
    email = fields.Str(
        required=True,
        errors={
            'required': 'Please provide a valid email.',
            'type': 'Invalid type'
        })
    mobile_number = fields.Str(
        required=True,
        errors={
            'required': 'Please provide a valid mobile number.',
            'type': 'Invalid type'
        })
    user_id = fields.Str(errors={'type': 'Invalid type'})
    authentication_type = fields.Str(errors={'type': 'Invalid type'})
    image_url = fields.Str(errors={'type': 'Invalid type'})
    authorization_code = fields.Str(errors={'type': 'Invalid type'})
    authorization_code_status = fields.Bool(errors={'type': 'Invalid type'})
    ratings = fields.Integer(errors={'type': 'Invalid type'})
    current_ride = fields.Dict(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)
    # addition information not in the db
    school = fields.Str(
                required=True,
                errors={
                    'required': 'Please provide a valid school.',
                    'type': 'Invalid type'
            })

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


class UserLoginSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Str(
        required=True,
        errors={
            'required': 'Invalid email/password',
            'type': 'Invalid type'
        })
    password = fields.Str(
        required=True,
        errors={
            'required': 'Invalid email/password.',
            'type': 'Invalid type'
        })

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


class ForgotPassword(Schema):
    id = fields.Str(dump_only=True)
    user_id = fields.Str(
        required=True,
        errors={
            'required': 'User id is compulsory',
            'type': 'Invalid type'
        })
    temp_password = fields.Str(
        required=True,
        errors={
            'required': 'Temporary password is required',
            'type': 'Invalid type'
        })
    used = fields.Bool(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


class TransactionSchema(Schema):
    id = fields.Str(dump_only=True)
    type_of_operation = fields.Str(
            required=True,
            errors={
                'required': 'Please provide a valid type of transaction (transfer, load_wallet or ride_fare).',
                'type': 'Invalid type'
            })
    cost_of_transaction = fields.Float(
            required=True,
            errors={
                'required': 'Please provide the cost of transaction.',
                'type': 'Invalid type'
            })
    transaction_detail = fields.Str(errors={'type': 'Invalid type'})
    type_of_transaction = fields.Str(errors={'type': 'Invalid type'})
    receiver_amount_before_transaction = fields.Float(errors={'type': 'Invalid type'})
    receiver_amount_after_transaction = fields.Float(errors={'type': 'Invalid type'})
    sender_amount_before_transaction = fields.Float(errors={'type': 'Invalid type'})
    sender_amount_after_transaction = fields.Float(errors={'type': 'Invalid type'})
    paystack_deduction = fields.Float(errors={'type': 'Invalid type'})
    receiver_id = fields.Str(errors={'type': 'Invalid type'})
    sender_id = fields.Str(errors={'type': 'Invalid type'})
    receiver_wallet_id = fields.Str(errors={'type': 'Invalid type'})
    sender_wallet_id = fields.Str(errors={'type': 'Invalid type'})
    transaction_date = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


class NotificationSchema(Schema):
    id = fields.Str(dump_only=True)
    message = fields.Str(errors={'type': 'Invalid type'})
    transaction_icon = fields.Str(errors={'type': 'Invalid type'})
    recipient_id = fields.Str(errors={'type': 'Invalid type'})
    sender_id = fields.Str(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


class DriverInfoSchema(Schema):
    id = fields.Str(dump_only=True)
    location_latitude = fields.Float(errors={'type': 'Invalid type'})
    location_longitude = fields.Float(errors={'type': 'Invalid type'})
    destination_latitude = fields.Float(errors={'type': 'Invalid type'})
    destination_longitude = fields.Float(errors={'type': 'Invalid type'})
    car_slots = fields.Integer(errors={'type': 'Invalid type'})
    available_car_slots = fields.Integer(errors={'type': 'Invalid type'})
    status = fields.Boolean(errors={'type': 'Invalid type'})
    on_trip_with = fields.Dict(errors={'type': 'Invalid type'})
    car_model = fields.Str(errors={'type': 'Invalid type'})
    left_image = fields.Str(errors={'type': 'Invalid type'})
    right_image = fields.Str(errors={'type': 'Invalid type'})
    front_image = fields.Str(errors={'type': 'Invalid type'})
    back_image = fields.Str(errors={'type': 'Invalid type'})
    plate_number = fields.Str(errors={'type': 'Invalid type'})
    admin_confirmed = fields.Boolean(errors={'type': 'Invalid type'})
    bank_name = fields.Str(errors={'type': 'Invalid type'})
    account_number = fields.Str(errors={'type': 'Invalid type'})
    driver_id = fields.Str(
            required=True,
            errors={
                'required': 'Please provide a valid free ride type.',
                'type': 'Invalid type'
            })
    admission_type_id = fields.Str(errors={'type': 'Invalid type'})
    number_of_rides = fields.Integer(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


class FreeRideSchema(Schema):
    id = fields.Str(dump_only=True)
    free_ride_type = fields.Str(
            required=True,
            errors={
                'required': 'Please provide a valid free ride type.',
                'type': 'Invalid type'
            })
    token = fields.Str(
            required=True,
            errors={
                'required': 'Please provide a token.',
                'type': 'Invalid type'
            })
    token_status = fields.Boolean(errors={'type': 'Invalid type'})
    description = fields.Str(errors={'type': 'Invalid type'})
    user_id = fields.Str(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

    @validates_schema(pass_original=True)
    def unknown_fields(self, data, original_data):
        check_unknown_fields(data, original_data, self.fields)


class SchoolInfoSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(
                required=True,
                errors={
                    'required': 'Please provide the school name.',
                    'type': 'Invalid type'
            })
    alias = fields.Str(errors={'type': 'Invalid type'})
    password = fields.Str(
                    required=True,
                    errors={
                        'required': 'Please provide the password for this account.',
                        'type': 'Invalid type'
                })
    admin_status = fields.Bool(errors={'type': 'Invalid type'})
    email = fields.Str(
                    required=True,
                    errors={
                        'required': 'Please provide a valid email for this account.',
                        'type': 'Invalid type'
                })
    user_type = fields.Str(
                        required=True,
                        errors={
                            'required': 'Please provide the user type. It can either be a driver or student',
                            'type': 'Invalid type'
                    })
    reset_password = fields.Bool(errors={'type': 'Invalid type'})
    bank_name = fields.Str(errors={'type': 'Invalid type'})
    account_number = fields.Str(errors={'type': 'Invalid type'})
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)


user_schema = UserSchema()
user_login_schema = UserLoginSchema()
forgot_password_schema = ForgotPassword()
transaction_schema = TransactionSchema()
notification_schema = NotificationSchema()
free_ride_schema = FreeRideSchema()
driver_info_schema = DriverInfoSchema()
school_info_schema= SchoolInfoSchema()
