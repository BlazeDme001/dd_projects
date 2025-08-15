import base64
import cv2
import numpy as np
import face_recognition
import json
import db_connect as db
from flask import Blueprint, request, jsonify, render_template, Response, session

face_capture_bp = Blueprint("face_capture_bp", __name__, template_folder="templates")

# Route for the capture page
@face_capture_bp.route("/face-capture")
def face_capture_page():
    # Require user to be logged in via session
    if not session.get('logged_in'):
        return "Unauthorized", 401
    return render_template("face_capture.html")

# API to save captured face
@face_capture_bp.route("/face-capture", methods=["POST"])
def face_capture_api():
    username = session.get('username')  # Get username from session
    data = request.get_json()
    image_data = data.get("image")

    if not username or not image_data:
        return jsonify({"success": False, "message": "Username or image missing"})

    # Decode base64 image
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Get face encoding
    encodings = face_recognition.face_encodings(frame)
    if not encodings:
        return jsonify({"success": False, "message": "No face detected"})

    encoding_list = encodings[0].tolist()

    # Save encoding to DB
    query = """
        INSERT INTO tender.user_faces (user_id, face_encoding)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET face_encoding = EXCLUDED.face_encoding
    """
    db.execute(query, [username, json.dumps(encoding_list)])

    return jsonify({"success": True, "message": "Face registered successfully!"})

# Route for live video feed
@face_capture_bp.route("/video-feed")
def video_feed():
    def generate():
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        cap.release()
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
