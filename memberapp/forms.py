from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField
from wtforms.validators import DataRequired,Email,Length,EqualTo
from flask_wtf.file import FileAllowed, FileField, FileRequired

class ContactForm(FlaskForm):
    screenshot = FileField("upload screenshot", validators=[FileAllowed(['png','jpg','jpeg'], "Please upload only jpg, jpeg or png files only."),FileRequired()])

    email = StringField("Your Email: ",validators=[Email(message="Hello, your email is invalid"),DataRequired(message="We will need to have your email address in order to get to you")])
    confirm_email = StringField("Confirm Email", validators=[EqualTo('email')])
    message = TextAreaField("Message", validators=[DataRequired(),Length(min=10, message="This message is too small now!")])
    submit = SubmitField("Send Message")