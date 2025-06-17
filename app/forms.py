from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class ProfileForm(FlaskForm):
    national_code = StringField('National Code', validators=[DataRequired(), Length(min=10, max=10)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=11, max=11)])

    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        Optional(), EqualTo('new_password', message='Passwords must match')
    ])

    submit = SubmitField('Update Profile')
