# Smart Attendance System - Teacher Portal

A modern, responsive teacher/admin dashboard for managing student attendance with QR code generation, analytics, and reporting features.

## Features

### Teacher Authentication
- Secure login with school email and password
- Session-based authentication
- Role-based access control

### Dashboard
- Real-time attendance statistics
- Today's class schedule
- Quick overview of attendance rates
- Upcoming classes

### Class Management
- View all assigned classes
- Class-wise student lists
- Attendance tracking per class
- Filter by course and class group

### QR Code Generator
- Generate time-limited QR codes for attendance
- Customizable validity duration (5-60 minutes)
- QR code download and printing options
- Automatic expiration handling

### Attendance Reports
- Daily, weekly, and monthly analytics
- Visual charts and graphs
- Export to CSV and JSON formats
- Filter by date range

### Profile Management
- Teacher profile information
- Password change functionality
- Notification preferences
- Theme customization (light/dark/auto)

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- pip package manager

### Database Setup
1. Create PostgreSQL database:
```sql
CREATE DATABASE smart_attendance;