from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import User, MRIRequest
from app import db
import re
import persian
import jdatetime
from sqlalchemy import or_, and_
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Decorators ---
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied.")
            return redirect(url_for('main.reserve'))
        return func(*args, **kwargs)
    return decorated_view

def can_assign_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_admin or current_user.can_assign_turn):
            flash("Access denied.")
            return redirect(url_for('main.reserve'))
        return func(*args, **kwargs)
    return decorated_view

# --- Routes ---
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from jdatetime import date as jdate

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    applicant_name = request.args.get('applicant_name')

    query = MRIRequest.query

    # Date filtering
    if start_date and end_date:
        try:
            start_parts = start_date.split('/')
            end_parts = end_date.split('/')
            if len(start_parts) == 3 and len(end_parts) == 3:
                sjy, sjm, sjd = map(int, start_parts)
                ejy, ejm, ejd = map(int, end_parts)
                g_start = jdate(sjy, sjm, sjd).togregorian()
                g_end = jdate(ejy, ejm, ejd).togregorian()
                query = query.filter(
                    MRIRequest.reservation_date.between(g_start, g_end)
                )
        except Exception as e:
            flash(f"Date conversion error: {e}")
            return redirect(url_for('admin.dashboard'))

    # User filtering
    if applicant_name:
        query = query.filter(
            or_(
                MRIRequest.application_first_name.ilike(f"%{applicant_name}%"),
                MRIRequest.application_last_name.ilike(f"%{applicant_name}%")
            )
        )

    reservations = query.all()

    # --- Count per user ---
    user_reservation_counts = {}

    for r in reservations:
        user_key = (r.application_first_name, r.application_last_name)
        if user_key not in user_reservation_counts:
            user_reservation_counts[user_key] = 0
        user_reservation_counts[user_key] += 1

    report_data = []
    for (first_name, last_name), count in user_reservation_counts.items():
        report_data.append({
            'first_name': first_name,
            'last_name': last_name,
            'reservation_count': count
        })

    return render_template('admin_dashboard.html',
        report_data=report_data,
        reservations=reservations,
        start_date=start_date,
        end_date=end_date,
        applicant_name=applicant_name
    )


@admin_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        national_code = request.form['national_code']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        section = request.form['section']
        is_admin = 'is_admin' in request.form
        can_assign_turn = 'can_assign_turn' in request.form
        is_active = 'is_active' in request.form

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin.create_user'))

        user = User(
            username=username,
            national_code=national_code,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            section=section,
            is_admin=is_admin,
            can_assign_turn=can_assign_turn,
            is_active=is_active
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        flash('User created successfully.')
        return redirect(url_for('admin.dashboard'))

    return render_template('create_user.html')

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('list_users.html', users=users)

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)

        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.national_code = request.form.get('national_code', user.national_code)
        user.phone_number = request.form.get('phone_number', user.phone_number)
        user.section = request.form.get('section', user.section)
        user.is_admin = 'is_admin' in request.form
        user.can_assign_turn = 'can_assign_turn' in request.form
        user.is_active = 'is_active' in request.form

        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('admin.list_users'))

    return render_template('edit_user.html', user=user)

@admin_bp.route('/reservations')
@login_required
@can_assign_required
def view_reservations():
    filter_status = request.args.get('filter')
    search_query = request.args.get('q')

    query = MRIRequest.query

    # --- Search ---
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                MRIRequest.patient_name.ilike(search),
                MRIRequest.application_first_name.ilike(search),
                MRIRequest.application_last_name.ilike(search),
                MRIRequest.tracking_code.ilike(search)
            )
        )

    # --- Filter ---
    if filter_status == 'assigned':
        query = query.filter(
            MRIRequest.turn_date.isnot(None),
            MRIRequest.turn_hour.isnot(None)
        )
    elif filter_status == 'unassigned':
        query = query.filter(
            or_(
                MRIRequest.turn_date.is_(None),
                MRIRequest.turn_hour.is_(None)
            )
        )

    reservations = query.all()
    return render_template('reservations_list.html', reservations=reservations)

@admin_bp.route('/assign_turn/<int:req_id>', methods=['POST'])
@login_required
def assign_turn(req_id):
    if not (current_user.is_admin or current_user.can_assign_turn):
        flash("You don't have permission to assign turns.")
        return redirect(url_for('main.reserve'))

    turn_date_raw = request.form.get('turn_date')
    turn_hour_raw = request.form.get('turn_hour')

    if not turn_date_raw or not turn_hour_raw:
        flash("Both turn date and turn hour are required.")
        return redirect(url_for('admin.view_reservations'))

    # Step 1: Convert Persian numbers to English
    turn_date_en = persian.convert_ar_numbers(turn_date_raw)
    turn_hour_en = persian.convert_ar_numbers(turn_hour_raw)

    # Step 2: Convert Jalali to Gregorian
    try:
        parts = turn_date_en.split('/')
        if len(parts) == 3:
            jy, jm, jd = map(int, parts)
            gregorian_date = jdatetime.date(jy, jm, jd).togregorian()
            turn_date_final = gregorian_date.strftime('%Y-%m-%d')  # format like 2025-04-29
        else:
            flash("Invalid date format.")
            return redirect(url_for('admin.view_reservations'))
    except Exception as e:
        flash(f"Date conversion error: {e}")
        return redirect(url_for('admin.view_reservations'))

    request_obj = MRIRequest.query.get_or_404(req_id)
    request_obj.turn_date = turn_date_final
    request_obj.turn_hour = turn_hour_en

    db.session.commit()
    flash("Turn assigned successfully.")
    return redirect(url_for('admin.view_reservations'))


@admin_bp.route('/view_image/<int:req_id>')
@login_required
def view_image(req_id):
    request_obj = MRIRequest.query.get_or_404(req_id)
    if not request_obj.uploaded_image:
        flash('No image uploaded for this request.')
        return redirect(url_for('main.my_reservations'))

    from flask import Response
    return Response(request_obj.uploaded_image, mimetype='image/jpeg')
