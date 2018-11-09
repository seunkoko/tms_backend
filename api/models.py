# models
import os
import json
import enum

from datetime import datetime
from alembic import op
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, relationship

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import JSON, TEXT, TypeDecorator
from sqlalchemy import event, and_
from werkzeug import generate_password_hash, check_password_hash

try:
    from generator.id_generator import PushID
except ImportError:
    from moov_backend.api.generator.id_generator import PushID

def to_camel_case(snake_str):
    title_str = snake_str.title().replace("_", "")
    return title_str[0].lower() + title_str[1:]


class StringyJSON(TypeDecorator):
    """Stores and retrieves JSON as TEXT."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        """Map value into json data."""
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        """Map json data to python dictionary."""
        if value is not None:
            value = json.loads(value)
        return value


# TypeEngine.with_variant says "use StringyJSON instead when
# connecting to 'sqlite'"
MagicJSON = JSON().with_variant(StringyJSON, 'sqlite')

type_map = {'sqlite': MagicJSON, 'postgresql': JSON}
json_type = type_map[os.getenv("DB_TYPE")]

db = SQLAlchemy()

class ModelViewsMix(object):

    def serialize(self):
        return {to_camel_case(column.name): getattr(self, column.name)
                for column in self.__table__.columns}

    def save(self):
        """Saves an instance of the model to the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError as error:
            db.session.rollback()
            return error
    
    def delete(self):
        """Delete an instance of the model from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError as error:
            db.session.rollback()
            return error


# enums
class OperationType(enum.Enum):
    transfer_type = "transfer"
    wallet_type = "load_wallet"
    ride_type = "ride_fare"
    borrow_type = "borrow_me"
    cancel_type = "cancel_ride"


class TransactionType(enum.Enum):
    debit_type = "debit"
    credit_type = "credit"
    both_types = "debit and credit"


class FreeRideType(enum.Enum):
    social_share_type = "social_share"
    ride_type = "ride"


class RatingsType(enum.Enum):
    no_ratings = None
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


class AuthenticationType(enum.Enum):
    facebook = "facebook_type"
    google = "google_type"
    email = "email_type"


# models
class RateMe(db.Model, ModelViewsMix):
    
    __tablename__ = 'RateMe'

    id = db.Column(db.String, primary_key=True)
    rating_type = db.Column(db.Enum(RatingsType), nullable=False)
    ratee_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    rater_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    ratee = relationship("User", single_parent=True, foreign_keys=[ratee_id])
    rater = relationship("User", single_parent=True, foreign_keys=[rater_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

    def __repr__(self):
        return '<RateMe ratee-%r rater-%r>' % (self.ratee_id, self.rater_id) 


class User(db.Model, ModelViewsMix):
    
    __tablename__ = 'User'

    id = db.Column(db.String, primary_key=True)
    authentication_type = db.Column(db.Enum(AuthenticationType))
    user_type_id = db.Column(db.String(), db.ForeignKey('UserType.id', ondelete='SET NULL'))
    user_id = db.Column(db.String, unique=True) 
    school_id = db.Column(db.String(), db.ForeignKey('SchoolInfo.id', ondelete='SET NULL'))
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    _password = db.Column('password', db.String())
    _ratings = db.Column('ratings', db.Integer)
    image_url = db.Column(db.String)
    mobile_number = db.Column(db.String, nullable=False)
    authorization_code = db.Column(db.String, unique=True)
    authorization_code_status = db.Column(db.Boolean, default=False)
    number_of_rides = db.Column(db.Integer, default=0)
    reset_password = db.Column(db.Boolean, default=False)
    current_ride = db.Column(json_type, nullable=True)
    forgot_password = db.relationship('ForgotPassword', backref='user_forgot_password', lazy='dynamic')
    wallet_user = db.relationship('Wallet', cascade="all,delete-orphan", back_populates='user_wallet')
    free_ride = db.relationship('FreeRide', backref='user_free_ride', lazy='dynamic')
    driver_info = db.relationship('DriverInfo', backref='driver_information', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<User %r %r>' % (self.firstname, self.lastname)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, item):
        return setattr(self, key, item)
    
    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    password = db.synonym('_password',
                        descriptor=property(_get_password,
                                            _set_password))

    def _get_ratings(self):
        self._ratings = self.get_average_ratings() 
        return self._ratings

    def _set_ratings(self):
        self._ratings = self.get_average_ratings() 

    ratings = db.synonym('_ratings',
                        descriptor=property(_get_ratings,
                                            _set_ratings))

    def get_average_ratings(self):
        total_ratings = 0
        my_ratings = RateMe.query.filter(and_(
                        RateMe.ratee_id==str(self.id),
                        RateMe.rating_type!=RatingsType.no_ratings
                    )).all()

        my_ratings_count = len(my_ratings)
        if my_ratings_count == 0:
            return None

        for rating in my_ratings:
            if rating.rating_type == RatingsType.one:
                total_ratings += 1
            if rating.rating_type == RatingsType.two:
                total_ratings += 2
            if rating.rating_type == RatingsType.three:
                total_ratings += 3
            if rating.rating_type == RatingsType.four:
                total_ratings += 4
            if rating.rating_type == RatingsType.five:
                total_ratings += 5

        average_ratings = int(round(total_ratings / my_ratings_count, 0))
        return average_ratings 

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def is_user_data_taken(cls, email):
        return db.session.query(db.exists().where(User.email==email)).scalar()

    @classmethod
    def is_user_id_taken(cls, user_id):
        return db.session.query(db.exists().where(User.user_id==user_id)).scalar()

    @classmethod
    def confirm_login(cls, email, user_id):
        user = db.session.query(User).filter(User.email==email).first()
        if str(user.user_id) == str(user_id):
            return True
        return False

    @classmethod
    def add_current_ride(cls, user_email, driver_info, user_location_name, user_destination_name, user_location, user_destination):
        user = db.session.query(User).filter(User.email==user_email).first()

        obj = {}
        obj["driver_info"] = driver_info
        obj["user_location_name"] = user_location_name
        obj["user_destination_name"] = user_destination_name
        obj["user_location"] = user_location
        obj["user_destination"] = user_destination
        user.current_ride = obj
        return user.save()

    @classmethod
    def remove_current_ride(cls, user_email):
        user = db.session.query(User).filter(User.email==user_email).first()
        user.current_ride = None
        user.save()
        


class ForgotPassword(db.Model, ModelViewsMix):
  
    __tablename__ = 'ForgotPassword'

    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    school_id = db.Column(db.String(), db.ForeignKey('SchoolInfo.id', ondelete='SET NULL'))
    temp_password = db.Column(db.String)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<ForgotPassword %r>' % (self.user_id)


class UserType(db.Model, ModelViewsMix):
  
    __tablename__ = 'UserType'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    description = db.Column(db.String, nullable=True)
    users = db.relationship('User', backref='user_type', lazy='dynamic')
    schools = db.relationship('SchoolInfo', backref='school_info_type', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<UserType %r>' % (self.title)


class FreeRide(db.Model, ModelViewsMix):
    
    __tablename__ = 'FreeRide'

    id = db.Column(db.String, primary_key=True)
    free_ride_type = db.Column(db.Enum(FreeRideType), nullable=False)
    token = db.Column(db.String, unique=True, nullable=False)
    token_status = db.Column(db.Boolean, default=False)
    description = db.Column(db.String, nullable=True)
    user_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<FreeRide %r>' % (self.user_id)


class DriverInfo(db.Model, ModelViewsMix):
    
    __tablename__ = 'DriverInfo'

    id = db.Column(db.String, primary_key=True)
    location_latitude = db.Column(db.Float, nullable=True)
    location_longitude = db.Column(db.Float, nullable=True)
    destination_latitude = db.Column(db.Float, nullable=True)
    destination_longitude = db.Column(db.Float, nullable=True)
    car_slots = db.Column(db.Integer, nullable=True)
    available_car_slots = db.Column(db.Integer)
    status = db.Column(db.Boolean, default=False)
    on_trip_with = db.Column(json_type, nullable=True)
    car_model = db.Column(db.String)
    left_image = db.Column(db.String)
    right_image = db.Column(db.String)
    front_image = db.Column(db.String)
    back_image = db.Column(db.String)
    plate_number = db.Column(db.String)
    admin_confirmed = db.Column(db.Boolean, default=False)
    bank_name = db.Column(db.String)
    account_number = db.Column(db.String)
    driver_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'), unique=True)
    admission_type_id = db.Column(db.String(), db.ForeignKey('AdmissionType.id', ondelete='SET NULL'))
    number_of_rides = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<DriverInfo %r>' % (self.driver_id)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, item):
        return setattr(self, key, item)

    @classmethod
    def add_to_trip(cls, driver_id, email, slots):
        driver = db.session.query(DriverInfo).filter(DriverInfo.driver_id==driver_id).first()
        if not driver.on_trip_with:
            driver.on_trip_with = {}

        obj = {}
        for key in driver.on_trip_with:
            obj[str(key)] = driver.on_trip_with[key]
        obj[email] = slots
        driver.on_trip_with = obj
        driver.available_car_slots -= slots
        driver.save()

    @classmethod
    def remove_from_trip(cls, driver_id, email):
        driver = db.session.query(DriverInfo).filter(DriverInfo.driver_id==driver_id).first()
        slots = driver.on_trip_with[email]
        driver.available_car_slots += slots

        obj = {}
        for key in driver.on_trip_with:
            obj[str(key)] = driver.on_trip_with[key]
        obj.pop(email, None)
        driver.on_trip_with = obj
        if not driver.on_trip_with:
            driver.on_trip_with = None
        driver.save()

    @classmethod
    def confirm_on_trip(cls, driver_id, email):
        driver = db.session.query(DriverInfo).filter(DriverInfo.driver_id==driver_id).first()
        if email in driver.on_trip_with:
            return True
        return False


class SchoolInfo(db.Model, ModelViewsMix):
    
    __tablename__ = "SchoolInfo"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    alias = db.Column(db.String)
    _password = db.Column('password', db.String())
    admin_status = db.Column(db.Boolean)
    email = db.Column(db.String, unique=True, nullable=False)
    user_type_id = db.Column(db.String(), db.ForeignKey('UserType.id', ondelete='SET NULL'))
    reset_password = db.Column(db.Boolean, default=False)
    account_number = db.Column(db.String, nullable=False)
    bank_name = db.Column(db.String, nullable=False)
    mobile_number = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    wallet_school = db.relationship('Wallet', cascade="all,delete-orphan", back_populates='school_wallet')
    forgot_password = db.relationship('ForgotPassword', backref='school_forgot_password', lazy='dynamic')
    admission_type = db.relationship('AdmissionType', backref='school_admission_type', lazy='dynamic')
    percentage_price = db.relationship('PercentagePrice', cascade="all,delete-orphan", backref='price_information', lazy='dynamic')
    school_info = db.relationship('User', backref='school_information', lazy='dynamic')

    def __repr__(self):
        return '<SchoolInfo %r>' % (self.name)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    password = db.synonym('_password',
                        descriptor=property(_get_password,
                                            _set_password))


class AdmissionType(db.Model, ModelViewsMix):
    
    __tablename__ = "AdmissionType"

    id = db.Column(db.String, primary_key=True)
    admission_type = db.Column(db.String, unique=True)
    description = db.Column(db.String)
    school_id = db.Column(db.String(), db.ForeignKey('SchoolInfo.id', ondelete='SET NULL'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    driver_info = db.relationship('DriverInfo', backref='admission_driver_info', lazy='dynamic')

    def __repr__(self):
        return '<AdmissionType %r>' % (self.admission_type)


class PercentagePrice(db.Model, ModelViewsMix):
    
    __tablename__ = "PercentagePrice"

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=True)
    school_id = db.Column(db.String(), db.ForeignKey('SchoolInfo.id'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow,
            onupdate=datetime.utcnow)

    def __repr__(self):
        return '<PercentagePrice %r %r>' % (self.description, self.price)


class Wallet(db.Model, ModelViewsMix):
    
    __tablename__ = 'Wallet'

    id = db.Column(db.String, primary_key=True)
    wallet_amount =  db.Column(db.Float, default=0.00)
    user_id = db.Column(db.String(), db.ForeignKey('User.id'))
    school_id = db.Column(db.String(), db.ForeignKey('SchoolInfo.id'))
    user_wallet = db.relationship('User', back_populates='wallet_user')
    school_wallet = db.relationship('SchoolInfo', back_populates='wallet_school')
    description = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Wallet %r %r>' % (self.user_id, self.wallet_amount)


class Transaction(db.Model, ModelViewsMix):
    
    __tablename__ = 'Transaction'

    id = db.Column(db.String, primary_key=True)
    transaction_detail = db.Column(db.String, nullable=False)
    type_of_operation = db.Column(db.Enum(OperationType), nullable=False)
    type_of_transaction = db.Column(db.Enum(TransactionType), nullable=False)
    cost_of_transaction = db.Column(db.Float, default=0.00)
    receiver_amount_before_transaction = db.Column(db.Float, default=0.00)
    receiver_amount_after_transaction = db.Column(db.Float, default=0.00)
    sender_amount_before_transaction = db.Column(db.Float, default=0.00)
    sender_amount_after_transaction = db.Column(db.Float, default=0.00)
    paystack_deduction = db.Column(db.Float, default=0.00)
    receiver_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    receiver = relationship("User", single_parent=True, foreign_keys=[receiver_id])
    sender = relationship("User", single_parent=True, foreign_keys=[sender_id])
    receiver_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id', ondelete='SET NULL'))
    sender_wallet_id = db.Column(db.String(), db.ForeignKey('Wallet.id', ondelete='SET NULL'))
    receiver_wallet = relationship("Wallet", single_parent=True, foreign_keys=[receiver_wallet_id])
    sender_wallet = relationship("Wallet", single_parent=True, foreign_keys=[sender_wallet_id])
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Transaction %r %r>' % (self.receiver_id, self.transaction_detail)


class Icon(db.Model, ModelViewsMix):
    
    __tablename__ = "Icon"

    id = db.Column(db.String, primary_key=True)
    icon = db.Column(db.String, nullable=False)
    operation_type = db.Column(db.String, nullable=False, unique=True)
    notifications = db.relationship('Notification', backref='notification_icon', lazy='dynamic')

    def __repr__(self):
        return '<Icon %r>' % (self.operation_type)


class Notification(db.Model, ModelViewsMix):
    
    __tablename__ = 'Notification'

    id = db.Column(db.String, primary_key=True)
    message = db.Column(db.String)
    recipient_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    sender_id = db.Column(db.String(), db.ForeignKey('User.id', ondelete='SET NULL'))
    transaction_icon_id = db.Column(db.String(), db.ForeignKey('Icon.id', ondelete='SET NULL'))
    recipient = relationship("User", single_parent=True, foreign_keys=[recipient_id])
    sender = relationship("User", single_parent=True, foreign_keys=[sender_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Notification %r>' % (self.message)


def fancy_id_generator(mapper, connection, target):
    '''
    A function to generate unique identifiers on insert
    '''
    push_id = PushID()
    target.id = push_id.next_id()

# associate the listener function with models, to execute during the
# "before_insert" event
tables = [
            RateMe,
            User, 
            ForgotPassword,
            UserType, 
            Wallet, 
            Transaction, 
            Notification, 
            PercentagePrice,
            AdmissionType,
            Icon,
            SchoolInfo,
            DriverInfo,
            FreeRide
        ]

for table in tables:
    event.listen(table, 'before_insert', fancy_id_generator)
