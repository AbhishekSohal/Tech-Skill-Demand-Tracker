import subprocess
import sys
import os
from datetime import datetime

log_file = f"data/scraper_log_{datetime.now().strftime('%Y%m%d')}.txt"

def log(msg):
    print(msg)
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} — {msg}\n")

log("="*50)
log(f"Scraper run started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
log("="*50)

# Run Naukri scraper
log("Running Naukri scraper...")
try:
    result = subprocess.run(
        [sys.executable, 'scrapers/naukri_scraper.py'],
        capture_output=True, text=True, timeout=600
    )
    log(f"Naukri scraper finished: {result.stdout[-200:] if result.stdout else 'No output'}")
except Exception as e:
    log(f"Naukri scraper error: {e}")

# Run Foundit scraper
log("Running Foundit scraper...")
try:
    result = subprocess.run(
        [sys.executable, 'scrapers/foundit_scraper.py'],
        capture_output=True, text=True, timeout=1200
    )
    log(f"Foundit scraper finished: {result.stdout[-200:] if result.stdout else 'No output'}")
except Exception as e:
    log(f"Foundit scraper error: {e}")

# Combine datasets
log("Combining datasets...")
try:
    import pandas as pd
    import re

    naukri_df = pd.read_csv('data/naukri_data_analyst_jobs.csv')
    foundit_df = pd.read_csv('data/foundit_data_analyst_jobs.csv')

    naukri_df['source'] = 'Naukri'
    foundit_df['source'] = 'Foundit'

    combined_df = pd.concat([naukri_df, foundit_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['Title', 'Company'])

    # Run skill extraction
    SKILL_PATTERNS = {
        'SQL':              r'(?i)\b(sql|mysql|postgresql|nosql|sqlite)\b',
        'Python':           r'(?i)\b(python)\b',
        'Excel':            r'(?i)\b(excel|advanced excel|ms excel)\b',
        'Power BI':         r'(?i)\b(power\s?bi|powerbi|microsoft power bi)\b',
        'Tableau':          r'(?i)\b(tableau)\b',
        'AWS':              r'(?i)\b(aws|amazon web services)\b',
        'Azure':            r'(?i)\b(azure)\b',
        'GCP':              r'(?i)\b(gcp|google cloud)\b',
        'Machine Learning': r'(?i)\b(machine learning)\b',
        'Statistics':       r'(?i)\b(statistics|statistical)\b',
        'Spark':            r'(?i)\b(spark|pyspark)\b',
        'Snowflake':        r'(?i)\b(snowflake)\b',
        'ETL':              r'(?i)\b(etl|elt)\b',
        'Power BI':         r'(?i)\b(power\s?bi|powerbi)\b',
        'Tableau':          r'(?i)\b(tableau)\b',
        'Data Visualization': r'(?i)\b(data visualization|data viz)\b',
    }

    def extract_skills(row):
        full_text = str(row.get('Description', '')).lower() + \
                    " " + str(row.get('Skills_Listed', '')).lower()
        extracted = {}
        for skill, pattern in SKILL_PATTERNS.items():
            extracted[skill] = 1 if re.search(pattern, full_text) else 0
        return pd.Series(extracted)

    skills_df = combined_df.apply(extract_skills, axis=1)
    final_df = pd.concat([combined_df, skills_df], axis=1)
    final_df['date_scraped'] = datetime.now().strftime('%Y-%m-%d')

    final_df.to_csv('data/all_market_data_with_skills.csv', index=False)
    log(f"Combined dataset saved: {len(final_df)} jobs")

except Exception as e:
    log(f"Combine error: {e}")

log(f"Run completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
log("="*50)