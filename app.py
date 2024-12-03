from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
import bcrypt
import requests

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/business_assistant_db"
mongo = PyMongo(app)

# API endpoint and headers
API_URL = "https://cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com/v1/chat/completions"
HEADERS = {
    "x-rapidapi-key": "a7b0734f2amsh73755e653a44facp1ce879jsn6decb4df32a6",
    "x-rapidapi-host": "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api.p.rapidapi.com",
    "Content-Type": "application/json"
}

# Function to fetch business analysis from API
def get_business_analysis_api(query):
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "model": "gpt-4o",
        "max_tokens": 500,
        "temperature": 0.7
    }
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "No response from API.")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

# Route for Home Page
@app.route('/')
def home_page():
    return render_template('home.html')
@app.route('/index')
def index():
    return render_template('index.html')

# Route for About Page
@app.route('/about')
def about_page():
    return render_template('about.html')

# Route for Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user exists
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into MongoDB
        mongo.db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })
        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Route for Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = mongo.db.users.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to index.html after successful login
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')



# Route for Results Page
@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        user_query = request.form.get('query')
        if not user_query:
            return render_template('result.html', response="No query provided.", query="")
        
        result = get_business_analysis_api(user_query)
        if result.startswith("Error:"):
            result = "We encountered an issue fetching the analysis. Please try again later."
        
        return render_template('result.html', response=result, query=user_query)
    
    # If GET request, redirect to home
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    app.run(debug=True)
