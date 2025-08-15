# face_login.py
import base64
import cv2
import numpy as np
import face_recognition
import json
import db_connect as db
from flask import Blueprint, request, jsonify, render_template

# Blueprint name MUST match what you will use in url_for
face_login_bp = Blueprint(
    "face_login",  # <-- this is used in url_for('face_login.face_login_page')
    __name__,
    template_folder="templates",
    static_folder="static",
)

@face_login_bp.route("/face-login", methods=["GET"])
def face_login_page():
    return render_template("face_login.html")

@face_login_bp.route("/face-login", methods=["POST"])
def face_login_api():
    data = request.get_json()
    image_data = data.get("image")

    if not image_data:
        return jsonify({"success": False, "message": "No image provided"})

    # Decode base64 image
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Get face encodings
    encodings = face_recognition.face_encodings(frame)
    if not encodings:
        return jsonify({"success": False, "message": "No face detected"})

    input_encoding = encodings[0]

    # Fetch all user face encodings and passwords
    query = """
        SELECT uf.user_id, uf.face_encoding, ud."password"
        FROM tender.user_faces uf
        JOIN ums.user_details ud ON ud.username = uf.user_id
    """
    rows = db.get_data_in_list_of_tuple(query)

    for user_id, face_encoding_json, password in rows:
        db_encoding = np.array(json.loads(face_encoding_json))
        matches = face_recognition.compare_faces([db_encoding], input_encoding)
        if matches[0]:
            # Face matched: return username & password to JS for login
            return jsonify({
                "success": True,
                "message": f"Welcome {user_id}",
                "username": user_id,
                "password": password
            })

    return jsonify({"success": False, "message": "Face not recognized"})

