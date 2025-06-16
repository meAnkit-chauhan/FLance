# Let's provide the backend logic for:
# 1. Displaying invitation cards from a directory
# 2. Handling card uploads from the admin panel
# 3. Enabling download of QR codes
# We'll simulate image metadata handling in a JSON file for simplicity.

import os
import json
from flask import Flask,session,flash, render_template, request, redirect, url_for, send_from_directory
import qrcode
from datetime import datetime
from werkzeug.utils import secure_filename

# Configuration
app = Flask(__name__)

# Add your secret key here
app.secret_key = os.getenv('SECRET_KEY', 'defaultfallbackkey') # Replace 'supersecretkey' with a strong and secure key

UPLOAD_FOLDER = 'static/cards'
QR_FOLDER = 'static/qr'
CARD_DB = 'card_data.json'


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_FOLDER'] = QR_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
  

# Load card metadata
def load_cards():
    if os.path.exists(CARD_DB):
        with open(CARD_DB, 'r') as f:
            return json.load(f)
    return []

# Save card metadata
def save_cards(cards):
    with open(CARD_DB, 'w') as f:
        json.dump(cards, f)

# Sample service dictionary
services = {
    "Design": ["Graphic Design", "UI/UX Design", "Custom Invitations"],
    "Development": ["Web Development", "App Development", "Custom CRM/ERM"],
    "Digital": ["E-commerce Setup", "Digital Marketing", "Domain & Hosting", "Support Packages"],
    "Content": ["Social Media Management", "Content Writing", "Video Editing"]
}

# Routes

@app.route('/admin', methods=['GET'])
def admin():
    if not session.get('admin'):  # Check if 'admin' is in the session
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))  # Redirect to home if not authenticated
    cards = load_cards()
    return render_template('admin.html', cards=cards)

@app.route('/', methods=['GET'])
def index():
    cards = load_cards()
    print(cards) # debugging check the console output for cards
    return render_template('index.html', services=services, cards=cards)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.form['qr_data']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}.png"
    path = os.path.join(app.config['QR_FOLDER'], filename)

    img = qrcode.make(data)
    img.save(path)
    qr_url = url_for('static', filename=f'qr/{filename}')
    
    cards = load_cards()
    flash("QR code generated successfully!", "success")
    return render_template('admin.html', cards=cards, qr_image_url=qr_url)



@app.route('/upload_card', methods=['POST'])
def upload_card():
    if not session.get('admin'):  # Admin-only access
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))
    
    title = request.form['title']
    file = request.files['card_image']
    filename = secure_filename(file.filename)
    
    # Validate file type
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm'}
    if '.' in filename and filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash("Invalid file type. Only images and videos are allowed.", "error")
        return redirect(url_for('admin'))

    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    cards = load_cards()
    cards.append({
        "id": len(cards) + 1,
        "title": title,
        "image_url": url_for('static', filename=f'cards/{filename}')
    })
    save_cards(cards)
    flash("Card uploaded successfully!", "success")
    return redirect(url_for('admin'))


@app.route('/card/<int:card_id>')
def card_detail(card_id):
    cards = load_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        return "Card not found", 404
    return f"<h1>{card['title']}</h1><img src='{card['image_url']}' style='max-width:600px;'>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Replace with your authentication logic
        if username == 'admin' and password == 'securepassword':  # Example credentials
            session['admin'] = True  # Save admin status in the session
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials.", "error")
    return render_template('login.html')  # Display the login form

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('admin', None)  # Remove admin from session
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    cards = load_cards()
    card = next((c for c in cards if c['id'] == card_id), None)
    if card:
        cards = [c for c in cards if c['id'] != card_id]
        save_cards(cards)
        flash("Card deleted successfully!", "success")
    else:
        flash("Card not found.", "error")
    return redirect(url_for('admin'))


# Run the app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

