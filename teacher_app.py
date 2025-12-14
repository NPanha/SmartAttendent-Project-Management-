from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from datetime import datetime, timedelta, time, date
import psycopg2
from psycopg2 import pool
import json
import os
import qrcode
import base64
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = 'smart-attendance-teacher-secret-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'

# PostgreSQL connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,
        host="localhost",
        database="smart_attendance",
        user="postgres",
        password="2510",
        port="5432"
    )
    
    if connection_pool:
        print("Teacher connection pool created successfully")
        # Test connection
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection_pool.putconn(conn)
        print("Teacher database connection successful")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

def get_db_connection():
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_db_connection(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)

def teacher_login_required(f):
    def decorated_function(*args, **kwargs):
        if 'teacher_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_teacher_by_id(teacher_id):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT teacher_id, full_name, email, created_at
            FROM teachers 
            WHERE teacher_id = %s
        """, (teacher_id,))
        teacher = cursor.fetchone()
        cursor.close()
        
        if teacher:
            return {
                'teacher_id': teacher[0],
                'full_name': teacher[1],
                'email': teacher[2],
                'created_at': teacher[3].strftime('%Y-%m-%d') if teacher[3] else None
            }
        return None
    finally:
        release_db_connection(conn)

def get_teacher_classes(teacher_id):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT
                c.course_id,
                c.course_code,
                c.course_name,
                tt.class_group,
                COUNT(DISTINCT s.student_id) as student_count
            FROM timetable tt
            JOIN courses c ON tt.course_id = c.course_id
            JOIN students s ON tt.class_group = s.class_group
            WHERE tt.teacher_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, tt.class_group
            ORDER BY c.course_code, tt.class_group
        """, (teacher_id,))
        
        classes = []
        for row in cursor.fetchall():
            classes.append({
                'course_id': row[0],
                'course_code': row[1],
                'course_name': row[2],
                'class_group': row[3],
                'student_count': row[4]
            })
        
        cursor.close()
        return classes
    except Exception as e:
        print(f"Error getting teacher classes: {e}")
        return []
    finally:
        release_db_connection(conn)

def get_today_schedule(teacher_id):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        today = datetime.now().strftime('%A')
        current_date = datetime.now().date()
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.timetable_id,
                t.day_of_week,
                t.start_time,
                t.end_time,
                c.course_code,
                c.course_name,
                t.class_group,
                t.room,
                t.type,
                COUNT(a.attendance_id) as attendance_count
            FROM timetable t
            JOIN courses c ON t.course_id = c.course_id
            LEFT JOIN attendance a ON t.course_id = a.course_id 
                AND a.attendance_date = %s
                AND a.attendance_time BETWEEN t.start_time AND t.end_time
            WHERE t.teacher_id = %s 
            AND t.day_of_week = %s
            GROUP BY t.timetable_id, t.day_of_week, t.start_time, t.end_time, 
                     c.course_code, c.course_name, t.class_group, t.room, t.type
            ORDER BY t.start_time
        """, (current_date, teacher_id, today))
        
        schedule = []
        for row in cursor.fetchall():
            schedule.append({
                'timetable_id': row[0],
                'day': row[1],
                'start_time': row[2].strftime('%H:%M'),
                'end_time': row[3].strftime('%H:%M'),
                'course_code': row[4],
                'course_name': row[5],
                'class_group': row[6],
                'room': row[7],
                'type': row[8],
                'attendance_count': row[9] or 0
            })
        
        cursor.close()
        return schedule
    finally:
        release_db_connection(conn)

def get_attendance_stats(teacher_id, period='today'):
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        if period == 'today':
            date_filter = datetime.now().date()
            query_date = "attendance_date = %s"
        elif period == 'week':
            date_filter = datetime.now().date() - timedelta(days=7)
            query_date = "attendance_date >= %s"
        elif period == 'month':
            date_filter = datetime.now().replace(day=1).date()
            query_date = "attendance_date >= %s"
        else:  # all time
            date_filter = None
        
        # Get total students taught by this teacher
        cursor.execute("""
            SELECT COUNT(DISTINCT s.student_id)
            FROM timetable t
            JOIN students s ON t.class_group = s.class_group
            WHERE t.teacher_id = %s
        """, (teacher_id,))
        total_students = cursor.fetchone()[0] or 0
        
        # Get attendance statistics
        if date_filter:
            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT a.student_id) as active_students,
                    COUNT(a.attendance_id) as total_records,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    AVG(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100 as attendance_rate
                FROM attendance a
                JOIN timetable t ON a.course_id = t.course_id
                WHERE t.teacher_id = %s
                AND {query_date}
            """, (teacher_id, date_filter))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT a.student_id) as active_students,
                    COUNT(a.attendance_id) as total_records,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    AVG(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100 as attendance_rate
                FROM attendance a
                JOIN timetable t ON a.course_id = t.course_id
                WHERE t.teacher_id = %s
            """, (teacher_id,))
        
        stats = cursor.fetchone()
        
        cursor.close()
        
        return {
            'total_students': total_students,
            'active_students': stats[0] or 0,
            'total_records': stats[1] or 0,
            'present_count': stats[2] or 0,
            'absent_count': (stats[1] or 0) - (stats[2] or 0),
            'attendance_rate': round(float(stats[3] or 0), 2) if stats[3] else 0
        }
    finally:
        release_db_connection(conn)

def get_class_attendance(course_id, class_group, date_filter=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                s.student_id,
                s.full_name,
                s.edu_email,
                COUNT(a.attendance_id) as total_classes,
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended,
                ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                      NULLIF(COUNT(a.attendance_id), 0), 2) as attendance_percentage,
                MAX(a.attendance_date) as last_attendance
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id 
                AND a.course_id = %s
                {date_filter}
            WHERE s.class_group = %s
            GROUP BY s.student_id, s.full_name, s.edu_email
            ORDER BY s.student_id
        """
        
        if date_filter:
            query = query.format(date_filter=f"AND a.attendance_date {date_filter}")
            cursor.execute(query, (course_id, class_group))
        else:
            query = query.format(date_filter="")
            cursor.execute(query, (course_id, class_group))
        
        attendance = []
        for row in cursor.fetchall():
            attendance.append({
                'student_id': row[0],
                'full_name': row[1],
                'email': row[2],
                'total_classes': row[3] or 0,
                'attended': row[4] or 0,
                'attendance_percentage': row[5] or 0,
                'last_attendance': row[6].strftime('%Y-%m-%d') if row[6] else 'Never'
            })
        
        cursor.close()
        return attendance
    finally:
        release_db_connection(conn)

def generate_qr_code(course_id, class_group, duration_minutes=15):
    conn = get_db_connection()
    if not conn:
        return None, "Database error"
    
    try:
        # Get course details
        cursor = conn.cursor()
        cursor.execute("SELECT course_code, course_name FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        
        if not course:
            return None, "Course not found"
        
        course_code = course[0]
        course_name = course[1]
        
        # Create QR data
        valid_from = datetime.now()
        valid_until = valid_from + timedelta(minutes=duration_minutes)
        
        qr_data = json.dumps({
            'course_code': course_code,
            'course_name': course_name,
            'class_group': class_group,
            'valid_from': valid_from.isoformat(),
            'valid_until': valid_until.isoformat(),
            'teacher_id': session.get('teacher_id')
        }, separators=(',', ':'))  # Minified JSON
        
        # Store QR code in database
        cursor.execute("""
            INSERT INTO qr_codes 
            (qr_data, course_id, class_group, valid_from, valid_until, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING qr_id
        """, (qr_data, course_id, class_group, valid_from, valid_until, True))
        
        qr_id = cursor.fetchone()[0]
        conn.commit()
        
        # Generate QR image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'qr_id': qr_id,
            'qr_data': qr_data,
            'qr_image': qr_base64,
            'course_code': course_code,
            'course_name': course_name,
            'class_group': class_group,
            'valid_from': valid_from.strftime('%Y-%m-%d %H:%M:%S'),
            'valid_until': valid_until.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': duration_minutes
        }, None
        
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        release_db_connection(conn)

def get_attendance_report(teacher_id, report_type='daily', start_date=None, end_date=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        if report_type == 'daily':
            cursor.execute("""
                SELECT 
                    a.attendance_date,
                    c.course_code,
                    c.course_name,
                    t.class_group,
                    COUNT(a.attendance_id) as total_attendance,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                          NULLIF(COUNT(a.attendance_id), 0), 2) as attendance_rate
                FROM attendance a
                JOIN courses c ON a.course_id = c.course_id
                JOIN timetable t ON a.course_id = t.course_id
                WHERE t.teacher_id = %s
                GROUP BY a.attendance_date, c.course_code, c.course_name, t.class_group
                ORDER BY a.attendance_date DESC
                LIMIT 30
            """, (teacher_id,))
            
        elif report_type == 'weekly':
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('week', a.attendance_date) as week_start,
                    c.course_code,
                    c.course_name,
                    t.class_group,
                    COUNT(a.attendance_id) as total_attendance,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                          NULLIF(COUNT(a.attendance_id), 0), 2) as attendance_rate
                FROM attendance a
                JOIN courses c ON a.course_id = c.course_id
                JOIN timetable t ON a.course_id = t.course_id
                WHERE t.teacher_id = %s
                GROUP BY DATE_TRUNC('week', a.attendance_date), c.course_code, c.course_name, t.class_group
                ORDER BY week_start DESC
                LIMIT 12
            """, (teacher_id,))
            
        elif report_type == 'monthly':
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('month', a.attendance_date) as month_start,
                    c.course_code,
                    c.course_name,
                    t.class_group,
                    COUNT(a.attendance_id) as total_attendance,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                          NULLIF(COUNT(a.attendance_id), 0), 2) as attendance_rate
                FROM attendance a
                JOIN courses c ON a.course_id = c.course_id
                JOIN timetable t ON a.course_id = t.course_id
                WHERE t.teacher_id = %s
                GROUP BY DATE_TRUNC('month', a.attendance_date), c.course_code, c.course_name, t.class_group
                ORDER BY month_start DESC
                LIMIT 6
            """, (teacher_id,))
        
        reports = []
        for row in cursor.fetchall():
            if report_type == 'daily':
                period = row[0].strftime('%Y-%m-%d')
            elif report_type == 'weekly':
                period = f"Week of {row[0].strftime('%b %d, %Y')}"
            else:  # monthly
                period = row[0].strftime('%B %Y')
            
            reports.append({
                'period': period,
                'course_code': row[1],
                'course_name': row[2],
                'class_group': row[3],
                'total_attendance': row[4] or 0,
                'present_count': row[5] or 0,
                'absent_count': (row[4] or 0) - (row[5] or 0),
                'attendance_rate': row[6] or 0
            })
        
        cursor.close()
        return reports
    finally:
        release_db_connection(conn)

@app.route('/')
def teacher_home():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def teacher_login():
    if 'teacher_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not connection_pool:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT teacher_id, full_name, password 
                FROM teachers 
                WHERE email = %s
            """, (email,))
            
            teacher = cursor.fetchone()
            cursor.close()
            
            if teacher and teacher[2] == password:  # Direct password comparison
                session['teacher_id'] = teacher[0]
                session['teacher_name'] = teacher[1]
                session['teacher_email'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            flash('Login error. Please try again.', 'error')
        finally:
            release_db_connection(conn)
    
    return render_template('login.html')

@app.route('/dashboard')
@teacher_login_required
def dashboard():
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    # Get today's schedule
    today_schedule = get_today_schedule(teacher_id)
    
    # Get statistics
    today_stats = get_attendance_stats(teacher_id, 'today')
    weekly_stats = get_attendance_stats(teacher_id, 'week')
    monthly_stats = get_attendance_stats(teacher_id, 'month')
    
    # Get upcoming classes (next 7 days)
    upcoming_classes = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            cursor.execute("""
                SELECT 
                    t.day_of_week,
                    t.start_time,
                    t.end_time,
                    c.course_code,
                    c.course_name,
                    t.class_group,
                    t.room,
                    t.type
                FROM timetable t
                JOIN courses c ON t.course_id = c.course_id
                WHERE t.teacher_id = %s
                ORDER BY 
                    CASE t.day_of_week
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    t.start_time
            """, (teacher_id,))
            
            for row in cursor.fetchall():
                upcoming_classes.append({
                    'day': row[0],
                    'time': f"{row[1].strftime('%H:%M')} - {row[2].strftime('%H:%M')}",
                    'course': f"{row[3]} - {row[4]}",
                    'class_group': row[5],
                    'room': row[6],
                    'type': row[7]
                })
            
            cursor.close()
        finally:
            release_db_connection(conn)
    
    return render_template('dashboard.html',
                         teacher=teacher,
                         today_schedule=today_schedule,
                         today_stats=today_stats,
                         weekly_stats=weekly_stats,
                         monthly_stats=monthly_stats,
                         upcoming_classes=upcoming_classes[:5],  # Limit to 5
                         current_date=datetime.now().strftime('%B %d, %Y'),
                         current_day=datetime.now().strftime('%A'),
                         datetime=datetime)  # Add this line
                            

@app.route('/classes')
@teacher_login_required
def classes():
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    teacher_classes = get_teacher_classes(teacher_id)
    
    # Calculate unique class groups
    unique_class_groups = len(set(class_info['class_group'] for class_info in teacher_classes))
    
    return render_template('classes.html',
                         teacher=teacher,
                         classes=teacher_classes,
                         unique_class_groups=unique_class_groups,
                         datetime=datetime)

@app.route('/attendance/<int:course_id>/<class_group>')
@teacher_login_required
def view_attendance(course_id, class_group):
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    # Get course details
    conn = get_db_connection()
    course_details = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT course_code, course_name 
                FROM courses 
                WHERE course_id = %s
            """, (course_id,))
            course_row = cursor.fetchone()
            if course_row:
                course_details = {
                    'course_code': course_row[0],
                    'course_name': course_row[1]
                }
            cursor.close()
        finally:
            release_db_connection(conn)
    
    if not course_details:
        flash('Course not found', 'error')
        return redirect(url_for('classes'))
    
    # Get attendance data
    attendance_data = get_class_attendance(course_id, class_group)
    
    # Calculate summary statistics
    total_students = len(attendance_data)
    if total_students > 0:
        avg_attendance = sum(student['attendance_percentage'] for student in attendance_data) / total_students
        present_students = sum(1 for student in attendance_data if student['attendance_percentage'] >= 75)
    else:
        avg_attendance = 0
        present_students = 0
    
    return render_template('attendance.html',
                         teacher=teacher,
                         course=course_details,
                         class_group=class_group,
                         attendance_data=attendance_data,
                         total_students=total_students,
                         avg_attendance=round(avg_attendance, 2),
                         present_students=present_students,
                         datetime=datetime)

@app.route('/qr-generator', methods=['GET', 'POST'])
@teacher_login_required
def qr_generator():
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    teacher_classes = get_teacher_classes(teacher_id)
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        class_group = request.form.get('class_group')
        duration = int(request.form.get('duration', 15))
        
        if not course_id or not class_group:
            flash('Please select a course and class group', 'error')
            return render_template('qr_generator.html',
                                 teacher=teacher,
                                 classes=teacher_classes)
        
        qr_data, error = generate_qr_code(int(course_id), class_group, duration)
        
        if error:
            flash(f'Error generating QR code: {error}', 'error')
            return render_template('qr_generator.html',
                                 teacher=teacher,
                                 classes=teacher_classes)
        
        return render_template('qr_generator.html',
                             teacher=teacher,
                             classes=teacher_classes,
                             qr_data=qr_data,
                             generated=True,
                             datetime=datetime)
    
    return render_template('qr_generator.html',
                         teacher=teacher,
                         classes=teacher_classes,
                         datetime=datetime)

@app.route('/reports')
@teacher_login_required
def reports():
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    report_type = request.args.get('type', 'daily')
    
    attendance_reports = get_attendance_report(teacher_id, report_type)
    
    # Get summary statistics for the selected period
    if report_type == 'daily':
        period_stats = get_attendance_stats(teacher_id, 'today')
    elif report_type == 'weekly':
        period_stats = get_attendance_stats(teacher_id, 'week')
    else:  # monthly
        period_stats = get_attendance_stats(teacher_id, 'month')
    
    return render_template('reports.html',
                         teacher=teacher,
                         reports=attendance_reports,
                         report_type=report_type,
                         period_stats=period_stats,
                         datetime=datetime)

@app.route('/profile')
@teacher_login_required
def profile():
    teacher_id = session['teacher_id']
    teacher = get_teacher_by_id(teacher_id)
    
    if not teacher:
        session.clear()
        return redirect(url_for('teacher_login'))
    
    # Get teacher statistics
    today_stats = get_attendance_stats(teacher_id, 'today')
    total_classes = len(get_teacher_classes(teacher_id))
    
    return render_template('profile.html',
                         teacher=teacher,
                         today_stats=today_stats,
                         total_classes=total_classes,
                         datetime=datetime)

@app.route('/logout')
@teacher_login_required
def teacher_logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('teacher_login'))

@app.route('/api/get-attendance-details')
@teacher_login_required
def get_attendance_details():
    course_id = request.args.get('course_id')
    class_group = request.args.get('class_group')
    period = request.args.get('period', 'all')  # all, today, week, month
    
    if not course_id or not class_group:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Determine date filter
    date_filter = None
    if period == 'today':
        date_filter = f"= '{datetime.now().date()}'"
    elif period == 'week':
        week_ago = (datetime.now() - timedelta(days=7)).date()
        date_filter = f">= '{week_ago}'"
    elif period == 'month':
        first_of_month = datetime.now().replace(day=1).date()
        date_filter = f">= '{first_of_month}'"
    
    attendance_data = get_class_attendance(int(course_id), class_group, date_filter)
    
    return jsonify({
        'success': True,
        'attendance_data': attendance_data
    })

@app.route('/api/update-attendance', methods=['POST'])
@teacher_login_required
def update_attendance():
    try:
        data = request.json
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        date = data.get('date')
        status = data.get('status')
        
        if not all([student_id, course_id, date, status]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Check if attendance record exists
            cursor.execute("""
                SELECT attendance_id FROM attendance 
                WHERE student_id = %s 
                AND course_id = %s 
                AND attendance_date = %s
            """, (student_id, course_id, date))
            
            attendance_record = cursor.fetchone()
            
            if attendance_record:
                # Update existing record
                cursor.execute("""
                    UPDATE attendance 
                    SET status = %s, 
                        created_at = CURRENT_TIMESTAMP
                    WHERE attendance_id = %s
                """, (status, attendance_record[0]))
            else:
                # Create new record
                cursor.execute("""
                    INSERT INTO attendance 
                    (student_id, course_id, attendance_date, attendance_time, status, method)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (student_id, course_id, date, datetime.now().time(), status, 'Manual'))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Attendance updated to {status}'
            })
            
        finally:
            release_db_connection(conn)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/export-report')
@teacher_login_required
def export_report():
    report_type = request.args.get('type', 'daily')
    format_type = request.args.get('format', 'csv')
    
    teacher_id = session['teacher_id']
    reports = get_attendance_report(teacher_id, report_type)
    
    if format_type == 'csv':
        # Create CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Period', 'Course Code', 'Course Name', 'Class Group', 
                        'Total Attendance', 'Present', 'Absent', 'Attendance Rate (%)'])
        
        # Write data
        for report in reports:
            writer.writerow([
                report['period'],
                report['course_code'],
                report['course_name'],
                report['class_group'],
                report['total_attendance'],
                report['present_count'],
                report['absent_count'],
                f"{report['attendance_rate']}%"
            ])
        
        output.seek(0)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=attendance_report_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    
    elif format_type == 'json':
        return jsonify(reports)
    
    else:
        return jsonify({'error': 'Invalid format'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)