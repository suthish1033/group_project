from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from docx import Document

from ats_analyzer import calculate_ats_score
from flask_cors import CORS

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime, timedelta

import random
import secrets

from db import users, password_resets
from email_service import send_otp_email


app = Flask(__name__)

CORS(app)


# ------------------------------------------------
# REGISTER
# ------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")


    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400


    existing_user = users.find_one({
        "email": email
    })


    if existing_user:

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409


    password_hash = generate_password_hash(
        password
    )


    user = {

        "name": name,

        "email": email,

        "password": password_hash,

        "created_at": datetime.utcnow()

    }


    users.insert_one(user)


    return jsonify({

        "success": True,

        "message":
            "Registration successful"

    }), 201


# ------------------------------------------------
# LOGIN
# ------------------------------------------------

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )


    user = users.find_one({
        "email": email
    })


    if not user:

        return jsonify({
            "success": False,
            "message":
                "Invalid email or password"
        }), 401


    password_correct = check_password_hash(

        user["password"],

        password

    )


    if not password_correct:

        return jsonify({
            "success": False,
            "message":
                "Invalid email or password"
        }), 401


    # Simple login token for demo
    token = secrets.token_hex(32)


    return jsonify({

        "success": True,

        "message": "Login successful",

        "token": token,

        "user": {

            "name": user["name"],

            "email": user["email"]

        }

    }), 200


# ------------------------------------------------
# FORGOT PASSWORD
# ------------------------------------------------

@app.route(
    "/api/forgot-password",
    methods=["POST"]
)
def forgot_password():

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()


    user = users.find_one({
        "email": email
    })


    # Do not reveal whether account exists
    if not user:

        return jsonify({

            "success": True,

            "message":
                "If this email is registered, "
                "a reset code has been sent."

        }), 200


    # Generate 6 digit OTP

    otp = str(
        random.randint(
            100000,
            999999
        )
    )


    # Expire after 10 minutes

    expires_at = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )


    # Delete old reset codes

    password_resets.delete_many({

        "email": email

    })


    password_resets.insert_one({

        "email": email,

        "otp": otp,

        "expires_at": expires_at,

        "verified": False

    })


    try:

        send_otp_email(
            email,
            otp
        )

    except Exception as e:

        print("Email error:", e)

        password_resets.delete_many({
            "email": email
        })

        return jsonify({

            "success": False,

            "message":
                "Unable to send email"

        }), 500


    return jsonify({

        "success": True,

        "message":
            "Reset code sent to your email"

    }), 200


# ------------------------------------------------
# VERIFY OTP
# ------------------------------------------------

@app.route(
    "/api/verify-code",
    methods=["POST"]
)
def verify_code():

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    otp = data.get(
        "code",
        ""
    ).strip()


    reset_data = password_resets.find_one({

        "email": email,

        "otp": otp,

        "verified": False

    })


    if not reset_data:

        return jsonify({

            "success": False,

            "message":
                "Invalid verification code"

        }), 400


    if datetime.utcnow() > reset_data[
        "expires_at"
    ]:

        return jsonify({

            "success": False,

            "message":
                "Verification code expired"

        }), 400


    password_resets.update_one(

        {
            "_id":
                reset_data["_id"]
        },

        {
            "$set": {
                "verified": True
            }
        }

    )


    return jsonify({

        "success": True,

        "message":
            "Code verified successfully"

    }), 200


# ------------------------------------------------
# RESET PASSWORD
# ------------------------------------------------

@app.route(
    "/api/reset-password",
    methods=["POST"]
)
def reset_password():

    data = request.get_json()

    email = data.get(
        "email",
        ""
    ).strip().lower()

    new_password = data.get(
        "new_password",
        ""
    )


    reset_data = password_resets.find_one({

        "email": email,

        "verified": True

    })


    if not reset_data:

        return jsonify({

            "success": False,

            "message":
                "Please verify your code first"

        }), 400


    if len(new_password) < 8:

        return jsonify({

            "success": False,

            "message":
                "Password must be at least 8 characters"

        }), 400


    new_hash = generate_password_hash(
        new_password
    )


    result = users.update_one(

        {
            "email": email
        },

        {
            "$set": {
                "password": new_hash
            }
        }

    )


    if result.matched_count == 0:

        return jsonify({

            "success": False,

            "message":
                "User not found"

        }), 404


    # Remove used reset record

    password_resets.delete_many({

        "email": email

    })


    return jsonify({

        "success": True,

        "message":
            "Password updated successfully"

    }), 200


# ==========================================
# ATS RESUME ANALYSIS
# ==========================================

@app.route("/api/ats/analyze", methods=["POST"])
def analyze_resume():

    try:

        if "resume" not in request.files:

            return jsonify({
                "success": False,
                "message": "Please upload a resume."
            }), 400


        file = request.files["resume"]

        job_role = request.form.get(
            "job_role",
            ""
        ).strip()


        if not job_role:

            return jsonify({
                "success": False,
                "message": "Please select a job role."
            }), 400


        if file.filename == "":

            return jsonify({
                "success": False,
                "message": "No file selected."
            }), 400


        filename = file.filename.lower()


        # ==========================
        # PDF
        # ==========================

        if filename.endswith(".pdf"):

            reader = PdfReader(file)

            text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"


        # ==========================
        # DOCX
        # ==========================

        elif filename.endswith(".docx"):

            document = Document(file)

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )


        else:

            return jsonify({
                "success": False,
                "message": "Only PDF and DOCX files are supported."
            }), 400


        if not text.strip():

            return jsonify({
                "success": False,
                "message": "Unable to extract text from this resume."
            }), 400


        # Analyze resume

        result = calculate_ats_score(
            text,
            job_role
        )


        result["filename"] = file.filename

        result["success"] = True


        return jsonify(result), 200


    except Exception as e:

        print("ATS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Resume analysis failed."
        }), 500
# ------------------------------------------------
# TEST ROUTE
# ------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "message": "ResumeAI backend is running"
    })


# ------------------------------------------------
# RUN SERVER
# ------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )