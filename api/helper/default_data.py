import os

from ..models import User, UserType, PercentagePrice, Wallet, AdmissionType, Icon, SchoolInfo

def create_default_user_types():
    user_types = ['admin', 'driver', 'student', 'moov', 'school', 'car_owner']
    for user_type in user_types:
        user_type = UserType(
            title=user_type,
            description='{} privilege'.format(user_type)
        )
        user_type.save()

def create_user(user_type_id, name, email, password):
    new_user = User(
                    user_type_id=user_type_id,
                    password=password,
                    firstname=name,
                    lastname=name,
                    image_url="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973461_1280.png",
                    email=email
                )
    new_user.save()
    return new_user

def create_percentage_price(title, price, description):
    new_percentage_price = PercentagePrice(
                                title=title,
                                price=price,
                                description= "{0}'s percentage price".format(description)        
                            )
    return new_percentage_price.save()

def create_wallet(user_id, wallet_amount, description):
    new_wallet = Wallet(
                    user_id= user_id,
                    wallet_amount= wallet_amount,
                    description= description
                )
    return new_wallet.save()

def create_admission_type():
    new_admission_type = AdmissionType(
                            admission_type="freelance",
                            description="default admission type"
                        )
    return new_admission_type.save()

def create_school(user_type_id):
    new_school = SchoolInfo(
                            name="default_school",
                            alias="school",
                            password=os.environ.get('SCHOOL_PASSWORD'),
                            admin_status=True,
                            email=os.environ.get('SCHOOL_EMAIL'),
                            user_type_id=user_type_id
                        )
    new_school.save()
    return new_school

def create_icon(icon, operation_type):
    new_icon = Icon(
                    icon=icon,
                    operation_type=operation_type
                )
    return new_icon.save()
