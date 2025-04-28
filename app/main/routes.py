from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import MRIRequest, Insurance
from app import db
from datetime import date
import os
import uuid
import jdatetime
from app.forms import ProfileForm
# ADD THIS
main_bp = Blueprint('main', __name__)

# Route to serve images from the /images directory
@main_bp.route('/images/<filename>')
def serve_image(filename):
    image_path = os.path.join(current_app.root_path, 'images', filename)
    if not os.path.exists(image_path):
        # اگر فایل نبود، یه صفحه HTML زیبا نشون بده
        return render_template('404_image.html'), 404
    return send_from_directory(os.path.join(current_app.root_path, 'images'), filename)

@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def reserve():
    insurances = Insurance.query.all()
    today_gregorian = date.today()
    # Persian today
    today_persian = jdatetime.date.today().strftime('%Y/%m/%d')  # Format nicely like 1403/02/08
    if request.method == 'POST':
        data = request.form

        existing = MRIRequest.query.filter_by(
            applicant_national_id=data['applicant_national_id'],
            reservation_date=today_gregorian
        ).first()

        if existing:
            flash("You have already submitted a request today.")
            return redirect(url_for('main.reserve'))

        uploaded_file = request.files.get('uploaded_image')
        image_path = None

        if uploaded_file:
            # Safe to use current_app here to determine the upload folder
            UPLOAD_FOLDER = os.path.join(current_app.root_path, 'images')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.filename)[1]
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(save_path)

            # Fix the path for URL to access the image from the /images directory
            relative_path = os.path.join('images', filename).replace('\\', '/')
            image_path = relative_path

        new_request = MRIRequest(
            reservation_date=today_gregorian,
            applicant_national_id=data['applicant_national_id'],
            application_first_name=data['application_first_name'],
            application_last_name=data['application_last_name'],
            application_phone_number=data['application_phone_number'],
            application_section=data['application_section'],
            user_id=current_user.id,
            patient_name=data['patient_name'],
            patient_phone_number=data['patient_phone_number'],
            patient_insurance_name=data['patient_insurance_name'],
            tracking_code=data['tracking_code'],
            explanation=data['explanation'],
            uploaded_image_path=image_path
        )

        db.session.add(new_request)
        db.session.commit()
        flash('Your MRI request has been submitted successfully.')

        return redirect(url_for('main.reserve'))

    user_data = current_user
    return render_template('form.html', user=user_data, today=today_persian, insurances=insurances)

@main_bp.route('/my_reservations')
@login_required
def my_reservations():
    query = MRIRequest.query.filter_by(user_id=current_user.id)

    reservation_date_persian = request.args.get('reservation_date')
    turn_assigned = request.args.get('turn_assigned')

    if reservation_date_persian:
        try:
            # تبدیل تاریخ شمسی به میلادی
            parts = reservation_date_persian.split('/')
            if len(parts) == 3:
                jy, jm, jd = map(int, parts)
                g_date = jdatetime.date(jy, jm, jd).togregorian()
                query = query.filter(MRIRequest.reservation_date == g_date)
        except Exception as e:
            flash(f"Invalid Persian date format: {e}")

    if turn_assigned == 'yes':
        query = query.filter(MRIRequest.turn_date.isnot(None))
    elif turn_assigned == 'no':
        query = query.filter(MRIRequest.turn_date.is_(None))

    reservations = query.order_by(MRIRequest.reservation_date.desc()).all()

    return render_template('my_reservations.html', reservations=reservations)

@main_bp.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    form = ProfileForm()

    if form.validate_on_submit():
        updated = False

        # Update National Code
        if form.national_code.data != current_user.national_code:
            current_user.national_code = form.national_code.data
            updated = True

        # Update Password ONLY if user entered something
        if form.current_password.data or form.new_password.data or form.confirm_new_password.data:
            if not form.current_password.data or not form.new_password.data or not form.confirm_new_password.data:
                flash('To change password, please fill all password fields.', 'error')
                return redirect(url_for('main.user_profile'))

            if form.new_password.data != form.confirm_new_password.data:
                flash('New password and confirmation do not match.', 'error')
                return redirect(url_for('main.user_profile'))

            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.password_hash = generate_password_hash(form.new_password.data)
                flash('Password updated successfully.', 'success')
                updated = True
            else:
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('main.user_profile'))

        if updated:
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        else:
            flash('No changes detected.', 'info')

        return redirect(url_for('main.user_profile'))

    # Pre-fill national code
    if request.method == 'GET':
        form.national_code.data = current_user.national_code

    return render_template('user_profile.html', form=form)
