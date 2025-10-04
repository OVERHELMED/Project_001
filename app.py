from flask import Flask, render_template, jsonify, request, Response
import cv2
import numpy as np
import mediapipe as mp
import pickle
import threading
import time
import webbrowser
import os

app = Flask(__name__)

# Load the trained model
try:
    model_dict = pickle.load(open('./model.p', 'rb'))
    model = model_dict['model']
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Labels dictionary for A-Z
labels_dict = {i: chr(65 + i) for i in range(26)}

# Global variables for camera
camera = None
hands_detector = None
frame_lock = threading.Lock()
current_prediction = {"letter": "?", "confidence": 0}

def init_camera():
    """Initialize camera and MediaPipe hands detector"""
    global camera, hands_detector
    
    if camera is None:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            print("❌ Error: Could not open camera")
            return False
    
    if hands_detector is None:
        hands_detector = mp_hands.Hands(
            static_image_mode=False, 
            min_detection_confidence=0.3, 
            min_tracking_confidence=0.3
        )
    
    return True

def process_frame(frame):
    """Process frame for hand detection and prediction"""
    global current_prediction
    
    if model is None:
        return frame, {"letter": "?", "confidence": 0, "status": "Model not loaded"}
    
    try:
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = hands_detector.process(frame_rgb)

        # Add instruction text
        cv2.putText(frame, "Make Hand Gestures - Real-time Detection", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

            # Process first hand for prediction
            hand_landmarks = results.multi_hand_landmarks[0]
            x_, y_, data_aux = [], [], []

            for lm in hand_landmarks.landmark:
                x_.append(lm.x)
                y_.append(lm.y)

            for lm in hand_landmarks.landmark:
                data_aux.append(lm.x - min(x_))
                data_aux.append(lm.y - min(y_))

            # Ensure correct feature vector size
            required_length = model.n_features_in_
            if len(data_aux) < required_length:
                data_aux.extend([0] * (required_length - len(data_aux)))
            elif len(data_aux) > required_length:
                data_aux = data_aux[:required_length]

            data_aux = np.array(data_aux).reshape(1, -1)

            # Make prediction
            prediction = model.predict(data_aux)
            predicted_character = labels_dict.get(int(prediction[0]), "?")
            
            # Get confidence score
            confidence_scores = model.predict_proba(data_aux)[0]
            confidence = max(confidence_scores) * 100

            # Draw bounding box and prediction
            x1, y1 = int(min(x_) * W) - 20, int(min(y_) * H) - 20
            x2, y2 = int(max(x_) * W) + 20, int(max(y_) * H) + 20

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(frame, f"Letter: {predicted_character}", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, f"Confidence: {confidence:.1f}%", (x1, y2 + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            
            # Update current prediction
            with frame_lock:
                current_prediction = {
                    "letter": predicted_character,
                    "confidence": round(confidence, 1),
                    "status": "success"
                }
        else:
            cv2.putText(frame, "No hand detected", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            with frame_lock:
                current_prediction = {
                    "letter": "?",
                    "confidence": 0,
                    "status": "No hand detected"
                }

        return frame, current_prediction
        
    except Exception as e:
        return frame, {"letter": "?", "confidence": 0, "status": f"Error: {str(e)}"}

def generate_frames():
    """Generate frames for video streaming"""
    if not init_camera():
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Process frame
        processed_frame, prediction = process_frame(frame)
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        
        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.03)  # ~30 FPS

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_prediction')
def get_prediction():
    """Get current prediction data"""
    with frame_lock:
        return jsonify(current_prediction)

@app.route('/start_camera')
def start_camera():
    """Initialize camera"""
    if init_camera():
        return jsonify({'status': 'success', 'message': 'Camera initialized'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to initialize camera'}), 500

@app.route('/stop_camera')
def stop_camera():
    """Stop camera"""
    global camera, hands_detector
    if camera:
        camera.release()
        camera = None
    if hands_detector:
        hands_detector.close()
        hands_detector = None
    return jsonify({'status': 'success', 'message': 'Camera stopped'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'model_loaded': model is not None,
        'camera_active': camera is not None and camera.isOpened()
    })

def open_browser():
    """Open browser after a short delay to ensure Flask is running"""
    time.sleep(1.5)  # Wait for Flask to start
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("🎯 Starting Real-time Hand Sign Detection Web App...")
    print("📋 Features:")
    print("   • Real-time camera feed")
    print("   • Live hand gesture detection")
    print("   • Alphabet letter prediction (A-Z)")
    print("   • Confidence scores")
    print("=" * 50)
    print("🌐 Opening browser automatically...")
    
    # Start browser opening in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
