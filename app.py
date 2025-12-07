from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
app.config['SESSION_TYPE'] = 'filesystem'

# Mock database (replace with PostgreSQL in production)
users = {
    'e20210134': {
        'password': 'password123',
        'name': 'NGRON Panha',
        'email': 'panha.ngron@student.edu',
        'phone': '+855 123 456 789',
        'dob': '2002-05-15',
        'gender': 'Male',
        'address': 'Phnom Penh, Cambodia',
        'student_id': 'e20210134',
        'program': 'Computer Science',
        'batch': '2021',
        'semester': '6',
        'academic_year': '2025-2026',
        'courses': ['Advanced Programming', 'Web Development', 'Database Systems', 'AI Fundamentals']
    }
}

# Mock timetable data based on the provided image
def get_timetable():
    return {
        'Monday': [
            {'time': '9:10-10:05', 'course': 'Paris Restaurant Bar', 'instructor': 'Separate', 'room': '1000', 'attended': True, 'upcoming': False},
            {'time': '10:10-11:05', 'course': 'Paris Restaurant Bar', 'instructor': 'Separate', 'room': '1000', 'attended': True, 'upcoming': False},
            {'time': '15:10-16:05', 'course': 'Nada Circular Restaurant', 'instructor': 'Billy', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Tuesday': [
            {'time': '7:00-7:55', 'course': 'EDA', 'instructor': 'Dr. HAS Sabine', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '8:00-8:55', 'course': 'EDA', 'instructor': 'Dr. HAS Sabine', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '9:10-10:05', 'course': 'CUP', 'instructor': 'Mr. TRADET Saparte', 'room': 'Separate', 'attended': True, 'upcoming': False},
            {'time': '10:10-11:05', 'course': 'CUP', 'instructor': 'Mr. TRADET Saparte', 'room': 'Separate', 'attended': True, 'upcoming': False},
            {'time': '15:10-16:05', 'course': 'ASU', 'instructor': 'TBA', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Wednesday': [
            {'time': '7:00-7:55', 'course': 'TPA', 'instructor': 'Dr. Still Tammy', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '8:00-8:55', 'course': 'TPA', 'instructor': 'Dr. Still Tammy', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '9:10-10:05', 'course': 'TPA', 'instructor': 'Dr. Still Tammy', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '10:10-11:05', 'course': 'TPA', 'instructor': 'Dr. Still Tammy', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Thursday': [
            {'time': '7:00-7:55', 'course': 'Advanced Programming for KB', 'instructor': 'Mr. KHGAV Head', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '8:00-8:55', 'course': 'Advanced Programming for KB', 'instructor': 'Mr. KHGAV Head', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '9:10-10:05', 'course': 'Intermediate WB', 'instructor': 'Mr. KHGAV Head', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '12:00-12:55', 'course': 'EDA', 'instructor': 'Dr. HAS Sabine', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '14:00-14:55', 'course': 'EDA', 'instructor': 'Dr. HAS Sabine', 'room': 'TBA', 'attended': False, 'upcoming': True},
            {'time': '15:10-16:05', 'course': 'Advanced Programming for KB', 'instructor': 'Dr HAS Sabine & Mr. KHGAV Head', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Friday': [
            {'time': '7:00-7:55', 'course': 'RLP', 'instructor': 'Dr. JOHN Tammy', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '8:00-8:55', 'course': 'RLP', 'instructor': 'Dr. JOHN Tammy', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '9:10-10:05', 'course': 'Centre Cup', 'instructor': 'Mr. TRADET Saparte', 'room': 'Separate', 'attended': True, 'upcoming': False},
            {'time': '10:10-11:05', 'course': 'English/English and Centre Expanding Film', 'instructor': 'TBA', 'room': 'TBA', 'attended': True, 'upcoming': False},
            {'time': '12:00-12:55', 'course': 'Centre Cup', 'instructor': 'Mr. TRADET Saparte', 'room': 'Separate', 'attended': False, 'upcoming': True},
            {'time': '14:00-14:55', 'course': 'Intermediate WB', 'instructor': 'Mr. KHGAV Head', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Saturday': [
            {'time': '9:10-10:05', 'course': 'ASU', 'instructor': 'TBA', 'room': 'TBA', 'attended': False, 'upcoming': True}
        ],
        'Sunday': []
    }

def get_current_day_classes():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day = datetime.now().strftime('%A')
    return get_timetable().get(current_day, [])

def get_today_attendance_stats():
    today_classes = get_current_day_classes()
    attended = sum(1 for c in today_classes if c['attended'])
    total = len(today_classes)
    return {
        'today_attendance': int((attended / total * 100)) if total > 0 else 0,
        'overall_attendance': 92,  # Mock data
        'classes_attended': 15,    # Mock data
        'total_classes': 18,       # Mock data
        'classes_missed': 3,       # Mock data
        'monthly_attendance': 88   # Mock data
    }

def get_attendance_records():
    # Mock attendance records
    records = []
    days_ago = 30
    
    for i in range(days_ago):
        date = datetime.now() - timedelta(days=i)
        day_name = date.strftime('%A')
        classes = get_timetable().get(day_name, [])
        
        for class_info in classes:
            record_date = date.strftime('%Y-%m-%d')
            status = 'Present' if class_info['attended'] else 'Absent'
            if i == 0 and not class_info['attended'] and class_info['upcoming']:
                status = 'Pending'
            elif i == 1 and not class_info['attended']:
                status = 'Late'
            
            records.append({
                'date': record_date,
                'course': class_info['course'],
                'time': class_info['time'],
                'instructor': class_info['instructor'],
                'status': status,
                'method': 'QR Code'
            })
    
    return sorted(records, key=lambda x: x['date'], reverse=True)[:50]

@app.route('/')
def home():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    stats = get_today_attendance_stats()
    today_classes = get_current_day_classes()
    
    return render_template('home.html',
                         stats=stats,
                         today_classes=today_classes,
                         today_date=datetime.now().strftime('%B %d, %Y'))

@app.route('/scan-qr')
def scan_qr():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    today_classes = get_current_day_classes()
    current_time = datetime.now().time()
    current_class = None
    
    for class_info in today_classes:
        if not class_info['attended'] and class_info['upcoming']:
            current_class = class_info
            break
    
    return render_template('scanqr.html',
                         current_class=current_class,
                         today_classes=today_classes)

@app.route('/my-attendance')
def my_attendance():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    stats = get_today_attendance_stats()
    records = get_attendance_records()
    courses = list(set(r['course'] for r in records))
    
    return render_template('myattendance.html',
                         stats=stats,
                         attendance_records=records,
                         courses=courses)

@app.route('/timetable')
def timetable():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    timetable_data = get_timetable()
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
    
    # Mock class statistics
    class_stats = [
        {'course': 'Advanced Programming', 'attendance': 95, 'attended': 19, 'total': 20},
        {'course': 'Web Development', 'attendance': 88, 'attended': 22, 'total': 25},
        {'course': 'Database Systems', 'attendance': 92, 'attended': 23, 'total': 25},
        {'course': 'AI Fundamentals', 'attendance': 85, 'attended': 17, 'total': 20}
    ]
    
    return render_template('timetable.html',
                         days=days,
                         class_stats=class_stats,
                         current_week_number=today.isocalendar()[1],
                         current_week_range=f"{start_of_week.strftime('%b %d')} - {(start_of_week + timedelta(days=6)).strftime('%b %d')}",
                         upcoming_classes_count=sum(1 for day in timetable_data.values() for c in day if c['upcoming']),
                         completed_classes_count=sum(1 for day in timetable_data.values() for c in day if c['attended']),
                         total_attended=sum(stat['attended'] for stat in class_stats),
                         total_upcoming=sum(1 for day in timetable_data.values() for c in day if c['upcoming']),
                         deadlines=[
                             {'title': 'Final Project Submission', 'course': 'Advanced Programming', 'due_date': '2024-01-15', 'priority': 'high'},
                             {'title': 'Web App Deployment', 'course': 'Web Development', 'due_date': '2024-01-10', 'priority': 'medium'},
                             {'title': 'Database Design', 'course': 'Database Systems', 'due_date': '2024-01-05', 'priority': 'low'}
                         ])

@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    student = users.get(student_id, {})
    
    stats = get_today_attendance_stats()
    
    return render_template('profile.html',
                         student=student,
                         stats=stats,
                         academic={
                             'program': student.get('program', 'Computer Science'),
                             'batch': student.get('batch', '2021'),
                             'semester': student.get('semester', '6'),
                             'academic_year': student.get('academic_year', '2025-2026'),
                             'courses': student.get('courses', [])
                         },
                         last_login=datetime.now().strftime('%Y-%m-%d %H:%M'),
                         account_created='2021-09-01')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        user = users.get(student_id)
        
        if user and user['password'] == password:
            session['student_id'] = student_id
            session['student_name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid student ID or password', 'error')
    
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
        qr_data = data.get('qrData')
        student_id = session['student_id']
        
        # Process attendance marking
        # In real app, verify QR validity, check class timing, update database
        
        return jsonify({
            'success': True,
            'message': 'Attendance marked successfully',
            'timestamp': datetime.now().isoformat(),
            'student_id': student_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)