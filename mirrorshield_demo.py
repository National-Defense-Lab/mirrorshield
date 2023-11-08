import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from urllib3.util.retry import Retry
import os
import json
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from concurrent.futures import ThreadPoolExecutor

# Environment Variables for API credentials
API_KEY = os.getenv('API_KEY')

# Define API endpoints
API_ENDPOINTS = {
    'social_media': 'https://api.socialmedia.com/posts',
    'news': 'https://api.newsprovider.com/articles'
}

# Alert Recipients
ALERT_RECIPIENTS = {
    'high_severity': ['admin@example.com', 'security@example.com'],
    'medium_severity': ['communications@example.com'],
    'low_severity': ['info@example.com'],
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MirrorShield')

# Session setup for retries and backoff
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Data ingestion function
def fetch_data(api_endpoint):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = session.get(api_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'Error fetching data: {e}')
        return None

# Data normalization function
def normalize_data(raw_data):
    normalized_data = {}
    for entry in raw_data:
        normalized_entry = {
            'source': entry.get('source'),
            'timestamp': entry.get('timestamp'),
            'author': entry.get('author'),
            'content': entry.get('content'),
        }
        normalized_data[entry['id']] = normalized_entry
    return normalized_data

# Disinformation detection function
def analyze_data(text_to_analyze):
    model = load('disinformation_model.joblib')
    prediction = model.predict([text_to_analyze])
    probability = model.predict_proba([text_to_analyze])
    return prediction, probability

# Alerting function
def send_alert(severity, message, content=''):
    recipients = ALERT_RECIPIENTS.get(severity, [])
    if not recipients:
        logger.error(f"No recipients defined for severity: {severity}")
        return

    email = EmailMessage()
    email.set_content(content)
    email['Subject'] = message
    email['From'] = 'alert-system@example.com'

    try:
        with smtplib.SMTP('localhost') as smtp:
            for recipient in recipients:
                email['To'] = recipient
                smtp.send_message(email)
                logger.info(f"Alert sent to: {recipient}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

# Reporting function
def generate_report(findings):
    report_filename = 'disinformation_report.pdf'
    historical_data_filename = 'historical_data.csv'
    
    df = pd.DataFrame(findings)
    df.plot(kind='bar')
    plt.savefig(report_filename)
    df.to_csv(historical_data_filename, mode='a', header=False)
    
    logger.info(f"Report and historical data saved. (Report: {report_filename}, Historical Data: {historical_data_filename})")

# Main task function
def main_task():
    aggregated_data = {}
    for endpoint_name, api_endpoint in API_ENDPOINTS.items():
        raw_data = fetch_data(api_endpoint)
        if raw_data:
            normalized_data = normalize_data(raw_data)
            aggregated_data[endpoint_name] = normalized_data
    
    findings = []
    for category, data in aggregated_data.items():
        for id, entry in data.items():
            prediction, probability = analyze_data(entry['content'])
            if prediction[0] == 1:
                finding = {
                    'id': id,
                    'content': entry['content'],
                    'probability': probability[0][1]
                }
                findings.append(finding)
    
    for finding in findings:
        severity = 'high_severity' if finding['probability'] > 0.9 else 'medium_severity' if finding['probability'] > 0.7 else 'low_severity'
        send
