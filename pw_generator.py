#
# from werkzeug.security import generate_password_hash
# print(generate_password_hash("1234"))

from werkzeug.security import generate_password_hash
from app import create_app, db  # ✅ Import create_app
from app.models import User     # Adjust if models are in another location

# Create app using the factory
app = create_app()

with app.app_context():
    hash_value = generate_password_hash("1234")
    User.query.update({User.password_hash: hash_value})  # or User.password if that's your column
    db.session.commit()
    print("✅ All user passwords updated successfully.")
