import os
from datetime import datetime

from flask import g, request, current_app, url_for, jsonify
from flask_restful import Resource
from sqlalchemy import or_

try:
    from ...auth.token import token_required
    from ...auth.validation import validate_request, validate_input_data
    from ...generator.free_ride_token_generator import generate_free_ride_token
    from ...helper.error_message import moov_errors, not_found_errors
    from ...helper.user_helper import get_user
    from ...helper.school_helper import get_school
    from ...helper.wallet_helper import get_wallet
    from ...helper.percentage_price_helper import get_percentage_price
    from ...helper.notification_helper import save_notification
    from ...helper.free_ride_helper import get_free_ride_token, save_free_ride_token
    from ...helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity, load_wallet_operation,
        ride_fare_operation, transfer_operation, save_transaction, verify_paystack_payment
    )
    from ...models import (
        User, Transaction, Wallet, Icon, FreeRide, OperationType, TransactionType,
        FreeRideType
    )
    from ...schema import transaction_schema
except ImportError:
    from moov_backend.api.auth.token import token_required
    from moov_backend.api.auth.validation import validate_request, validate_input_data
    from moov_backend.api.helper.error_message import moov_errors, not_found_errors
    from moov_backend.api.helper.user_helper import get_user
    from moov_backend.api.helper.school_helper import get_school
    from moov_backend.api.helper.wallet_helper import get_wallet
    from moov_backend.api.helper.percentage_price_helper import get_percentage_price
    from moov_backend.api.helper.notification_helper import save_notification
    from moov_backend.api.helper.free_ride_helper import get_free_ride_token, save_free_ride_token
    from moov_backend.api.helper.transactions_helper import (
        paystack_deduction_amount, check_transaction_validity, load_wallet_operation,
        ride_fare_operation, transfer_operation, save_transaction, verify_paystack_payment
    )
    from moov_backend.api.models import (
        User, Transaction, Wallet, Icon, FreeRide, OperationType, TransactionType,
        FreeRideType
    )
    from moov_backend.api.schema import transaction_schema


class TransactionResource(Resource):
    
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

        _transactions = Transaction.query.filter(or_(
                            Transaction.sender_id==_user_id,
                            Transaction.receiver_id==_user_id
                        )).order_by(
                            Transaction.transaction_date.desc()
                        )
        transaction_count = len(_transactions.all())
        _transactions = _transactions.paginate(
            page=page, per_page=limit, error_out=False)

        transactions = []
        for _transaction in _transactions.items:
            _data, _ = transaction_schema.dump(_transaction)
            transactions.append(_data)

        previous_url = None
        next_url = None

        if _transactions.has_next:
            next_url = url_for(request.endpoint,
                               limit=limit,
                               page=page+1,
                               _external=True)
        if _transactions.has_prev:
            previous_url = url_for(request.endpoint,
                                   limit=limit,
                                   page=page-1,
                                   _external=True)

        return {
            'status': 'success',
            'data': { 
                        'message': 'Transactions successfully retrieved',
                        'all_count': transaction_count,
                        'current_count': len(transactions),
                        'transactions': transactions,
                        'next_url': next_url,
                        'previous_url': previous_url,
                        'current_page': _transactions.page,
                        'all_pages': _transactions.pages
                    }
        }, 200
    
    @token_required
    @validate_request()
    def post(self):
        json_input = request.get_json()
        
        keys = [
            'type_of_operation', 
            'cost_of_transaction', 
            'receiver_email', 
            'school_name',
            'verification_code', 
            'car_owner_email', 
            'free_token'
        ]

        _transaction = {}
        if validate_input_data(json_input, keys, _transaction):
            return validate_input_data(json_input, keys, _transaction)

        data, errors = transaction_schema.load(json_input)
        if errors:
            return moov_errors(errors, 422)

        # establishing the _current_user is valid and not an admin
        _current_user_id = g.current_user.id

        _current_user = User.query.get(_current_user_id)
        if not _current_user:
            return moov_errors('User does not exist', 404)

        _current_user_type = (_current_user.user_type.title).lower()
        if _current_user_type == "admin":
            return moov_errors('Unauthorized access', 401)

        _transaction_icon = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"

        moov_email = os.environ.get("MOOV_EMAIL")
        moov_user = User.query.filter(User.email==moov_email).first()
        if not moov_user:
            return not_found_errors(moov_email)

        # case load_wallet
        if str(json_input['type_of_operation']).lower() == 'load_wallet':
            if 'verification_code' not in json_input:
                return moov_errors('Transaction denied. Verification is compulsory to load wallet', 400)

            # third-party api to verify paystack payment
            paystack_verified = verify_paystack_payment(user=_current_user, verification_code=str(json_input['verification_code']))
            if not paystack_verified:
                return moov_errors("Unauthorized transaction. Paystack payment was not verified", 401)

            cost_of_transaction = json_input["cost_of_transaction"]

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)
            
            _data, _ = load_wallet_operation(cost_of_transaction, _current_user, _current_user_id, moov_user)
            _data["free_ride_token"] = ""
            return {
                    'status': 'success',
                    'data': {
                        'transaction': _data,
                        'message': "Transaction succesful"
                    }
                }, 201

        # case ride_fare and transfer
        if ('receiver_email') in json_input:
            cost_of_transaction = json_input["cost_of_transaction"]
            _receiver_email = json_input['receiver_email']
            _sender_id = _current_user_id
            _sender = _current_user
            _receiver = User.query.filter(User.email==_receiver_email).first()

            if not _receiver:
                return moov_errors("User does not exist", 404)
            if str(_receiver.user_type.title) == "admin":
                return moov_errors("Unauthorized access", 401) 
            

            _receiver_wallet = Wallet.query.filter(Wallet.user_id==_receiver.id).first()
            _sender_wallet = Wallet.query.filter(Wallet.user_id==_sender_id).first()

            message = "Cost of transaction cannot be a negative value"
            if check_transaction_validity(cost_of_transaction, message):
                return check_transaction_validity(cost_of_transaction, message)

            receiver_amount_before_transaction = _receiver_wallet.wallet_amount
            sender_amount_before_transaction = _sender_wallet.wallet_amount
            sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction

            message = "Sorry, you cannot transfer more than your wallet amount"
            if check_transaction_validity(sender_amount_after_transaction, message):
                return check_transaction_validity(sender_amount_after_transaction, message)

            # case transfer
            if str(json_input['type_of_operation']).lower() == 'transfer':
                if str(_receiver.id) == str(_sender_id):
                    return moov_errors("Unauthorized. A user cannot transfer to him/herself", 401)
                
                transfer_percentage_price = (get_percentage_price(title="default_transfer")).price
                transfer_charge = transfer_percentage_price * cost_of_transaction
                sender_amount_after_transaction = _sender_wallet.wallet_amount - cost_of_transaction - transfer_charge

                if check_transaction_validity(sender_amount_after_transaction, message):
                  return check_transaction_validity(sender_amount_after_transaction, message)

                moov_wallet = get_wallet(email=moov_email)
                if not moov_wallet:
                    return not_found_errors(moov_email)

                _data, _ = transfer_operation(
                                _sender, 
                                _receiver, 
                                _sender_wallet, 
                                _receiver_wallet, 
                                moov_wallet, 
                                cost_of_transaction, 
                                transfer_charge, 
                                sender_amount_before_transaction, 
                                receiver_amount_before_transaction, 
                                sender_amount_after_transaction, 
                                moov_user
                            )
                _data["free_ride_token"] = ""
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                }, 201
                 
            # case ride_fare
            if str(json_input['type_of_operation']).lower() == 'ride_fare':
                _data = {}
                free_ride_icon = Icon.query.filter(Icon.operation_type=="free_ride_operation").first()
                if free_ride_icon:
                    free_ride_icon_id = free_ride_icon.id

                if ("free_token" in json_input) and (json_input["free_token"] is not None):
                    token_valid = FreeRide.query.filter(
                                    FreeRide.token==json_input["free_token"]
                                ).first()

                    # error handlers
                    if not token_valid:
                        return moov_errors("{0} is not a valid token".format(json_input["free_token"]), 404)
                    if not token_valid.token_status:
                        return moov_errors("{0} has been used".format(json_input["free_token"]), 400)

                    # set the token to false i.e. make it inactive
                    token_valid.token_status = False
                    token_valid.save()

                    # save notification
                    transaction_icon = Icon.query.filter(Icon.operation_type=="ride_operation").first()
                    if transaction_icon:
                        _transaction_icon_id = transaction_icon.id
                    notification_user_sender_message = "Your transaction costs N0, your free token {0} was used".format(json_input["free_token"])
                    notification_user_receiver_message = "Your transaction with {0} was a free ride".format(str(_sender.firstname).title())
                    save_notification(
                            recipient_id=_sender.id, 
                            sender_id=moov_user.id, 
                            message=notification_user_sender_message, 
                            transaction_icon_id=_transaction_icon_id
                        )
                    save_notification(
                            recipient_id=_receiver.id, 
                            sender_id=moov_user.id, 
                            message=notification_user_receiver_message, 
                            transaction_icon_id=_transaction_icon_id
                        )

                    # save transaction
                    transaction_detail = "Free ride token {0} was used for this ride transaction".format(json_input["free_token"])
                    _data, _ = save_transaction(
                                    transaction_detail=transaction_detail, 
                                    type_of_operation=OperationType.ride_type, 
                                    type_of_transaction=TransactionType.both_types, 
                                    cost_of_transaction=0, 
                                    _receiver=_receiver, 
                                    _sender=_sender, 
                                    _receiver_wallet=_receiver_wallet, 
                                    _sender_wallet=_sender_wallet, 
                                    receiver_amount_before_transaction=receiver_amount_before_transaction, 
                                    sender_amount_before_transaction=sender_amount_before_transaction, 
                                    receiver_amount_after_transaction=(receiver_amount_before_transaction + 0), 
                                    sender_amount_after_transaction=(sender_amount_before_transaction+0)
                                )
                    _data["free_ride_token"] = ""
                else:
                    # increments the number of rides taken by a user
                    _sender.number_of_rides += 1

                    if "school_name" not in json_input:
                        return moov_errors("school_name field is compulsory for ride fare", 400)
                    
                    school = get_school((str(json_input["school_name"])).lower())
                    if not school:
                        return not_found_errors(json_input["school_name"])

                    school_email = school.email
                    car_owner_email = os.environ.get("CAR_OWNER_EMAIL") if ("car_owner" not in json_input) else json_input["car_owner"]
                    car_owner = get_user(car_owner_email)
                    if not car_owner:
                        return not_found_errors(car_owner_email)

                    moov_wallet = get_wallet(email=moov_email)
                    school_wallet = get_wallet(email=school_email)
                    car_owner_wallet = get_wallet(email=car_owner_email)

                    if not moov_wallet:
                        return not_found_errors(moov_email)
                    if not school_wallet:
                        return not_found_errors(school_email)
                    if not car_owner_wallet:
                        return not_found_errors(car_owner_email)

                    # change here in case percentage cut is dynamic for drivers of different schools
                    driver_percentage_price_info = get_percentage_price(title="default_driver")
                    if not driver_percentage_price_info:
                        # ignore repitition from above for now
                        driver_percentage_price_info = get_percentage_price(title="default_driver")  
                    school_percentage_price_info = get_percentage_price(title=school.email)
                    if not school_percentage_price_info:
                        school_percentage_price_info = get_percentage_price(title="default_school")          
                    car_owner_percentage_price_info = get_percentage_price(title=car_owner.email)
                    if not car_owner_percentage_price_info:
                        car_owner_percentage_price_info = get_percentage_price(title="default_car_owner")  

                    if not car_owner_percentage_price_info or not school_percentage_price_info:
                        return moov_errors("Percentage price was not set for the school or car_owner ({0}, {1})".format(school.name, car_owner_email), 400)

                    # free ride generation
                    free_ride_token = get_free_ride_token(_sender)
                    if free_ride_token:
                        free_ride_description = "Token generated for {0} on the {1} for ride number {2}".format(
                                                    _sender.email, str(datetime.now()), _sender.number_of_rides
                                                )
                        save_free_ride_token(
                            free_ride_type=FreeRideType.ride_type,
                            token=free_ride_token, 
                            description=free_ride_description, 
                            user_id=_sender_id
                        )

                        free_ride_notification_message = "You have earned a free ride token '{0}'".format(free_ride_token)
                        save_notification(
                            recipient_id=_sender_id, 
                            sender_id=moov_user.id, 
                            message=free_ride_notification_message, 
                            transaction_icon_id=free_ride_icon_id
                        )
                    
                    _data, _ = ride_fare_operation(
                                    _sender, 
                                    _receiver, 
                                    driver_percentage_price_info, 
                                    school_percentage_price_info, 
                                    car_owner_percentage_price_info, 
                                    cost_of_transaction, 
                                    receiver_amount_before_transaction, 
                                    sender_amount_before_transaction, 
                                    sender_amount_after_transaction, 
                                    moov_wallet, 
                                    school_wallet, 
                                    car_owner_wallet, 
                                    _sender_wallet, 
                                    _receiver_wallet, 
                                    moov_user
                                )
                    _data["free_ride_token"] = free_ride_token
    
                return {
                        'status': 'success',
                        'data': {
                            'transaction': _data,
                            'message': "Transaction succesful"
                        }
                    }, 201

        # cases that don't meet the required condition
        return moov_errors("Transaction denied", 400) 

class AllTransactionsResource(Resource):
    
    def get(self):
        pass
