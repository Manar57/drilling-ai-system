import os
import time
import cv2
import numpy as np
import tensorflow as tf

from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

import database as db

# ===============================
# CONFIGURATION
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'lithoai-secret-key-2025'
CORS(app, supports_credentials=True)

# Initialize database
db.init_db()

# Load model
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'rock_classifier.h5')
model = tf.keras.models.load_model(MODEL_PATH)

CLASS_NAMES = ['limestone', 'sandstone', 'shale']
IMG_SIZE = 224

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ===============================
# Helper Functions
# ===============================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))
    img_normalized = img_resized.astype(np.float32) / 255.0
    return np.expand_dims(img_normalized, axis=0)


def get_geological_properties(class_name):
    properties = {
        'limestone': {
            'color': 'Light Gray / Beige',
            'grainSize': 'Fine to Medium',
            'angularity': 'Sub-angular',
            'description': 'Carbonate sedimentary rock composed mainly of calcite.'
        },
        'sandstone': {
            'color': 'Tan / Light Brown',
            'grainSize': 'Medium',
            'angularity': 'Sub-rounded',
            'description': 'Clastic sedimentary rock composed mainly of sand-sized minerals.'
        },
        'shale': {
            'color': 'Dark Gray / Black',
            'grainSize': 'Very Fine',
            'angularity': 'Irregular',
            'description': 'Fine-grained clastic rock rich in clay minerals.'
        }
    }
    return properties.get(class_name, {
        'color': 'Unknown',
        'grainSize': 'Unknown',
        'angularity': 'Unknown',
        'description': 'Lithology unclear based on image.'
    })


def is_logged_in():
    return 'user_id' in session and 'username' in session


# ===============================
# PAGE ROUTES
# ===============================
@app.route('/')
def serve_login():
    return send_file(os.path.join(BASE_DIR, 'login.html'))


@app.route('/app')
def serve_app():
    if not is_logged_in():
        return send_file(os.path.join(BASE_DIR, 'login.html'))
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/script.js')
def serve_script():
    return send_file(os.path.join(BASE_DIR, 'script.js'))


@app.route('/style.css')
def serve_style():
    return send_file(os.path.join(BASE_DIR, 'style.css'))


# ===============================
# AUTHENTICATION API
# ===============================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    if len(password) < 4:
        return jsonify({'success': False, 'error': 'Password must be at least 4 characters'}), 400

    user_id = db.add_user(username, email, password)
    if user_id:
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Account created successfully'
        })

    return jsonify({'success': False, 'error': 'Username or email already exists'}), 400


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400

    user = db.verify_user(username, password)
    if not user:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    session['user_id'] = user[0]
    session['username'] = user[1]

    return jsonify({
        'success': True,
        'user_id': user[0],
        'username': user[1]
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    if not is_logged_in():
        return jsonify({'authenticated': False})

    user = db.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'authenticated': False})

    return jsonify({
        'authenticated': True,
        'user_id': user[0],
        'username': user[1]
    })


@app.route('/api/user_stats', methods=['GET'])
def user_stats():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    stats = db.get_user_stats(session['user_id'])
    return jsonify({'success': True, 'stats': stats})


@app.route('/api/user_history', methods=['GET'])
def user_history():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    history = db.get_user_history(session['user_id'])
    return jsonify({'success': True, 'history': history})


@app.route('/api/export_user_data', methods=['GET'])
def export_user_data():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = db.get_all_user_data(session['user_id'])
    return jsonify({'success': True, 'data': data})


@app.route('/api/save_classification', methods=['POST'])
def save_classification():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json(silent=True) or {}

    db.save_classification(session['user_id'], session['username'], data)
    return jsonify({'success': True})


# ===============================
# PREDICTION API
# ===============================
@app.route('/predict', methods=['POST'])
def predict():
    if not is_logged_in():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image file'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No image selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        input_tensor = preprocess_image(filepath)
        if input_tensor is None:
            return jsonify({'success': False, 'error': 'Could not read image'}), 400

        predictions = model.predict(input_tensor, verbose=0)[0]
        predicted_idx = int(np.argmax(predictions))
        predicted_class = CLASS_NAMES[predicted_idx]
        confidence = float(predictions[predicted_idx] * 100)

        probabilities = []
        for i, class_name in enumerate(CLASS_NAMES):
            probabilities.append({
                'name': class_name.capitalize(),
                'value': round(float(predictions[i] * 100), 1)
            })

        probabilities.sort(key=lambda x: x['value'], reverse=True)

        props = get_geological_properties(predicted_class)

        depth = request.form.get('depth', 'N/A')
        wob = request.form.get('wob', 'N/A')
        rop = request.form.get('rop', 'N/A')

        response = {
            'success': True,
            'rockType': predicted_class.capitalize(),
            'confidence': round(confidence, 1),
            'color': props['color'],
            'grainSize': props['grainSize'],
            'angularity': props['angularity'],
            'description': props['description'],
            'probabilities': probabilities,
            'depth': depth,
            'wob': wob,
            'rop': rop
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_loaded': True})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)