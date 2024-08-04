from app import db, create_app
from app import User, Geofence, Timestamp

app = create_app()
app.app_context().push()

# Connect to the database
connection = db.engine.connect()

# Adding missing columns to timestamp table
try:
    connection.execute('ALTER TABLE timestamp ADD COLUMN clock_in_edited BOOLEAN DEFAULT FALSE')
except Exception as e:
    print(f"Error updating database schema for clock_in_edited: {e}")

try:
    connection.execute('ALTER TABLE timestamp ADD COLUMN clock_out_edited BOOLEAN DEFAULT FALSE')
except Exception as e:
    print(f"Error updating database schema for clock_out_edited: {e}")

try:
    connection.execute('ALTER TABLE timestamp ADD COLUMN break_duration_edited BOOLEAN DEFAULT FALSE')
except Exception as e:
    print(f"Error updating database schema for break_duration_edited: {e}")

try:
    connection.execute('ALTER TABLE timestamp ADD COLUMN lunch_duration_edited BOOLEAN DEFAULT FALSE')
except Exception as e:
    print(f"Error updating database schema for lunch_duration_edited: {e}")

print("Database schema updated successfully.")
