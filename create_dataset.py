import os
import pickle
import mediapipe as mp
import cv2

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

DATA_DIR = './data'

data = []
labels = []
valid_extensions = ('.jpg', '.jpeg', '.png')

for dir_ in os.listdir(DATA_DIR):
    dir_path = os.path.join(DATA_DIR, dir_)

    if not os.path.isdir(dir_path):  
        continue  # Skip non-directory files like .DS_Store

    for img_path in os.listdir(dir_path):
        if not img_path.lower().endswith(valid_extensions):  
            continue  

        img_full_path = os.path.join(dir_path, img_path)
        
        # Check if file exists
        if not os.path.exists(img_full_path):
            print(f"⚠️ Warning: File not found - {img_full_path}")
            continue

        img = cv2.imread(img_full_path)

        if img is None:
            print(f"⚠️ Warning: Unable to read {img_full_path}. Skipping...")
            continue  # Skip this image and proceed

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Line 29 (Now Safe)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            data_aux = []
            x_ = []
            y_ = []

            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y

                    x_.append(x)
                    y_.append(y)

                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    data_aux.append(x - min(x_))
                    data_aux.append(y - min(y_))

            data.append(data_aux)
            labels.append(int(dir_))

# Save dataset
with open('data.pickle', 'wb') as f:
    pickle.dump({'data': data, 'labels': labels}, f)

print(f"✅ Dataset created: {len(data)} samples.")
