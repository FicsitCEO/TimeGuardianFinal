from app import db, create_app
from app import User, Geofence, Timestamp

app = create_app()
app.app_context().push()

# Drop all tables
db.drop_all()
print("Dropped all tables.")

# Create all tables
db.create_all()
print("Created all tables.")

# Create a master admin user
master_user = User(
    first_name='Leonard',
    last_name='Jacob',
    password='24DroidTaffy',  # Use a hashed password in a real application
    role='master',
    admin_code='6609xx07'  # Example admin code
)
db.session.add(master_user)
db.session.commit()
print("Created master admin user.")
