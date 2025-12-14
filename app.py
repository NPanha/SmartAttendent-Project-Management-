from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from datetime import datetime, timedelta, time
import psycopg2
from psycopg2 import pool
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Add to existing imports
import cv2
import base64
import numpy as np
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.secret_key = 'smart-attendance-secret-key-2024'
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
        print("Connection pool created successfully")
        # Test connection
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection_pool.putconn(conn)
        print("Database connection successful")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None
    
    

# Initialize face recognizer
def init_face_recognizer():
    try:
        from face_recognition_utils import init_face_recognition
        if init_face_recognition():
            print("Face recognition model loaded successfully")
            return True
        else:
            print("Failed to load face recognition model")
            return False
    except Exception as e:
        print(f"Error initializing face recognizer: {e}")
        return False

# Call this when app starts
face_recognition_ready = init_face_recognizer()


def get_db_connection():
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_db_connection(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)

def get_student_by_id(student_id):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_id, full_name, gender, dob, phone_number, 
                   class_group, edu_email, password, address
            FROM students 
            WHERE student_id = %s
        """, (student_id,))
        student = cursor.fetchone()
        cursor.close()
        
        if student:
            return {
                'student_id': student[0],
                'full_name': student[1],
                'gender': student[2],
                'dob': student[3].strftime('%Y-%m-%d') if student[3] else None,
                'phone_number': student[4],
                'class_group': student[5],
                'edu_email': student[6],
                'password': student[7],
                'address': student[8]
            }
        return None
    finally:
        release_db_connection(conn)

def get_timetable_by_class_group(class_group):
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.day_of_week,
                t.start_time,
                t.end_time,
                c.course_code,
                c.course_name,
                tea.full_name as teacher_name,
                t.room,
                t.type
            FROM timetable t
            JOIN courses c ON t.course_id = c.course_id
            JOIN teachers tea ON t.teacher_id = tea.teacher_id
            WHERE t.class_group = %s
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
        """, (class_group,))
        
        timetable = {}
        for row in cursor.fetchall():
            day = row[0]
            if day not in timetable:
                timetable[day] = []
            
            # Check if this class is today and within time range
            today = datetime.now().strftime('%A')
            current_time = datetime.now().time()
            start_time = row[1]
            end_time = row[2]
            
            # Check attendance status (simplified - would query actual attendance in real app)
            attended = False
            upcoming = False
            
            if day == today:
                if current_time > end_time:
                    # Class already ended
                    attended = True
                elif start_time <= current_time <= end_time:
                    # Class is happening now
                    upcoming = True
            
            timetable[day].append({
                'time': f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}",
                'course': f"{row[3]} - {row[4]}",
                'course_code': row[3],
                'course_name': row[4],
                'instructor': row[5],
                'room': row[6],
                'type': row[7],
                'attended': attended,
                'upcoming': upcoming
            })
        
        cursor.close()
        return timetable
    finally:
        release_db_connection(conn)

def get_current_day_classes(student_class_group):
    current_day = datetime.now().strftime('%A')
    timetable = get_timetable_by_class_group(student_class_group)
    return timetable.get(current_day, [])

def get_today_attendance_stats(student_id):
    conn = get_db_connection()
    if not conn:
        return {
            'today_attendance': 0,
            'overall_attendance': 0,
            'classes_attended': 0,
            'total_classes': 0,
            'classes_missed': 0,
            'monthly_attendance': 0
        }
    
    try:
        cursor = conn.cursor()
        today = datetime.now().date()
        
        # Get today's attendance
        cursor.execute("""
            SELECT 
                COUNT(*) as total_today,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended_today
            FROM attendance 
            WHERE student_id = %s AND attendance_date = %s
        """, (student_id, today))
        
        today_stats = cursor.fetchone()
        total_today = today_stats[0] or 0
        attended_today = today_stats[1] or 0
        
        # Get overall attendance
        cursor.execute("""
            SELECT 
                COUNT(*) as total_overall,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended_overall
            FROM attendance 
            WHERE student_id = %s
        """, (student_id,))
        
        overall_stats = cursor.fetchone()
        total_overall = overall_stats[0] or 0
        attended_overall = overall_stats[1] or 0
        
        # Get this month's attendance
        first_day_of_month = today.replace(day=1)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_month,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended_month
            FROM attendance 
            WHERE student_id = %s AND attendance_date >= %s
        """, (student_id, first_day_of_month))
        
        month_stats = cursor.fetchone()
        total_month = month_stats[0] or 0
        attended_month = month_stats[1] or 0
        
        cursor.close()
        
        return {
            'today_attendance': int((attended_today / total_today * 100)) if total_today > 0 else 0,
            'overall_attendance': int((attended_overall / total_overall * 100)) if total_overall > 0 else 0,
            'classes_attended': attended_overall,
            'total_classes': total_overall,
            'classes_missed': total_overall - attended_overall,
            'monthly_attendance': int((attended_month / total_month * 100)) if total_month > 0 else 0
        }
    finally:
        release_db_connection(conn)

def get_attendance_records(student_id):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                a.attendance_date,
                c.course_code,
                c.course_name,
                a.attendance_time,
                tea.full_name as instructor,
                a.status,
                a.method
            FROM attendance a
            JOIN courses c ON a.course_id = c.course_id
            LEFT JOIN timetable t ON a.course_id = t.course_id
            LEFT JOIN teachers tea ON t.teacher_id = tea.teacher_id
            WHERE a.student_id = %s
            ORDER BY a.attendance_date DESC, a.attendance_time DESC
            LIMIT 50
        """, (student_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'date': row[0].strftime('%Y-%m-%d'),
                'course': f"{row[1]} - {row[2]}",
                'course_code': row[1],
                'course_name': row[2],
                'time': row[3].strftime('%H:%M'),
                'instructor': row[4] or 'N/A',
                'status': row[5],
                'method': row[6]
            })
        
        cursor.close()
        return records
    finally:
        release_db_connection(conn)

def mark_attendance_from_qr(student_id, qr_data):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error"
    
    try:
        # Parse QR data
        try:
            qr_info = json.loads(qr_data)
            print(f"QR Info: {qr_info}")  # Add debugging
            
            # Extract fields with error handling
            course_code = qr_info.get('course_code')
            class_group = qr_info.get('class_group')
            valid_until_str = qr_info.get('valid_until')
            
            if not all([course_code, class_group, valid_until_str]):
                return False, "Invalid QR code format - missing fields"
            
            # Parse valid_until time
            valid_until = datetime.fromisoformat(valid_until_str)
            current_time = datetime.now()
            
            # Check if QR is still valid
            if current_time > valid_until:
                return False, "QR code has expired"
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"QR Parse Error: {e}")
            return False, "Invalid QR code format"
        
        cursor = conn.cursor()
        
        # Get student's class group
        cursor.execute("SELECT class_group FROM students WHERE student_id = %s", (student_id,))
        student_class = cursor.fetchone()
        
        if not student_class:
            return False, "Student not found"
        
        if student_class[0] != class_group:
            return False, "QR code is not for your class group"
        
        # Check if attendance already marked for this class today
        cursor.execute("""
            SELECT 1 FROM attendance a
            JOIN courses c ON a.course_id = c.course_id
            WHERE a.student_id = %s 
            AND a.attendance_date = %s
            AND c.course_code = %s
        """, (student_id, current_time.date(), course_code))
        
        if cursor.fetchone():
            return False, "Attendance already marked for this class today"
        
        # Get course ID
        cursor.execute("SELECT course_id FROM courses WHERE course_code = %s", (course_code,))
        course_row = cursor.fetchone()
        if not course_row:
            return False, "Invalid course"
        
        course_id = course_row[0]
        
        # Verify the QR exists in qr_codes table (teacher system stores it)
        cursor.execute("""
            SELECT 1 FROM qr_codes 
            WHERE course_id = %s 
            AND class_group = %s 
            AND valid_until >= %s
            AND is_active = TRUE
            ORDER BY created_at DESC LIMIT 1
        """, (course_id, class_group, current_time))
        
        if not cursor.fetchone():
            return False, "QR code not authorized"
        
        # Insert attendance record
        cursor.execute("""
            INSERT INTO attendance 
            (student_id, course_id, attendance_date, attendance_time, status, method, qr_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (student_id, course_id, current_time.date(), current_time.time(), 
              'Present', 'QR Code', qr_data))
        
        conn.commit()
        cursor.close()
        return True, "Attendance marked successfully"
        
    except Exception as e:
        conn.rollback()
        print(f"Error marking attendance: {e}")
        return False, str(e)
    finally:
        release_db_connection(conn)
        
        

@app.route('/')
def home():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    stats = get_today_attendance_stats(student_id)
    today_classes = get_current_day_classes(student['class_group'])
    
    return render_template('home.html',
                         stats=stats,
                         today_classes=today_classes,
                         today_date=datetime.now().strftime('%B %d, %Y'),
                         student=student)

@app.route('/scan-qr')
def scan_qr():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    today_classes = get_current_day_classes(student['class_group'])
    current_time = datetime.now().time()
    current_class = None
    
    for class_info in today_classes:
        if class_info['upcoming'] and not class_info['attended']:
            # Parse time from string
            start_str = class_info['time'].split('-')[0]
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_str = class_info['time'].split('-')[1]
            end_time = datetime.strptime(end_str, '%H:%M').time()
            
            if start_time <= current_time <= end_time:
                current_class = class_info
                break
    
    return render_template('scanqr.html',
                         current_class=current_class,
                         today_classes=today_classes,
                         student=student)

@app.route('/my-attendance')
def my_attendance():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    stats = get_today_attendance_stats(student_id)
    records = get_attendance_records(student_id)
    courses = list(set(r['course_code'] for r in records))
    
    return render_template('myattendance.html',
                         stats=stats,
                         attendance_records=records,
                         courses=courses,
                         student=student)

@app.route('/timetable')
def timetable():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    timetable_data = get_timetable_by_class_group(student['class_group'])
    days = []
    
    # Get current week days
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = day_date.strftime('%A')
        is_today = i == today.weekday()
        
        days.append({
            'name': day_name,
            'short': day_name[:3],
            'date': day_date.strftime('%d/%m'),
            'active': is_today,
            'classes': timetable_data.get(day_name, [])
        })
    
    # Get class statistics
    conn = get_db_connection()
    class_stats = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.course_code,
                    c.course_name,
                    COUNT(a.attendance_id) as total_classes,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended
                FROM courses c
                LEFT JOIN attendance a ON c.course_id = a.course_id AND a.student_id = %s
                GROUP BY c.course_id, c.course_code, c.course_name
            """, (student_id,))
            
            for row in cursor.fetchall():
                total = row[2] or 0
                attended = row[3] or 0
                attendance_pct = int((attended / total * 100)) if total > 0 else 0
                
                class_stats.append({
                    'course': f"{row[0]} - {row[1]}",
                    'course_code': row[0],
                    'attendance': attendance_pct,
                    'attended': attended,
                    'total': total
                })
            
            cursor.close()
        finally:
            release_db_connection(conn)
    
    return render_template('timetable.html',
                         days=days,
                         class_stats=class_stats,
                         student=student,
                         current_week_number=today.isocalendar()[1],
                         current_week_range=f"{start_of_week.strftime('%b %d')} - {(start_of_week + timedelta(days=6)).strftime('%b %d')}",
                         upcoming_classes_count=sum(1 for day in timetable_data.values() for c in day if c['upcoming']),
                         completed_classes_count=sum(1 for day in timetable_data.values() for c in day if c['attended']),
                         total_attended=sum(stat['attended'] for stat in class_stats),
                         total_upcoming=sum(1 for day in timetable_data.values() for c in day if c['upcoming']),
                         deadlines=[])  # Empty for now

@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    stats = get_today_attendance_stats(student_id)
    
    # Get academic info
    academic = {
        'program': 'Applied Mathematics and Statistics',
        'batch': '2021',
        'semester': '5',
        'academic_year': '2024-2025',
        'courses': ['Project Management', 'EDA', 'NLP', 'TSA', 'APDS', 'IWR', 'EWC', 'MIP']
    }
    
    return render_template('profile.html',
                         student=student,
                         stats=stats,
                         academic=academic,
                         last_login=datetime.now().strftime('%Y-%m-%d %H:%M'),
                         account_created='2021-09-01')

@app.route('/face-recognition')
def face_recognition():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for('login'))
    
    return render_template('face_recognition.html',
                         student=student)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
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
                SELECT student_id, full_name, password, class_group 
                FROM students 
                WHERE student_id = %s
            """, (student_id,))
            
            user = cursor.fetchone()
            cursor.close()
            
            if user and user[2] == password:  # Direct password comparison (not hashed as requested)
                session['student_id'] = user[0]
                session['student_name'] = user[1]
                session['class_group'] = user[3]
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid student ID or password', 'error')
                
        except Exception as e:
            flash('Login error. Please try again.', 'error')
        finally:
            release_db_connection(conn)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        qr_data_str = data.get('qrData')
        student_id = session['student_id']
        
        if not qr_data_str:
            return jsonify({'success': False, 'message': 'No QR data provided'}), 400
        
        # Parse QR data
        try:
            qr_info = json.loads(qr_data_str)
            print(f"QR Info received: {qr_info}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
        
        # Call the existing function
        success, message = mark_attendance_from_qr(student_id, qr_data_str)  # Pass as string
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'student_id': student_id
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        print(f"Error in mark_attendance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400
    





@app.route('/api/mark-face-attendance', methods=['POST'])
def mark_face_attendance():
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        student_id = session['student_id']
        student_name = session.get('student_name')
        
        # Get image data from request
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
        
        if not face_recognition_ready:
            return jsonify({'success': False, 'message': 'Face recognition system not ready'}), 500
        
        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64,
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image'}), 400
        
        # Recognize face
        from face_recognition_utils import face_recognizer
        recognized_name, confidence = face_recognizer.recognize_face(image)
        
        print(f"Recognized: {recognized_name}, Confidence: {confidence}%, Expected: {student_name}")
        
        # Verify it's the correct student
        if recognized_name != student_name or confidence < 50:
            return jsonify({
                'success': False, 
                'message': f'Face verification failed. Recognized: {recognized_name} (Confidence: {confidence:.1f}%)'
            }), 400
        
        # If verified, mark attendance
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Get current class based on time
            current_time = datetime.now()
            current_day = current_time.strftime('%A')
            current_time_str = current_time.time()
            
            # Find current class
            cursor.execute("""
                SELECT t.course_id, c.course_code
                FROM timetable t
                JOIN courses c ON t.course_id = c.course_id
                JOIN students s ON t.class_group = s.class_group
                WHERE s.student_id = %s 
                AND t.day_of_week = %s
                AND t.start_time <= %s
                AND t.end_time >= %s
                LIMIT 1
            """, (student_id, current_day, current_time_str, current_time_str))
            
            current_class = cursor.fetchone()
            
            if not current_class:
                return jsonify({'success': False, 'message': 'No active class at this time'}), 400
            
            course_id = current_class[0]
            course_code = current_class[1]
            
            # Check if already marked
            cursor.execute("""
                SELECT 1 FROM attendance 
                WHERE student_id = %s 
                AND course_id = %s 
                AND attendance_date = %s
            """, (student_id, course_id, current_time.date()))
            
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Attendance already marked for this class'}), 400
            
            # Mark attendance
            cursor.execute("""
                INSERT INTO attendance 
                (student_id, course_id, attendance_date, attendance_time, status, method, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (student_id, course_id, current_time.date(), current_time.time(), 
                  'Present', 'Face Recognition', confidence))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Attendance marked for {course_code} via Face Recognition',
                'timestamp': current_time.isoformat(),
                'course': course_code,
                'confidence': confidence,
                'student_name': recognized_name
            })
            
        finally:
            release_db_connection(conn)
            
    except Exception as e:
        print(f"Face recognition error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400
    
    








@app.route('/api/capture-face', methods=['POST'])
def capture_face():
    """Capture face image for verification"""
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image'}), 400
        
        # Detect face
        from face_recognition_utils import face_recognizer
        faces, gray = face_recognizer.detect_faces(image)
        
        face_count = len(faces)
        has_face = face_count > 0
        
        # Calculate confidence (simplified)
        confidence = 0
        if has_face:
            # Use face size as confidence indicator
            (x, y, w, h) = faces[0]
            face_area = w * h
            img_area = image.shape[0] * image.shape[1]
            confidence = min(100, int((face_area / img_area) * 300))
        
        return jsonify({
            'success': True,
            'face_detected': has_face,
            'face_count': face_count,
            'confidence': confidence
        })
        
    except Exception as e:
        print(f"Capture face error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400
    
    
    
    
    
    

@app.route('/api/update-password', methods=['POST'])
def update_password():
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.json
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        student_id = session['student_id']
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        if len(new_password) < 4:
            return jsonify({'success': False, 'message': 'Password must be at least 4 characters'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Verify current password
            cursor.execute("SELECT password FROM students WHERE student_id = %s", (student_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != current_password:
                return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            
            # Update password
            cursor.execute("UPDATE students SET password = %s WHERE student_id = %s", 
                         (new_password, student_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Password updated successfully'})
            
        finally:
            release_db_connection(conn)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)