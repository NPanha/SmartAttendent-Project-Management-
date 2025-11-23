# Smart Attendance System  
A modern, AI-powered web application designed to automate student attendance using **QR Code Scanning**, **Face Recognition**, and (future) **Fingerprint Recognition**.  
This system eliminates traditional manual sign-in methods and ensures fast, accurate, and secure attendance management.

## Features

### **1. Multi-Mode Attendance**
- **QR Code Scanning** – Fast and reliable check-ins using mobile cameras.  
- **Face Recognition (AI)** – Real-time identity verification using the student's face.  
- **Fingerprint Recognition** *(Next Step)* – Hardware-based biometric authentication.

### **2. Smart Admin Panel**
- Register new students  
- Upload face images  
- Auto-generate QR codes  
- View real-time attendance logs (method + timestamp)  
- Manage students & classes  

### **3. Analytics (Upcoming)**
- Daily / Weekly / Monthly attendance reports  
- Export to CSV / Excel  
- Attendance insights & visual charts  

### **4. Security**
- Role-based access control (Admin / Teacher)  
- Face embedding storage (not raw face images)  
- Secure API endpoints  
- Data encryption (future enhancement)

## System Architecture

```text
Frontend (HTML + JS + Bootstrap)
|
|---- QR Scanner (jsQR)
|---- Webcam Face Capture (getUserMedia)
|
Backend (Flask API + Face Recognition)
|
|---- QR Code Generator
|---- Face Encoding & Matching (OpenCV + dlib)
|---- Attendance Logger
|
Database (SQLite / PostgreSQL / MySQL)
|
|---- Students Table
|---- Attendance Table
```

## 🤖 Tech Stack
### **Backend**

| Technology              | Badge                                                                                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Python (Flask)          | ![Python](https://img.shields.io/badge/Python-3776AB?logo=python\&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-000000?logo=flask\&logoColor=white) |
| Face Recognition (dlib) | ![dlib](https://img.shields.io/badge/dlib-A80000?logo=ai\&logoColor=white)                                                                                         |
| OpenCV                  | ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv\&logoColor=white)                                                                                 |

### **Frontend**
| Technology              | Badge                                                                                                                                                                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HTML / CSS / JavaScript | ![HTML](https://img.shields.io/badge/HTML5-E34F26?logo=html5\&logoColor=white) ![CSS](https://img.shields.io/badge/CSS3-1572B6?logo=css3\&logoColor=white) ![JS](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript\&logoColor=black) |
| jsQR (QR decoding)      | ![QR](https://img.shields.io/badge/jsQR-000000?logo=qr-code\&logoColor=white)                                                                                                                                                                     |
| Webcam API              | ![Webcam](https://img.shields.io/badge/Webcam-4A90E2?logo=camera\&logoColor=white)                                                                                                                                                                |

### **Database**
| Technology | Badge                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------------- |
| SQLite     | ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite\&logoColor=white)             |
| PostgreSQL | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql\&logoColor=white) |
| MySQL      | ![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql\&logoColor=white)                |

## Attendance Flow
### **QR Mode:**

Student shows their QR code

Camera scans

System reads student_id

Attendance saved instantly

### **Face Mode:**

Student stands in front of camera

System captures & compares face embedding

If matched → attendance recorded

## Data Privacy

Stores only face embeddings, not raw face images

Supports HTTPS when deployed

Secure API endpoints recommended

Access control recommended for production

## Roadmap (Future Enhancements)

 Fingerprint Scanner Integration

 Admin Authentication / Login

 Student Mobile App (Flutter)

 Attendance Statistics Dashboard

 Export attendance reports

 Live class monitoring with camera feed

## 🤝 Contributing

Pull requests are welcome!
Please open an issue first to discuss improvements.

## 📝 License

This project is licensed under the MIT License — free to use, modify, and distribute.



