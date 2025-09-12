import pickle
import cv2
import mediapipe as mp
import numpy as np
import sys
import time

# Load trained model
print("Loading model...")
model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']
print("✅ Model loaded!")

# Initialize camera
print("Initializing camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Error: Could not open camera")
    sys.exit(1)

# Initialize MediaPipe
print("Initializing MediaPipe...")
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.3, min_tracking_confidence=0.3)

# Labels dictionary
labels_dict = {i: chr(65 + i) for i in range(26)}

print("\n🎯 SYSTEM READY!")
print("=" * 50)
print("📋 INSTRUCTIONS:")
print("   • Make hand gestures in front of the camera")
print("   • The system will detect and show letters (A-Z)")
print("   • Press 'q' to quit")
print("   • Press 'ESC' to quit")
print("=" * 50)

# Create window with specific properties
cv2.namedWindow('Hand Sign Detection', cv2.WINDOW_AUTOSIZE)
cv2.setWindowProperty('Hand Sign Detection', cv2.WND_PROP_TOPMOST, 1)  # Always on top
cv2.resizeWindow('Hand Sign Detection', 800, 600)

print("🔍 Camera window created and set to always stay on top...")
print("   The window should be visible now!")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Error reading camera frame")
        break

    frame_count += 1
    
    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    
    H, W, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process with MediaPipe
    results = hands.process(frame_rgb)

    # Add instruction text
    cv2.putText(frame, "Make Hand Gestures - Press 'q' to quit", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Frame: {frame_count}", 
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
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

        # Draw bounding box and prediction
        x1, y1 = int(min(x_) * W) - 20, int(min(y_) * H) - 20
        x2, y2 = int(max(x_) * W) + 20, int(max(y_) * H) + 20

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(frame, f"Letter: {predicted_character}", (x1, y1 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
    else:
        cv2.putText(frame, "No hand detected", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Show frame
    cv2.imshow('Hand Sign Detection', frame)
    
    # Print status every 100 frames
    if frame_count % 100 == 0:
        print(f"📊 System running... Frame {frame_count}")

    # Exit conditions
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 'q' or ESC
        print("🛑 Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Application closed successfully!")
