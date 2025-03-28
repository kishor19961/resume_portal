from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
from datetime import datetime
import pytz
import requests
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Replace with your public Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv"

# Cache the sheet data for 1 minute to avoid too many requests
sheet_cache = {'data': None, 'timestamp': 0}
CACHE_DURATION = 60  # seconds

def get_sheet_data():
    current_time = time.time()
    if sheet_cache['data'] is None or (current_time - sheet_cache['timestamp']) > CACHE_DURATION:
        try:
            df = pd.read_csv(SHEET_URL)
            sheet_cache['data'] = df.values.tolist()
            sheet_cache['timestamp'] = current_time
        except Exception as e:
            print(f"Error reading sheet: {e}")
            return []
    return sheet_cache['data']

def get_profile_counts(job_id):
    data = get_sheet_data()
    counts = {
        'All': 0,
        'New': 0,
        'Rejected': 0,
        'Shortlisted': 0
    }
    
    for row in data:
        if str(row[0]) == str(job_id):
            counts['All'] += 1
            status = row[3] if len(row) > 3 and pd.notna(row[3]) else 'New'
            if status in counts:
                counts[status] += 1
            else:
                counts['New'] += 1
    
    return counts

def get_profiles(job_id, status='All'):
    data = get_sheet_data()
    profiles = []
    
    for i, row in enumerate(data, start=2):
        if str(row[0]) == str(job_id):
            current_status = row[3] if len(row) > 3 and pd.notna(row[3]) else 'New'
            if status == 'All' or current_status == status:
                profiles.append({
                    'id': i,
                    'name': row[1],
                    'email': row[2],
                    'status': current_status,
                    'pdf_url': row[4] if len(row) > 4 else ''
                })
    
    return profiles

@app.route('/')
def index():
    return render_template('index.html',
                         timestamp=datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                         user='kishor19961')

@app.route('/profiles')
def profiles():
    job_id = request.args.get('job_id')
    if not job_id:
        return redirect(url_for('index'))
    
    counts = get_profile_counts(job_id)
    return render_template('profiles.html',
                         job_id=job_id,
                         counts=counts,
                         timestamp=datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                         user='kishor19961')

@app.route('/profile-list')
def profile_list():
    job_id = request.args.get('job_id')
    status = request.args.get('status', 'All')
    
    if not job_id:
        return redirect(url_for('index'))
    
    profiles = get_profiles(job_id, status)
    return render_template('profile_list.html',
                         profiles=profiles,
                         job_id=job_id,
                         status=status,
                         timestamp=datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                         user='kishor19961')

@app.route('/profile-view')
def profile_view():
    job_id = request.args.get('job_id')
    profile_id = request.args.get('id')
    pdf_url = request.args.get('pdf')
    
    if not all([job_id, profile_id, pdf_url]):
        return redirect(url_for('index'))
    
    return render_template('profile_view.html',
                         job_id=job_id,
                         profile_id=profile_id,
                         pdf_url=pdf_url,
                         timestamp=datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                         user='kishor19961')

if __name__ == '__main__':
    app.run(debug=True)
