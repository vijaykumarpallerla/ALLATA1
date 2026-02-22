from flask import Flask, send_file
import webbrowser
import threading
import os

# Initialize Flask app
# We use the current directory for static files so we don't need to move styles.css, script.js, index.html 
app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')

@app.route('/')
def home():
    # Serve the main job portal HTML
    return send_file('index.html')

@app.route('/api/jobs')
def api_jobs():
    # A placeholder API route where you can later upload your scraped jobs
    return {"status": "success", "message": "Jobs API is ready to be implemented."}

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
