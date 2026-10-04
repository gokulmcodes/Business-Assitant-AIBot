import os
import smtplib
from pymongo import MongoClient

from huggingface_hub import InferenceClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

import bcrypt
import requests
from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    redirect,
    url_for,
    flash,
)
from pymongo import MongoClient


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)

# IMPORTANT:
# Store this value in an environment variable.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-secret-key")


# ============================================================
# Environment Variables
# ============================================================

MONGO_URI = os.environ.get("MONGO_URI")
HF_TOKEN = os.environ.get("HF_TOKEN")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
CONTACT_RECIPIENT_EMAIL = os.environ.get(
    "CONTACT_RECIPIENT_EMAIL",
    SMTP_EMAIL
)


# ============================================================
# MongoDB Configuration
# ============================================================

client = None
db = None
users_collection = None

if not MONGO_URI:
    print("WARNING: MONGO_URI environment variable is not configured.")

else:
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Force an actual connection to MongoDB
        client.admin.command("ping")

        db = client["businessAI"]
        users_collection = db["users"]

        print("MongoDB connected successfully.")

    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        users_collection = None



# ============================================================
# Health Check
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """
    Simple health-check endpoint.

    This endpoint does not connect to MongoDB or RapidAPI.
    It can be used by Vercel or monitoring services.
    """

    return jsonify({
        "status": "ok",
        "service": "Business Assistant AI Bot"
    }), 200


# ============================================================
# Business Analysis API
# ============================================================

def get_business_analysis_api(query, location=None):
    if not HF_TOKEN:
        return "Error: HF_TOKEN environment variable is not configured."

    if location:
        user_prompt = f"""
Analyze this business idea for {location}, Tamil Nadu.

Business request:
{query}

Provide a practical business analysis covering:

1. Business opportunity
2. Target customers
3. Suitable location strategy
4. Estimated initial investment
5. Expected operating costs
6. Revenue opportunities
7. Competition
8. Marketing strategy
9. Major risks
10. Final recommendation

Keep the answer practical, realistic and easy to understand.
"""
    else:
        user_prompt = f"""
Analyze this business idea:

{query}

Provide:

1. Business opportunity
2. Target customers
3. Investment
4. Location strategy
5. Revenue opportunities
6. Competition
7. Marketing strategy
8. Risks
9. Final recommendation

Keep the answer practical and easy to understand.
"""

    try:
        client = InferenceClient(
            api_key=HF_TOKEN
        )

        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical business analysis "
                        "assistant."
                    )
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_tokens=600,
            temperature=0.7
        )

        content = response.choices[0].message.content

        if not content:
            return "Error: No response received from Hugging Face."

        content = content.replace("###", "")
        content = content.replace("**", "")

        lines = content.split("\n")

        formatted_content = "<br>".join(
            line.strip()
            for line in lines
            if line.strip()
        )

        return formatted_content

    except Exception as e:
        print(f"Hugging Face API error: {e}")
        return f"AI API Error: {str(e)}"


# ============================================================
# Email Sending Function
# ============================================================

def send_email(name, email, message):
    """
    Send contact-form email using Gmail SMTP.
    """

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("SMTP credentials are not configured.")
        return False

    if not CONTACT_RECIPIENT_EMAIL:
        print("Contact recipient email is not configured.")
        return False

    try:

        # ----------------------------------------------------
        # Create MIME email
        # ----------------------------------------------------

        msg = MIMEMultipart()

        msg["From"] = SMTP_EMAIL
        msg["To"] = CONTACT_RECIPIENT_EMAIL
        msg["Subject"] = (
            f"Contact Form Submission from {name}"
        )

        body = (
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Message: {message}"
        )

        msg.attach(
            MIMEText(body, "plain")
        )

        # ----------------------------------------------------
        # Connect to Gmail SMTP
        # ----------------------------------------------------

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        )

        server.starttls()

        server.login(
            SMTP_EMAIL,
            SMTP_PASSWORD
        )

        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        server.sendmail(
            SMTP_EMAIL,
            CONTACT_RECIPIENT_EMAIL,
            msg.as_string()
        )

        server.quit()

        return True

    except smtplib.SMTPException as e:

        print(f"SMTP error while sending email: {e}")

        return False

    except Exception as e:

        print(f"Error sending email: {e}")

        return False


# ============================================================
# Home Page
# ============================================================

@app.route("/", methods=["GET"])
def home_page():
    return render_template("home.html")


# ============================================================
# Index Page
# ============================================================

@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")


# ============================================================
# Home Route
# ============================================================

@app.route("/home", methods=["GET"])
def home():
    return render_template("home.html")


# ============================================================
# About Page
# ============================================================

@app.route("/about", methods=["GET"])
def about_page():
    return render_template("about.html")


# ============================================================
# Features Page
# ============================================================

@app.route("/features", methods=["GET"])
def features_page():
    return render_template("features.html")


# ============================================================
# Contact Page + Contact Form
# ============================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    popup_message = None
    popup_status = None

    # --------------------------------------------------------
    # GET request
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "contact.html",
            popup_message=popup_message,
            popup_status=popup_status
        )

    # --------------------------------------------------------
    # POST request
    # --------------------------------------------------------

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    # --------------------------------------------------------
    # Validate form
    # --------------------------------------------------------

    if not name or not email or not message:

        popup_message = "Please fill in all fields."
        popup_status = "error"

        return render_template(
            "contact.html",
            popup_message=popup_message,
            popup_status=popup_status
        )

    # --------------------------------------------------------
    # Send email
    # --------------------------------------------------------

    if send_email(name, email, message):

        popup_message = "Email sent successfully!"
        popup_status = "success"

    else:

        popup_message = "Error sending email. Please try again."
        popup_status = "error"

    return render_template(
        "contact.html",
        popup_message=popup_message,
        popup_status=popup_status
    )


# ============================================================
# Signup
# ============================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":
        return render_template("signup.html")

    # --------------------------------------------------------
    # Check MongoDB configuration
    # --------------------------------------------------------

    if users_collection is None:

        flash(
            "Database is currently unavailable.",
            "danger"
        )

        return redirect(url_for("signup"))

    # --------------------------------------------------------
    # Get form values
    # --------------------------------------------------------

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # --------------------------------------------------------
    # Validate form
    # --------------------------------------------------------

    if not email or not password:

        flash(
            "Email and password are required.",
            "danger"
        )

        return redirect(url_for("signup"))

    # --------------------------------------------------------
    # Check existing user
    # --------------------------------------------------------

    try:

        existing_user = users_collection.find_one({
            "email": email
        })

        if existing_user:

            flash(
                "User already exists. Please try logging in.",
                "danger"
            )

            return redirect(url_for("signup"))

        # ----------------------------------------------------
        # Hash password
        # ----------------------------------------------------

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        # ----------------------------------------------------
        # Insert user
        # ----------------------------------------------------

        users_collection.insert_one({
            "email": email,
            "password": hashed_password.decode("utf-8")
        })

        flash(
            "Signup successful! Please log in to continue.",
            "success"
        )

        return redirect(url_for("login"))

    except Exception as e:

        print(f"Signup database error: {e}")

        flash(
            "An error occurred while creating your account.",
            "danger"
        )

        return redirect(url_for("signup"))


# ============================================================
# Login
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":
        return render_template("login.html")

    # --------------------------------------------------------
    # Check MongoDB
    # --------------------------------------------------------

    if users_collection is None:

        flash(
            "Database is currently unavailable.",
            "danger"
        )

        return redirect(url_for("login"))

    # --------------------------------------------------------
    # Get form values
    # --------------------------------------------------------

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not email or not password:

        flash(
            "Email and password are required.",
            "danger"
        )

        return redirect(url_for("login"))

    try:

        # ----------------------------------------------------
        # Find user
        # ----------------------------------------------------

        user = users_collection.find_one({
            "email": email
        })

        # ----------------------------------------------------
        # Verify password
        # ----------------------------------------------------

        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):

            flash(
                "Login successful!",
                "success"
            )

            return redirect(url_for("index"))

        # ----------------------------------------------------
        # Invalid credentials
        # ----------------------------------------------------

        flash(
            "Invalid email or password. Please try again.",
            "danger"
        )

        return redirect(url_for("login"))

    except Exception as e:

        print(f"Login database error: {e}")

        flash(
            "An error occurred while logging in.",
            "danger"
        )

        return redirect(url_for("login"))


# ============================================================
# Business Analysis Result
# ============================================================

@app.route("/result", methods=["GET", "POST"])
def result():

    # --------------------------------------------------------
    # POST request
    # --------------------------------------------------------

    if request.method == "POST":

        user_query = request.form.get(
            "query",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validate query
        # ----------------------------------------------------

        if not user_query:

            return render_template(
                "result.html",
                response="No query provided.",
                query=""
            )

        # ----------------------------------------------------
        # Call AI API
        # ----------------------------------------------------

        analysis_result = get_business_analysis_api(
            user_query,
            location
        )

        # ----------------------------------------------------
        # Render result
        # ----------------------------------------------------

        return render_template(
            "result.html",
            response=analysis_result,
            query=user_query
        )

    # --------------------------------------------------------
    # GET request
    # --------------------------------------------------------

    return render_template(
        "result.html",
        response="Reloading the page...",
        query=""
    )


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == "__main__":

    # Local development only.
    # Vercel will import the `app` object directly.

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )