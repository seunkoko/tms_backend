import os

from flask import current_app, render_template
from flask_mail import Mail, Message


def send_forgot_password_mail(email, firstname, password):
  	try:
            current_app.config.update(
                #EMAIL SETTINGS
                MAIL_SERVER='smtp.gmail.com',
                MAIL_PORT=465,
                MAIL_USE_SSL=True,
                MAIL_USERNAME = os.environ.get('MOOV_EMAIL'),
                MAIL_PASSWORD = os.environ.get('MOOV_EMAIL_PASSWORD')
            )
            mail = Mail(current_app) 
            message = Message("Forgot Password",
                sender=os.environ.get('MOOV_EMAIL'),
                recipients=[email])
            message.html = render_template(
                'template_forgot_password.html', 
                firstname=firstname, 
                password=password
            )  
            mail.send(message)    
            return {
                "status": True,
                "message": "Email sent succesfully"
            }
	except Exception, e:
            print ("exception--->", str(e))
            return {
                "status": False,
                "message": str(e)
            }
    