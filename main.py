import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask_mail import Mail
from flask import Flask, jsonify
from flask_sslify import SSLify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api, abort


try:
    from config import app_configuration
    from api.v1.views.route import RouteResource
    from api.v1.views.user import (
        UserResource, UserSignupResource, UserLoginResource, 
        UserAuthorizationResource
    )
    from api.v1.views.driver import (
        DriverResource, DriverConfirmRideResouce
    )
    from api.v1.views.profile_page import BasicInfoResource
    from api.v1.views.transaction import (
        TransactionResource, AllTransactionsResource
    )
    from api.v1.views.free_ride import FreeRideResource
    from api.v1.views.notification import NotificationResource
    from api.v1.views.forgot_password import ForgotPasswordResource
    from api.v1.views.school import SchoolResource
except ImportError:
    from moov_backend.config import app_configuration
    from moov_backend.api.v1.views.route import RouteResource
    from moov_backend.api.v1.views.user import (
        UserResource, UserSignupResource, UserLoginResource, 
        UserAuthorizationResource
    )
    from moov_backend.api.v1.views.driver import (
        DriverResource, DriverConfirmRideResouce
    )
    from moov_backend.api.v1.views.profile_page import BasicInfoResource
    from moov_backend.api.v1.views.transaction import (
        TransactionResource, AllTransactionsResource
    )
    from moov_backend.api.v1.views.free_ride import FreeRideResource
    from moov_backend.api.v1.views.notification import NotificationResource
    from moov_backend.api.v1.views.forgot_password import ForgotPasswordResource
    from moov_backend.api.v1.views.school import SchoolResource
    

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def create_flask_app(environment):
    app = Flask(__name__, instance_relative_config=True, static_folder=None, template_folder='./api/emails/templates')
    app.config.from_object(app_configuration[environment])
    app.config['BUNDLE_ERRORS'] = True

    try:
        from api import models
    except ImportError:
        from moov_backend.api import models

    # to allow cross origin resource sharing
    CORS(app)

    # initialize SQLAlchemy
    models.db.init_app(app)

    # initilize migration commands
    Migrate(app, models.db)

    # initilize api resources
    api = Api(app)

    environment = os.getenv("FLASK_CONFIG")

    # to redirect all incoming requests to https
    if environment.lower() == "production":
        sslify = SSLify(app, subdomains=True, permanent=True)

    # Landing page
    @app.route('/')
    def index():
        return "Welcome to the MOOV Api"

    ##
    ## Actually setup the Api resource routing here
    ##
    api.add_resource(RouteResource, '/api/v1/route', '/api/v1/route/', endpoint='single_route')

    # User routes
    api.add_resource(UserResource, '/api/v1/user', '/api/v1/user/', endpoint='user_endpoint')
    api.add_resource(UserAuthorizationResource, '/api/v1/user_authorization', '/api/v1/user_authorization/',
                        endpoint='user_authorization_endpoint')

    # Driver routes
    api.add_resource(DriverResource, '/api/v1/driver', '/api/v1/driver/', endpoint='single_driver')
    api.add_resource(DriverConfirmRideResouce, '/api/v1/driver_confirm_ride', '/api/v1/driver_confirm_ride/', endpoint='driver_confirm_endpoint')

    # Authentication routes
    api.add_resource(UserSignupResource, '/api/v1/signup', '/api/v1/signup/', endpoint='singup_user')
    api.add_resource(UserLoginResource, '/api/v1/login', '/api/v1/login/', endpoint='login_endpoint')

    # Transaction routes
    api.add_resource(TransactionResource, '/api/v1/transaction', '/api/v1/transaction/', endpoint='single_transaction')
    api.add_resource(AllTransactionsResource, '/api/v1/all_transactions', '/api/v1/all_transactions/', endpoint='all_transactions')

    # Profile Page routes
    api.add_resource(BasicInfoResource, '/api/v1/basic_info', '/api/v1/basic_info/', endpoint='user_basic_info')
    
    # Free Ride routes
    api.add_resource(FreeRideResource, '/api/v1/free_ride', '/api/v1/free_ride/', endpoint='free_ride_endpoint')

    # Notification routes
    api.add_resource(NotificationResource, '/api/v1/notification', '/api/v1/notification/', endpoint='single_notification')

    # Forgot Password routes
    api.add_resource(ForgotPasswordResource, '/api/v1/forgot_password', '/api/v1/forgot_password/', endpoint='forgot_password')

    # School routes
    api.add_resource(SchoolResource, '/api/v1/all_schools', '/api/v1/all_schools/', endpoint='all_schools')


    # handle default 404 exceptions with a custom response
    @app.errorhandler(404)
    def resource_not_found(exception):
        response = jsonify(dict(status='fail', data={
                    'error':'Not found', 'message':'The requested URL was'
                    ' not found on the server. If you entered the URL '
                    'manually please check and try again'
                }))
        response.status_code = 404
        return response

    # both error handlers below handle default 500 exceptions with a custom response
    @app.errorhandler(500)
    def internal_server_error(error):
        response = jsonify(dict(status=error,error='Internal Server Error',
                    message='The server encountered an internal error and was' 
                    ' unable to complete your request.  Either the server is'
                    ' overloaded or there is an error in the application'))
        response.status_code = 500
        return response

    if environment.lower() == "production":
        # handles 500 exception on production
        @app.errorhandler(Exception)
        def unhandled_exception(error):
            response = jsonify(dict(
                status='error',
                data={
                    'error': 'Unhandle Error',
                    'message': 'The server encountered an internal error and was unable to complete your request.'
                }
            ))
            response.status_code = 500
            app.logger.error(repr(error))
            return response

    return app

# enable flask commands
app = create_flask_app(os.getenv("FLASK_CONFIG"))
