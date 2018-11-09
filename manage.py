import os
import logging

from flask_script import Manager, Server, prompt_bool, Shell
from flask_migrate import MigrateCommand
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError

from main import create_flask_app

try:
    from api.helper.default_data import (
        create_user, create_default_user_types, create_percentage_price,
        create_wallet, create_admission_type, create_icon, create_school
    )
    from api.models import db, UserType, User, Wallet
except ImportError:
    from moov_backend.api.helper.default_data import (
        create_user, create_default_user_types, create_percentage_price,
        create_wallet, create_admission_type, create_icon, create_school
    )
    from moov_backend.api.models import db, UserType, User, Wallet


environment = os.getenv("FLASK_CONFIG")
app = create_flask_app(environment)

app.secret_key = os.getenv("APP_SECRET")

port = int(os.environ.get('PORT', 5000))
server = Server(host="0.0.0.0", port=port)

def _make_context():
    return dict(UserType=UserType)

# initialize flask script
manager = Manager(app)

# enable migration commands
manager.add_command("runserver", server)
manager.add_command("db", MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def seed_default_data(prompt=True):
    if environment == "production":
        print("\n\n\tNot happening! Aborting...\n\n Aborted\n\n")
        return

    if environment in ["testing", "development"]:
        if (prompt_bool("\n\nAre you sure you want to seed your database, all previous data will be wiped off?")):
            try:
                # drops all the tables 
                db.drop_all()
                db.session.commit()

                # creates all the tables
                db.create_all()
            except SQLAlchemyError as error:
                db.session.rollback()
                print("\n\n\tCommand could not execute due to the error below! Aborting...\n\n Aborted\n\n" + str(error) + "\n\n")
                return

            try:
                # seed default user_types
                create_default_user_types()

                # seed default user
                admin_user_type_id = UserType.query.filter_by(title="admin").first().id
                moov_user_type_id = UserType.query.filter_by(title="moov").first().id
                school_user_type_id = UserType.query.filter_by(title="school").first().id
                car_owner_user_type_id = UserType.query.filter_by(title="car_owner").first().id

                # no wallet needed for admin
                admin_user = create_user(admin_user_type_id, "admin", os.environ.get('ADMIN_EMAIL'), os.environ.get('ADMIN_PASSWORD'))
                moov = create_user(moov_user_type_id, "moov", os.environ.get('MOOV_EMAIL'), os.environ.get('MOOV_PASSWORD'))
                # school = create_user(school_user_type_id, "school", "school@email.com", os.environ.get('SCHOOL_PASSWORD'))
                car_owner = create_user(car_owner_user_type_id, "school", "car_owner@email.com", os.environ.get('CAR_OWNER_PASSWORD'))
                admin_user.save()

                # seed default school
                school = create_school(user_type_id=school_user_type_id)
                
                # seed default wallets
                wallet_amount = 0.0
                create_wallet(user_id=moov.id, wallet_amount=wallet_amount, description="Moov Wallet")
                create_wallet(user_id=school.id, wallet_amount=wallet_amount, description="School Wallet")
                create_wallet(user_id=car_owner.id, wallet_amount=wallet_amount, description="Car Owner Wallet")

                # seed percentage prices
                create_percentage_price(title="default_car_owner", price=0.1, description="Car owner")
                create_percentage_price(title="default_school", price=0.1, description="School")
                create_percentage_price(title="default_driver", price=0.4, description="Driver")
                create_percentage_price(title="default_moov", price=0.4, description="Moov")
                create_percentage_price(title="default_transfer", price=0.0, description="Transfer")

                # seed default admission type
                create_admission_type()

                # seed default icons
                default_icon = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png"
                create_icon(icon=default_icon, operation_type="transfer_operation")
                create_icon(icon=default_icon, operation_type="borrow_operation")
                create_icon(icon=default_icon, operation_type="cancel_operation")
                create_icon(icon=default_icon, operation_type="load_wallet_operation")
                create_icon(icon=default_icon, operation_type="ride_operation")
                create_icon(icon=default_icon, operation_type="free_ride_operation")
                create_icon(icon=default_icon, operation_type="moov_operation")

                message = "\n\n\tYay *\(^o^)/* \n\n Your database has been succesfully seeded !!! \n\n\t *\(@^_^@)/* <3 <3 \n\n"
            except SQLAlchemyError as error:
                db.session.rollback()
                message = "\n\n\tThe error below occured when trying to seed the database\n\n\n" + str(error) + "\n\n"

            print(message)

        else:
            print("\n\n\tAborting...\n\n\tAborted\n\n")

    else:
        print("\n\n\tAborting... Invalid environment '{}'.\n\n"
              .format(environment))

# initialize the log handler
handler = RotatingFileHandler('errors.log', maxBytes=10000000, backupCount=5)
formatter = logging.Formatter( "%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s ")
# set the log handler level
handler.setLevel(logging.INFO)
# set the app logger level
app.logger.setLevel(logging.INFO)
werkzeug_handler = logging.getLogger('werkzeug')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.addHandler(werkzeug_handler)

manager.run()
