from flask import Flask, send_file, request, jsonify
import webbrowser
import threading
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

import logging

ADMIN_PATH = os.environ.get('ADMIN_PATH', 'admin')

# Hide Secret Admin Link from Console Logs
class HideAdminLinkFilter(logging.Filter):
    def filter(self, record):
        query = ADMIN_PATH
        # Werkzeug request logs pass format args in record.args
        if record.args and len(record.args) > 0 and isinstance(record.args[0], str) and query in record.args[0]:
            print("0-------------------------------------------------------------0")
            return False
        return True

logging.getLogger('werkzeug').addFilter(HideAdminLinkFilter())

# Initialize Flask app
# We use the current directory for static files so we don't need to move styles.css, script.js, index.html 
app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    # Serve the main job portal HTML
    return send_file('index.html')

@app.route('/api/jobs')
def api_jobs():
    # A placeholder API route where you can later upload your scraped jobs
    return {"status": "success", "message": "Jobs API is ready to be implemented."}

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    try:
        new_msg = ContactMessage(
            name=data.get('name', 'Unknown'),
            email=data.get('email'),
            subject=data.get('subject'),
            body=data.get('body')
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "success", "message": "Your message has been sent successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route(f'/{ADMIN_PATH}')
def admin():
    # Secret route to access the admin panel
    return send_file('admin.html')

@app.route('/api/admin/messages', methods=['GET'])
def get_admin_messages():
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        msg_list = [{
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "subject": m.subject,
            "body": m.body,
            "created_at": m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else "Unknown"
        } for m in messages]
        return jsonify({"status": "success", "messages": msg_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/messages/<int:msg_id>', methods=['DELETE'])
def delete_admin_message(msg_id):
    try:
        msg = db.session.get(ContactMessage, msg_id)
        if not msg:
            return jsonify({"status": "error", "message": "Message not found"}), 404
        
        db.session.delete(msg)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Function to automatically open the browser
    def open_browser():
        # Make sure it opens the correct local address
        webbrowser.open('http://127.0.0.1:5000/')
        
    # Prevent the browser from opening twice when the development server reloads
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Start a short timer so the server can start up before the browser opens
        threading.Timer(1.25, open_browser).start()
        
    print("Starting Allata Job Portal app...")
    # Run the Flask server
    app.run(debug=True, port=5000)
