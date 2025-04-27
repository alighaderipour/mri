
from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    national_code = db.Column(db.String(10), nullable=True)
    first_name = db.Column(db.String(15), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    phone_number = db.Column(db.String(11), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    can_assign_turn = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MRIRequest(db.Model):
    __tablename__ = 'mri_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reservation_date = db.Column(db.Date, nullable=False, default=datetime.today)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    applicant_national_id = db.Column(db.String(10), nullable=False)
    application_first_name = db.Column(db.String(30), nullable=False)
    application_last_name = db.Column(db.String(30), nullable=False)
    application_phone_number = db.Column(db.String(11), nullable=False)
    application_section = db.Column(db.String(30), nullable=False)
    patient_name = db.Column(db.String(30), nullable=False)
    patient_phone_number = db.Column(db.String(11), nullable=False)
    patient_insurance_name = db.Column(db.String(20), nullable=False)
    tracking_code = db.Column(db.String(20), nullable=False)
    explanation = db.Column(db.String(100), nullable=False)
    submitted_date = db.Column(db.Date, nullable=False, default=datetime.today)
    submitted_hour = db.Column(db.Time, nullable=False, default=datetime.now().time)
    turn_date = db.Column(db.Date, nullable=True)
    turn_hour = db.Column(db.Time, nullable=True)
    uploaded_image_path = db.Column(db.String(255), nullable=True)  # Storing raw image data



class Insurance(db.Model):
    __tablename__ = 'insurances'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    image_required = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"<Insurance {self.name}>"