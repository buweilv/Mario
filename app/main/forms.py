from flask_wtf import Form
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import IPAddress, DataRequired


class HostForm(Form):
 #   username = StringField('Username: ', validators=[DataRequired()])
    IP = StringField('IP: ', validators=[IPAddress(), DataRequired()])
    passwd = PasswordField("Root Password: ", validators=[DataRequired()])
    submit = SubmitField("Submit")