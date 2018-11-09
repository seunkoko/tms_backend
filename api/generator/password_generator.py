import string
import random

try:
    from ..models import ForgotPassword
except:
    from moov_backend.api.models import ForgotPassword


# password generator 
def generate_password(size=8, chars=string.ascii_uppercase + string.digits):
    new_password = None

    # runs until a unique password is generated
    while not new_password:
        generated_password = ''.join(random.choice(chars) for _ in range(size))
        _password_found = ForgotPassword.query.filter(ForgotPassword.temp_password==str(generated_password)).first()

        if not _password_found:
            new_password = str(generated_password)

    return new_password
