from flask import Flask, render_template, jsonify, request
import base64
import cv2
import numpy as np
import mediapipe as mp
import pickle
import io
from PIL import Image

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

def process_image(image_data):
    """Process uploaded image and return prediction"""
    if model is None:
        return None, "Model not loaded"
    
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Initialize MediaPipe hands
        with mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3) as hands:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)
            
            if results.multi_hand_landmarks:
                # Process first detected hand
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
                
                return predicted_character, confidence
            else:
                return None, "No hand detected"
                
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload and prediction"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image provided'}), 400
        
        prediction, confidence = process_image(image_data)
        
        if prediction:
            return jsonify({
                'prediction': prediction,
                'confidence': round(confidence, 2),
                'status': 'success'
            })
        else:
            return jsonify({
                'error': confidence,
                'status': 'error'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model_loaded': model is not None})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
