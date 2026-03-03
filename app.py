from flask import Flask, send_file, request, jsonify, render_template
import webbrowser
import threading
import os
import math
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

load_dotenv()

import logging
from Algorithm import moderate_job_post

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
app = Flask(__name__)

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

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(100), nullable=False)
    posted = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    apply_url = db.Column(db.String(500), nullable=True)
    is_algorithm = db.Column(db.Boolean, default=False, nullable=False)

with app.app_context():
    # Because sqlite is rigid, adding a default False value to existing rows might require dropping the table or setting server_default.
    # Since it's development, we'll let SQLAlchemy manage it or add a try/except for the migration if Xata handles it.
    db.create_all()
import json

@app.route('/')
def home():
    try:
        json_path = os.path.join(app.root_path, 'static', 'data', 'blogs.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            blogs = json.load(f)
    except Exception as e:
        blogs = []
    return render_template('index.html', blogs=blogs)

@app.route('/blog/<blog_id>')
def read_blog(blog_id):
    try:
        json_path = os.path.join(app.root_path, 'static', 'data', 'blogs.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            blogs = json.load(f)
        for blog in blogs:
            if blog['id'] == blog_id:
                return render_template('blog_post.html', blog=blog)
    except Exception as e:
        pass
    return "Blog not found", 404

@app.route('/browse_jobs')
def usa_jobs_page():
    # Read the main job portal HTML
    try:
        html_content = render_template('USA_Browse_jobs.html')

        # Parse query parameters for server-side filtering
        jobtype_query = request.args.get('jobtype', '')
        workmodel_query = request.args.get('workmodel', '')
        search_query = request.args.get('q', '').strip().lower()
        location_query = request.args.get('loc', '').strip().lower()
        
        job_types = []
        work_models = []
        
        if jobtype_query:
            job_types = [t.strip() for t in jobtype_query.split(',')]
            
        if workmodel_query:
            work_models = [m.strip() for m in workmodel_query.split(',')]

        # Fetch live jobs from the database (newest first!)
        all_jobs = Job.query.order_by(Job.id.desc()).all()
        filtered_jobs = []
        
        # Apply filters server-side
        for job in all_jobs:
            type_match = True
            if job_types:
                type_match = job.job_type in job_types
                
            model_match = True
            if work_models:
                loc = job.location.lower()
                is_remote = 'remote' in loc
                is_hybrid = 'hybrid' in loc
                is_onsite = not is_remote and not is_hybrid
                
                model_match = False
                if 'Remote' in work_models and is_remote: model_match = True
                if 'Hybrid' in work_models and is_hybrid: model_match = True
                if 'On-site' in work_models and is_onsite: model_match = True
                
            search_match = True
            if search_query:
                # Search across title, company, and skills (experience)
                search_match = (
                    search_query in job.title.lower() or 
                    search_query in job.company.lower() or 
                    search_query in job.experience.lower()
                )
                
            loc_match = True
            if location_query:
                loc_match = location_query in job.location.lower()
                
            if type_match and model_match and search_match and loc_match:
                filtered_jobs.append(job)

        # --- Pagination Logic ---
        per_page = 8
        total_jobs = len(filtered_jobs)
        total_pages = math.ceil(total_jobs / per_page)
        
        if total_pages == 0:
            total_pages = 1
            
        current_page = request.args.get('page', 1, type=int)
        
        if current_page < 1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages
            
        start_idx = (current_page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_jobs = filtered_jobs[start_idx:end_idx]

        jobs_html = ""
        
        for job in paginated_jobs:
            # Generate initials for logo
            initials = ''.join(w[0] for w in job.company.split()).upper()[:2]
            
            query_str = urlencode({'jobid': job.id, 'jobtitle': job.title})
            job_url = f"/job?{query_str}"
            
            jobs_html += f'''
            <article class="job-card" onclick="window.location.href='{job_url}'" style="cursor: pointer;">
                <div class="job-card-header">
                    <div class="job-company-info">
                        <div class="company-logo">{initials}</div>
                        <div class="job-title-container">
                            <h3>{job.title}</h3>
                            <span class="company-name">{job.company}</span>
                        </div>
                    </div>
                    <button class="job-save" aria-label="Save job" onclick="event.stopPropagation(); toggleSave(this)">
                        <i class="far fa-bookmark"></i>
                    </button>
                </div>
                
                <div class="job-details">
                    <div class="job-detail-badge">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>{job.location}</span>
                    </div>
                    <div class="job-detail-badge">
                        <i class="fas fa-briefcase"></i>
                        <span>{job.job_type}</span>
                    </div>'''
            
            if job.salary and job.salary != 'Competitive':
                jobs_html += f'''
                    <div class="job-detail-badge">
                        <i class="fas fa-money-bill-wave"></i>
                        <span>{job.salary}</span>
                    </div>'''
                    
            jobs_html += f'''
                </div>
                
                <p class="job-description">
                    {job.description}
                </p>
                
                <div class="job-footer">
                    <span class="job-posted-time">Date Posted: {job.posted}</span>'''
            
            if getattr(job, 'apply_url', None) and job.apply_url.strip():
                if '@' in job.apply_url:
                    jobs_html += f'''
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 0.85rem; color: var(--primary-color); font-weight: 500;">Email ID Found &rarr;</span>
                        <button type="button" class="btn btn-primary" style="display: inline-flex; align-items: center; justify-content: center;" onclick="event.stopPropagation(); window.location.href='{job_url}'">Apply Now</button>
                    </div>'''
                else:
                    jobs_html += f'''
                        <button type="button" class="btn btn-primary" style="display: inline-flex; align-items: center; justify-content: center;" onclick="event.stopPropagation(); window.location.href='{job_url}'">Apply Now</button>'''
            else:
                jobs_html += f'''
                    <button type="button" class="btn btn-primary" onclick="event.stopPropagation(); window.location.href='{job_url}'">Apply Now</button>'''
                    
            jobs_html += f'''
                </div>
            </article>
            '''

        # If there are jobs, inject them into the HTML, otherwise put the empty marker
        if not jobs_html:
            jobs_html = '<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);"><h3>No jobs match your selected filters.</h3></div>'
            
        # Build pagination HTML dynamically
        pagination_html = ""
        if total_jobs > 0:
            # Construct a base query dictionary excluding 'page' to keep filter params
            base_args = request.args.to_dict()
            
            for p in range(1, total_pages + 1):
                page_args = base_args.copy()
                page_args['page'] = p
                query_string = urlencode(page_args)
                
                active_class = ' active' if p == current_page else ''
                pagination_html += f'<a href="/?{query_string}#jobs" class="btn-page{active_class}" style="text-decoration: none; display: inline-flex; align-items: center; justify-content: center;">{p}</a>\n'
                
        # Perform Server-Side Rendering (SSR) by injecting the HTML strings directly
        html_content = html_content.replace('<!-- Job cards will be populated by JavaScript -->', jobs_html)
        html_content = html_content.replace('<!-- Pagination will be replaced by the server -->', pagination_html)
        
        # We need to return the modified string as proper HTML
        return html_content
        
    except FileNotFoundError:
        return "index.html not found", 404

# Get API Keys from environment
API_KEY = os.environ.get('API_KEY')
UPLOAD_KEY = os.environ.get('UPLOAD_KEY')

@app.route('/api/jobs', methods=['GET', 'POST'])
def api_jobs():
    if request.method == 'POST':
        # Authenticate upload using separate UPLOAD_KEY
        request_key = request.headers.get('X-UPLOAD-KEY')
        if not UPLOAD_KEY or request_key != UPLOAD_KEY:
            return jsonify({"status": "error", "message": "Unauthorized Upload Key"}), 401
            
        data = request.json
        if not data or 'jobs' not in data:
            return jsonify({"status": "error", "message": "Missing 'jobs' array in JSON payload."}), 400
            
        incoming_jobs = data.get('jobs', [])
        added_count = 0
        
        try:
            for job_data in incoming_jobs:
                # We use .get() with safe fallback strings so the server NEVER crashes
                # even if the scraping script misspells a key or forgets one!
                new_job = Job(
                    title=job_data.get('title') or 'Unknown Title',
                    company=job_data.get('company') or 'Unknown Company',
                    location=job_data.get('location') or 'Location not specified',
                    job_type=job_data.get('job_type') or job_data.get('type') or 'Full-time',
                    experience=job_data.get('experience') or 'Not specified',
                    salary=job_data.get('salary') or 'Competitive',
                    posted=job_data.get('posted') or datetime.now(timezone(timedelta(hours=-5), 'EST')).strftime("%d/%m/%Y EST"),
                    description=job_data.get('description') or 'No description provided.',
                    apply_url=job_data.get('apply_url') or job_data.get('url') or '',
                    is_algorithm=False # External uploads bypass algorithm
                )
                db.session.add(new_job)
                added_count += 1
                
            db.session.commit()
            return jsonify({"status": "success", "message": f"Successfully securely uploaded {added_count} jobs!"})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": f"Database insertion failed: {str(e)}"}), 500
            
    # Handle GET request (sending jobs to API users)
    # Authenticate the request using standard API_KEY
    request_key = request.headers.get('X-API-KEY')
    if not API_KEY or request_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    try:
        # Fetch ordered by newest first
        jobs = Job.query.order_by(Job.id.desc()).all()
        jobs_list = [{
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "type": j.job_type,  # Mapped for frontend compatibility
            "experience": j.experience,
            "salary": j.salary,
            "posted": j.posted,
            "description": j.description
        } for j in jobs]
        return jsonify({"status": "success", "jobs": jobs_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/submit-job', methods=['POST'])
def api_submit_job():
    data = request.json
    try:
        title = data.get('title', 'Unknown Title')
        company = data.get('company', 'Unknown Company')
        location = data.get('location', 'Location not specified')
        description = data.get('description', 'No description provided.')
        
        # 🛡️ AI CONTENT MODERATION ALGORITHM 🛡️
        # We pass the raw text to the Algorithm.py script to determine if it is spam or real
        is_approved = moderate_job_post(title, company, location, description)
        
        if not is_approved:
            print(f"[REJECTED FLAG] User tried to post fake/spam job: {title}")
            return jsonify({
                "status": "error", 
                "message": "Error 403: Your job posting was flagged as invalid or unprofessional by our automated AI system."
            }), 403
            
        new_job = Job(
            title=title,
            company=company,
            location=location,
            job_type=data.get('job_type', 'Full-time'),
            experience=data.get('experience', 'Not specified'),  # Maps to skills
            salary=data.get('salary', 'Competitive'),
            posted=datetime.now(timezone(timedelta(hours=-5), 'EST')).strftime("%d/%m/%Y EST"),
            description=description,
            apply_url=data.get('apply_url', ''),
            is_algorithm=True # Marks that it was passed through Algorithm.py via UI
        )
        db.session.add(new_job)
        db.session.commit()
        return jsonify({"status": "success", "message": f"Job '{new_job.title}' has been successfully submitted!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

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

@app.route('/job')
def job_detail():
    job_id = request.args.get('jobid')
    
    if not job_id:
        return "Missing job ID", 400
        
    job = db.session.get(Job, job_id)
    if not job:
        return "Job not found", 404
        
    try:
        html = render_template('job_detail.html')
            
        html = html.replace('<!-- JOB_TITLE -->', job.title)
        html = html.replace('<!-- JOB_COMPANY -->', job.company)
        html = html.replace('<!-- JOB_LOCATION -->', job.location)
        html = html.replace('<!-- JOB_TYPE -->', job.job_type)
        html = html.replace('<!-- JOB_SALARY -->', job.salary if job.salary else "Competitive")
        html = html.replace('<!-- JOB_EXPERIENCE -->', job.experience)
        
        # Replace line breaks with <br> for HTML rendering
        desc_html = job.description.replace('\n', '<br>')
        html = html.replace('<!-- JOB_DESCRIPTION -->', desc_html)
        html = html.replace('<!-- JOB_POSTED -->', job.posted)
        
        if getattr(job, 'apply_url', None) and job.apply_url.strip():
            if '@' in job.apply_url:
                apply_btn = f'''
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span id="job-detail-email-found" style="font-size: 1rem; color: var(--primary-color); font-weight: 600;">Email ID Found &rarr;</span>
                    <button type="button" id="job-detail-apply-btn" class="btn btn-primary btn-large" style="padding: 1rem 3rem; font-size: 1.1rem;" onclick="revealAndCopyEmail('{job.apply_url.strip()}')">Apply Now</button>
                    <a href="mailto:{job.apply_url.strip()}" id="job-detail-email-reveal" style="display: none; font-size: 1.1rem; font-weight: 600; color: var(--primary-dark); text-decoration: none;"><i class="far fa-envelope"></i> {job.apply_url.strip()}</a>
                    
                    <script>
                    function revealAndCopyEmail(email) {{
                        const foundText = document.getElementById('job-detail-email-found');
                        const revealText = document.getElementById('job-detail-email-reveal');
                        const btn = document.getElementById('job-detail-apply-btn');
                        
                        if (foundText.style.display !== 'none') {{
                            // First tap: Reveal email and change button text
                            foundText.style.display = 'none';
                            revealText.style.display = 'inline-block';
                            btn.innerHTML = 'Copy Email &nbsp;<i class="far fa-copy"></i>';
                        }} else {{
                            // Second tap: Copy to clipboard
                            navigator.clipboard.writeText(email).then(() => {{
                                btn.innerHTML = 'Email id Copied! <i class="fas fa-check"></i>';
                                setTimeout(() => {{
                                    btn.innerHTML = 'Copy Email &nbsp;<i class="far fa-copy"></i>';
                                }}, 2000);
                            }}).catch(err => {{
                                console.error('Failed to copy text: ', err);
                            }});
                        }}
                    }}
                    </script>
                </div>'''
            else:
                apply_btn = f'<a href="{job.apply_url.strip()}" target="_blank" class="btn btn-primary btn-large" style="text-decoration: none; display: inline-flex; align-items: center; justify-content: center; padding: 1rem 3rem; font-size: 1.1rem;">Apply Now &nbsp;<i class="fas fa-external-link-alt" style="font-size: 0.9rem;"></i></a>'
        else:
            apply_btn = f'<button class="btn btn-primary btn-large" onclick="applyJob(\'{job.title}\')" style="padding: 1rem 3rem; font-size: 1.1rem;">Apply Now</button>'
            
        html = html.replace('<!-- APPLY_BUTTON -->', apply_btn)
        
        return html
        
    except FileNotFoundError:
        return "job_detail.html not found", 404

@app.route(f'/{ADMIN_PATH}')
def admin():
    # Secret route to access the admin panel
    return render_template('admin.html')

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

@app.route('/api/admin/jobs', methods=['GET'])
def get_admin_jobs():
    try:
        jobs = Job.query.order_by(Job.id.desc()).all()
        job_list = [{
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "posted": j.posted,
            "type": j.job_type,
            "is_algorithm": j.is_algorithm
        } for j in jobs]
        return jsonify({"status": "success", "jobs": job_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/jobs/<int:job_id>', methods=['DELETE'])
def delete_admin_job(job_id):
    try:
        job = db.session.get(Job, job_id)
        if not job:
            return jsonify({"status": "error", "message": "Job not found"}), 404
        
        db.session.delete(job)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template('404.html'), 404
    except Exception:
        return "404 - Page Not Found", 404

@app.route('/job.html')
def job_html_page():
    return render_template('job.html')

@app.route('/aboutus.html')
def aboutus_page():
    return render_template('aboutus.html')

@app.route('/contact.html')
def contact_page():
    return render_template('contact.html')

@app.route('/terms.html')
def terms_page():
    return render_template('terms.html')

@app.route('/privacy.html')
def privacy_page():
    return render_template('privacy.html')

@app.route('/students.html')
def students_page():
    return render_template('students/students.html')

@app.route('/projects.html')
def projects_page():
    return render_template('students/projects.html')

@app.route('/project1.html')
def project1_page():
    return render_template('students/project1.html')

@app.route('/project2.html')
def project2_page():
    return render_template('students/project2.html')

@app.route('/project3.html')
def project3_page():
    return render_template('students/project3.html')

@app.route('/project4.html')
def project4_page():
    return render_template('students/project4.html')

@app.route('/DSAAI.html')
def dsaai_page():
    return render_template('students/DSAAI.html')

@app.route('/crack2026.html')
def crack2026_page():
    return render_template('students/crack2026.html')

@app.route('/promptai.html')
def promptai_page():
    return render_template('students/promptai.html')

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
