from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from forms import RegistrationForm, LoginForm, AdminCodeForm, EditTimestampForm, VacationRequestForm, UpdateAdminCodeForm, GeofenceForm
from datetime import datetime
from geopy.distance import geodesic
import requests
from config import Config  # Import the Config class

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Apply configuration from Config class

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    admin_code = db.Column(db.String(255), nullable=True)
    
    timestamps = db.relationship('Timestamp', backref='user', lazy=True)


class Timestamp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clock_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    clock_out = db.Column(db.DateTime, nullable=True)
    break_duration = db.Column(db.Integer, nullable=True)
    lunch_duration = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    edited = db.Column(db.Boolean, default=False)
    clock_in_edited = db.Column(db.Boolean, default=False)
    clock_out_edited = db.Column(db.Boolean, default=False)
    break_duration_edited = db.Column(db.Boolean, default=False)
    lunch_duration_edited = db.Column(db.Boolean, default=False)

class Vacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Geofence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Register the custom filter with Jinja2
@app.template_filter('format_worked_hours')
def format_worked_hours(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f'{hours}h {minutes}m'

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        admin_code = form.admin_code.data
        admin = User.query.filter_by(admin_code=admin_code, role='admin').first()
        if admin:
            user = User(first_name=form.first_name.data, last_name=form.last_name.data, password=form.password.data, role='worker', admin_code=admin_code)
            db.session.add(user)
            db.session.commit()
            flash('Ditt konto har skapats!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Ogiltig admin kod. Vänligen kontakta din administratör.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Fel i fältet '{getattr(form, field).label.text}': {error}", 'danger')
    return render_template('register.html', title='Registrera', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(first_name=form.first_name.data, last_name=form.last_name.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('master_dashboard' if user.role == 'master' else 'admin_dashboard' if user.role == 'admin' else 'worker_dashboard'))
        else:
            flash('Inloggningen misslyckades. Vänligen kontrollera förnamn, efternamn och lösenord.', 'danger')
    return render_template('login.html', title='Logga in', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/master_dashboard', methods=['GET', 'POST'])
@login_required
def master_dashboard():
    if current_user.role != 'master':
        return redirect(url_for('home'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            password = request.form.get('password')
            admin_code = request.form.get('admin_code')
            if first_name and last_name and password and admin_code:
                new_admin = User(first_name=first_name, last_name=last_name, password=password, role='admin', admin_code=admin_code)
                db.session.add(new_admin)
                db.session.commit()
                flash('Admin tillagd framgångsrikt', 'success')
        elif action == 'delete':
            admin_id = request.form.get('admin_id')
            if admin_id:
                admin_to_delete = User.query.get(admin_id)
                if admin_to_delete and admin_to_delete.role == 'admin':
                    db.session.delete(admin_to_delete)
                    db.session.commit()
                    flash('Admin borttagen framgångsrikt', 'success')

    admins = User.query.filter_by(role='admin').all()
    return render_template('master_dashboard.html', title='Master Dashboard', admins=admins)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role not in ['master', 'admin']:
        return redirect(url_for('home'))

    update_admin_code_form = UpdateAdminCodeForm()
    geofence_form = GeofenceForm()

    if request.method == 'POST':
        if update_admin_code_form.validate_on_submit():
            current_user.admin_code = update_admin_code_form.new_admin_code.data
            db.session.commit()
            flash('Admin kod uppdaterad framgångsrikt', 'success')
        elif geofence_form.validate_on_submit():
            new_geofence = Geofence(latitude=geofence_form.latitude.data, longitude=geofence_form.longitude.data, radius=geofence_form.radius.data, admin_id=current_user.id)
            db.session.add(new_geofence)
            db.session.commit()
            flash('Geofence tillagd framgångsrikt', 'success')

    workers = User.query.filter_by(admin_code=current_user.admin_code, role='worker').all()
    vacations = Vacation.query.filter(Vacation.user_id.in_([worker.id for worker in workers])).all()
    geofences = Geofence.query.filter_by(admin_id=current_user.id).all()
    print(f"Geofences in admin_dashboard: {geofences}")

    timestamps = Timestamp.query.filter(Timestamp.user_id.in_([worker.id for worker in workers])).order_by(Timestamp.clock_in.desc()).all()

    return render_template('admin_dashboard.html', title='Admin Dashboard', workers=workers, vacations=vacations, update_admin_code_form=update_admin_code_form, geofence_form=geofence_form, geofences=geofences, admin_code=current_user.admin_code, timestamps=timestamps)

@app.route('/view_times/<int:worker_id>', methods=['GET', 'POST'])
@login_required
def view_times(worker_id):
    if current_user.role not in ['master', 'admin']:
        return redirect(url_for('home'))

    worker = User.query.get(worker_id)
    if not worker or worker.role != 'worker' or worker.admin_code != current_user.admin_code:
        flash('Ogiltig arbetare eller otillräcklig åtkomst', 'danger')
        return redirect(url_for('admin_dashboard'))

    timestamps = Timestamp.query.filter_by(user_id=worker_id).order_by(Timestamp.clock_in.desc()).all()
    return render_template('view_times.html', title=f'Tider för {worker.first_name} {worker.last_name}', worker=worker, timestamps=timestamps)

@app.route('/approve_vacation', methods=['POST'])
@login_required
def approve_vacation():
    if current_user.role not in ['master', 'admin']:
        return redirect(url_for('home'))

    vacation_id = request.form.get('vacation_id')
    vacation = Vacation.query.get(vacation_id)
    if vacation:
        vacation.status = 'approved'
        db.session.commit()
        flash('Semester godkänd framgångsrikt', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/decline_vacation', methods=['POST'])
@login_required
def decline_vacation():
    if current_user.role not in ['master', 'admin']:
        return redirect(url_for('home'))

    vacation_id = request.form.get('vacation_id')
    vacation = Vacation.query.get(vacation_id)
    if vacation:
        vacation.status = 'declined'
        db.session.commit()
        flash('Semester nekad framgångsrikt', 'success')

    return redirect(url_for('admin_dashboard'))

# Add the missing endpoint for requesting vacation
@app.route('/request_vacation', methods=['POST'])
@login_required
def request_vacation():
    if current_user.role != 'worker':
        return redirect(url_for('home'))

    vacation_form = VacationRequestForm()
    if vacation_form.validate_on_submit():
        new_vacation = Vacation(
            start_date=vacation_form.start_date.data,
            end_date=vacation_form.end_date.data,
            user_id=current_user.id,
            status='pending'
        )
        db.session.add(new_vacation)
        db.session.commit()
        flash('Semesteransökan skickad.', 'success')
    return redirect(url_for('worker_dashboard'))

@app.route('/worker_dashboard', methods=['GET', 'POST'])
@login_required
def worker_dashboard():
    if current_user.role != 'worker':
        return redirect(url_for('home'))

    vacation_form = VacationRequestForm()
    clocked_in = Timestamp.query.filter_by(user_id=current_user.id, clock_out=None).first()

    if request.method == 'POST':
        if clocked_in:
            clocked_in.clock_out = datetime.utcnow()
            clocked_in.lunch_duration = request.form.get('lunch_duration', type=int, default=0)
            clocked_in.break_duration = request.form.get('break_duration', type=int, default=0)
            db.session.commit()
            flash('Du har nu checkat ut.', 'success')
            clocked_in = None  # Update clocked_in to reflect the new state
        else:
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')

            if not lat or not lon:
                flash('Misslyckades med att hämta platsinformation. Vänligen försök igen.', 'danger')
                return redirect(url_for('worker_dashboard'))

            user_location = (float(lat), float(lon))

            worker_admin = User.query.filter_by(admin_code=current_user.admin_code, role='admin').first()
            if not worker_admin:
                flash('Ingen administratör hittades för att kontrollera geofences.', 'danger')
                return redirect(url_for('worker_dashboard'))

            geofences = Geofence.query.filter_by(admin_id=worker_admin.id).all()
            clock_in_allowed = False
            for geofence in geofences:
                geofence_location = (geofence.latitude, geofence.longitude)
                distance = geodesic(user_location, geofence_location).meters
                if distance <= geofence.radius:
                    clock_in_allowed = True
                    new_timestamp = Timestamp(user_id=current_user.id)
                    db.session.add(new_timestamp)
                    db.session.commit()
                    flash('Du har nu checkat in.', 'success')
                    return redirect(url_for('worker_dashboard'))

            if not clock_in_allowed:
                flash('Du är för långt från tillåtet område för att checka in.', 'danger')

    timestamps = Timestamp.query.filter_by(user_id=current_user.id).order_by(Timestamp.clock_in.desc()).all()
    vacations = Vacation.query.filter_by(user_id=current_user.id).all()

    return render_template('worker_dashboard.html', title='Worker Dashboard', vacation_form=vacation_form, clocked_in=clocked_in, timestamps=timestamps, vacations=vacations)



@app.route('/delete_worker/<int:worker_id>', methods=['POST'])
@login_required
def delete_worker(worker_id):
    worker = User.query.get_or_404(worker_id)
    db.session.delete(worker)
    db.session.commit()
    flash('Arbetare borttagen', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_geofence/<int:geofence_id>', methods=['POST'])
@login_required
def delete_geofence(geofence_id):
    if current_user.role not in ['master', 'admin']:
        return redirect(url_for('home'))

    geofence = Geofence.query.get(geofence_id)
    if geofence and geofence.admin_id == current_user.id:
        db.session.delete(geofence)
        db.session.commit()
        flash('Geofence borttagen framgångsrikt', 'success')

    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host = "0.0.0.0", port=5000 )
