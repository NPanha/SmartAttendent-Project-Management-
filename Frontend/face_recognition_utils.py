# face_recognition_utils.py
import cv2
import numpy as np
import pickle
import os
from datetime import datetime

class FaceRecognizer:
    def __init__(self):
        self.recognizer = None
        self.label_encoder = None
        self.face_cascade = None
        
    def load_model(self):
        """Load the trained face recognition model"""
        try:
            model_path = os.path.join('model', 'face_model.yml')
            label_path = os.path.join('model', 'label_encoder.pkl')
            
            if not os.path.exists(model_path) or not os.path.exists(label_path):
                print("Model files not found")
                return False
            
            # Load recognizer
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(model_path)
            
            # Load label encoder
            with open(label_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            # Load face cascade
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            print(f"Model loaded successfully! Students: {len(self.label_encoder)}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def detect_faces(self, image):
        """Detect faces in an image"""
        if self.face_cascade is None:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Equalize histogram
        gray = cv2.equalizeHist(gray)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(60, 60)
        )
        
        return faces, gray
    
    def preprocess_face(self, face_roi):
        """Preprocess face ROI for recognition"""
        # Resize
        face_roi = cv2.resize(face_roi, (100, 100))
        
        # Equalize histogram
        face_roi = cv2.equalizeHist(face_roi)
        
        # Apply Gaussian blur
        face_roi = cv2.GaussianBlur(face_roi, (3, 3), 0)
        
        return face_roi
    
    def recognize_face(self, image):
        """Recognize face in image"""
        if self.recognizer is None or self.label_encoder is None:
            return None, 0
        
        # Detect faces
        faces, gray = self.detect_faces(image)
        
        if len(faces) == 0:
            return None, 0
        
        # Take the largest face (assuming it's the main subject)
        faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
        (x, y, w, h) = faces[0]
        
        # Extract and preprocess face
        face_roi = gray[y:y+h, x:x+w]
        processed_face = self.preprocess_face(face_roi)
        
        # Predict
        label, confidence = self.recognizer.predict(processed_face)
        
        # Convert confidence to percentage (lower is better in LBPH)
        confidence_percent = max(0, 100 - min(confidence, 100))
        
        # Get student name
        student_name = self.label_encoder.get(label, "Unknown")
        
        return student_name, confidence_percent
    
    def verify_student(self, image, student_name):
        """Verify if the face belongs to a specific student"""
        recognized_name, confidence = self.recognize_face(image)
        
        if recognized_name == student_name and confidence > 50:  # Threshold
            return True, confidence
        return False, confidence

# Global recognizer instance
face_recognizer = FaceRecognizer()

def init_face_recognition():
    """Initialize face recognition system"""
    return face_recognizer.load_model()