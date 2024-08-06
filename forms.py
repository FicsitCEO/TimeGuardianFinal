from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, EqualTo

class RegistrationForm(FlaskForm):
    first_name = StringField('Förnamn', validators=[DataRequired(message="Förnamn krävs."), Length(min=2, max=20, message="Förnamnet måste vara mellan 2 och 20 tecken.")])
    last_name = StringField('Efternamn', validators=[DataRequired(message="Efternamn krävs."), Length(min=2, max=20, message="Efternamnet måste vara mellan 2 och 20 tecken.")])
    password = PasswordField('Lösenord', validators=[DataRequired(message="Lösenord krävs.")])
    confirm_password = PasswordField('Bekräfta Lösenord', validators=[DataRequired(message="Bekräfta lösenord krävs."), EqualTo('password', message="Lösenorden måste stämma överens.")])
    admin_code = StringField('Adminkod', validators=[DataRequired(message="Adminkod krävs.")])
    submit = SubmitField('Registrera')

class LoginForm(FlaskForm):
    first_name = StringField('Förnamn', validators=[DataRequired()])
    last_name = StringField('Efternamn', validators=[DataRequired()])
    password = PasswordField('Lösenord', validators=[DataRequired()])
    remember_me = BooleanField('Kom ihåg mig')
    submit = SubmitField('Logga in')

class AdminCodeForm(FlaskForm):
    admin_code = StringField('Adminkod', validators=[DataRequired(message="Adminkod krävs.")])
    submit = SubmitField('Uppdatera Adminkod')

class EditTimestampForm(FlaskForm):
    clock_in = StringField('Checka in', validators=[DataRequired(message="Checka in krävs.")])
    clock_out = StringField('Checka ut', validators=[DataRequired(message="Checka ut krävs.")])
    break_duration = StringField('Rastlängd')
    lunch_duration = StringField('Lunchlängd')
    submit = SubmitField('Uppdatera Tidsstämpel')

class VacationRequestForm(FlaskForm):
    start_date = DateField('Startdatum', format='%Y-%m-%d', validators=[DataRequired(message="Startdatum krävs.")])
    end_date = DateField('Slutdatum', format='%Y-%m-%d', validators=[DataRequired(message="Slutdatum krävs.")])
    submit = SubmitField('Ansök om Semester')

class UpdateAdminCodeForm(FlaskForm):
    new_admin_code = StringField('Ny Adminkod', validators=[DataRequired(message="Ny Adminkod krävs.")])
    submit = SubmitField('Uppdatera Adminkod')

class GeofenceForm(FlaskForm):
    latitude = StringField('Latitud', validators=[DataRequired(message="Latitud krävs.")])
    longitude = StringField('Longitud', validators=[DataRequired(message="Longitud krävs.")])
    radius = StringField('Radie', validators=[DataRequired(message="Radie krävs.")])
    submit = SubmitField('Lägg till Geofence')

