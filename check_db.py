from app import app, db, Job

with app.app_context():
    jobs = Job.query.order_by(Job.id.desc()).limit(3).all()
    for j in jobs:
        print(f"ID: {j.id}, Title: {j.title}, LinkedIn: '{j.linkedin_url}'")
