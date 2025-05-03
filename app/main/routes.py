from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import MRIRequest, Insurance, Pref
from app import db
from datetime import date
import os
import uuid
import jdatetime
from app.forms import ProfileForm
from jdatetime import date as jdate

main_bp = Blueprint('main', __name__)

# Route to serve images from the /images directory
@main_bp.route('/images/<filename>')
def serve_image(filename):
    image_path = os.path.join(current_app.root_path, 'images', filename)
    if not os.path.exists(image_path):
        return render_template('404_image.html'), 404
    return send_from_directory(os.path.join(current_app.root_path, 'images'), filename)

@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def reserve():
    insurances = Insurance.query.all()
    today_gregorian = date.today()
    today_persian = jdatetime.date.today().strftime('%Y/%m/%d')

    pref = Pref.query.first()
    if not pref:
        flash("تنظیمات برنامه پیدا نشد.")
        return redirect(url_for('main.reserve'))

    if request.method == 'POST':
        data = request.form

        # ✅ CHECK: One request per day per applicant
        max_daily_per_user = pref.max_user_reserve_day
        daily_user_count = MRIRequest.query.filter_by(
            user_id=current_user.id,
            reservation_date=today_gregorian
        ).count()

        if daily_user_count >= max_daily_per_user:
            flash(f"شما امروز سقف تعداد درخواست ({max_daily_per_user}) را ثبت كرده‌ايد.")
            return redirect(url_for('main.reserve'))

        # ✅ CHECK: Max 3 requests per month per user
        from sqlalchemy import extract, and_
        max_monthly_requests = pref.max_user_reserve_month
        monthly_count = MRIRequest.query.filter(
            and_(
                MRIRequest.user_id == current_user.id,
                extract('year', MRIRequest.reservation_date) == today_gregorian.year,
                extract('month', MRIRequest.reservation_date) == today_gregorian.month
            )
        ).count()
        if monthly_count >= max_monthly_requests:
            flash("شما در اين ماه قبلاً {} درخواست ثبت كرده‌ايد.".format(max_monthly_requests))
            return redirect(url_for('main.reserve'))

        # ✅ CHECK: Max 10 total requests per day across all users
        max_daily_requests = pref.max_mri_reserve_day
        daily_total = MRIRequest.query.filter_by(reservation_date=today_gregorian).count()
        if daily_total >= max_daily_requests:
            flash("سقف تعداد درخواست‌ها براي امروز ({}) پر شده است. لطفاً فردا مجدداً تلاش كنيد.".format(
                max_daily_requests))
            return redirect(url_for('main.reserve'))

        # ✅ Validate 'has_requested_site'
        has_requested_site = data.get('has_requested_site')
        if has_requested_site not in ['0', '1']:
            flash("لطفاً مشخص کنید که آیا قبلاً درخواستی ثبت کرده‌اید یا خیر.")
            return redirect(url_for('main.reserve'))
        has_requested_site = has_requested_site == '1'

        # ✅ HANDLE file upload
        uploaded_file = request.files.get('uploaded_image')
        image_path = None
        if uploaded_file:
            UPLOAD_FOLDER = os.path.join(current_app.root_path, 'images')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.filename)[1]
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(save_path)
            image_path = os.path.join('images', filename).replace('\\', '/')

        # ✅ CREATE and save the request
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
            user_explanation=data['user_explanation'],
            uploaded_image_path=image_path,
            has_requested_site=has_requested_site
        )

        db.session.add(new_request)
        db.session.commit()
        flash('درخواست شما با موفقيت ثبت شد.')
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
            parts = reservation_date_persian.split('/')
            if len(parts) == 3:
                jy, jm, jd = map(int, parts)
                g_date = jdate(jy, jm, jd).togregorian()
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

        # Update Password
        if form.current_password.data or form.new_password.data or form.confirm_new_password.data:
            if not form.current_password.data or not form.new_password.data or not form.confirm_new_password.data:
                flash('براي تغيير پسورد فيلد هاي پسورد را تغيير دهيد', 'error')
                return redirect(url_for('main.user_profile'))

            if form.new_password.data != form.confirm_new_password.data:
                flash('رمز عبور جديد با تكرار مرز عبور جديد يكسان نيست', 'error')
                return redirect(url_for('main.user_profile'))

            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.password_hash = generate_password_hash(form.new_password.data)
                flash('رمز عبور با موفقيت ثبت شد', 'success')
                updated = True
            else:
                flash('رمزعبور در حال استفاده اشتباه است', 'error')
                return redirect(url_for('main.user_profile'))

        if updated:
            db.session.commit()
            flash('پروفايل با موفقيت به روزرساني شد.', 'success')
        else:
            flash('تغييري انجام نشد.', 'info')

        return redirect(url_for('main.user_profile'))

    if request.method == 'GET':
        form.national_code.data = current_user.national_code

    return render_template('user_profile.html', form=form)

@main_bp.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    reservation = MRIRequest.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        flash("فقط ميتوانيد نوبت هاي خود را حذف كنيد.", "error")
        return redirect(url_for('main.my_reservations'))

    db.session.delete(reservation)
    db.session.commit()
    flash("حذف نوبت با موفقيت انجام شد", "success")
    return redirect(url_for('main.my_reservations'))
