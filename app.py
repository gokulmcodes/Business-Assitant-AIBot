from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import bcrypt
import requests
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual connection string
db = client['businessAI']  # Replace with your actual database name
users_collection = db['users']  # Replace 'users' with your actual collection name

# Replace with your email and SMTP server settings
SMTP_SERVER = 'smtp.gmail.com'  # For Gmail
SMTP_PORT = 587  # Use 465 for SSL
SENDER_EMAIL = 'mounicababe@gmail.com'
SENDER_PASSWORD = 'ervz jofn inod pamu'  # Use App Passwords if 2FA is enabled

def get_business_analysis_api(query, location=None):
    url = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"

    # Prepare the full message based on location
    if location:
        user_prompt = f"Analyze this business idea for {location}, Tamil Nadu: {query}"
    else:
        user_prompt = query

    # Payload format for GPT-4o
    payload = {
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "model": "gpt-4o",
        "max_tokens": 500,
        "temperature": 0.8
    }

    headers = {
        "x-rapidapi-key": "a7b0734f2amsh73755e653a44facp1ce879jsn6decb4df32a6",
        "x-rapidapi-host": "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']

            # Optional cleanup and business keyword filtering
            content = content.replace("###", "").replace("**", "")
            business_keywords = ["business", "market", "startup", "strategy", "economy", "investment"]
            if any(keyword in content.lower() for keyword in business_keywords):
                lines = content.split("\n")
                return "<br>".join([line.strip() for line in lines if line.strip()])
            else:
                return "Error: This query is not related to business."
        else:
            return f"API Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"Exception occurred while calling GPT-4o API: {str(e)}"



# Email sending function
def send_email(name, email, message):
    try:
        # Set up the MIME message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = 'mounicababe@gmail.com'  # Replace with your recipient's email
        msg['Subject'] = f"Contact Form Submission from {name}"

        # Body of the email
        body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server and send the email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Start TLS encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, msg['To'], text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Route for Home Page
@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

# Route for About Page
@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/features')
def features_page():
    return render_template('features.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

# Route for Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the user already exists
        if users_collection.find_one({'email': email}):
            flash('User already exists. Please try logging in.', 'danger')
            return redirect(url_for('signup'))

        # Hash the password before saving
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert the new user into the database
        users_collection.insert_one({'email': email, 'password': hashed_password.decode('utf-8')})
        flash('Signup successful! Please log in to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Retrieve the user from the database
        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

# Route for Contact Form with Email Sending
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    popup_message = None
    popup_status = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Send email and check if it was successful
        if send_email(name, email, message):
            popup_message = "Email sent successfully!"
            popup_status = "success"
        else:
            popup_message = "Error sending email."
            popup_status = "error"

    return render_template('contact.html', popup_message=popup_message, popup_status=popup_status)

@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        user_query = request.form.get('query')
        location = request.form.get('location')
        
        if not user_query:
            return render_template('result.html', response="No query provided.", query="")
        
        result = get_business_analysis_api(user_query, location)
        return render_template('result.html', response=result, query=user_query)

    # If GET request, show a placeholder or redirect
    return render_template('result.html', response="Reloading the page...", query="")


if __name__ == '__main__':
    app.run(debug=True)
