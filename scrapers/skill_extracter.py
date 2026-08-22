import pandas as pd
import re
import os

# ensure the output directory exists
os.makedirs('data', exist_ok=True)

#Loading csv raw file
csv_file='data/all_market_data_raw.csv'
print(f"[*] Loading raw data from {csv_file}...")

try:
    df=pd.read_csv(csv_file)
    print(f"[*] Successfully loaded {len(df)} jobs.")
except FileNotFoundError:
    print(f"[!] {csv_file} not found. Make sure you ran the scraper first!")
    exit()

# Defining skill patterns using Regex
#\b = exact word match
#(?i)= for case-insensitive matching
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
    'R':                r'(?i)\b(r programming|r studio)\b',
    'Spark':            r'(?i)\b(spark|pyspark)\b',
    'Git':              r'(?i)\b(git|github)\b',
    'Pandas':           r'(?i)\b(pandas)\b',
    'NumPy':            r'(?i)\b(numpy)\b',
    'Scikit-learn':     r'(?i)\b(scikit-learn|sklearn)\b',
    'Looker':           r'(?i)\b(looker|looker studio|google data studio)\b',
    'DAX':              r'(?i)\b(dax)\b',
    'Snowflake':        r'(?i)\b(snowflake)\b',
    'ETL':              r'(?i)\b(etl|elt)\b',
    'Power Query':      r'(?i)\b(power query)\b',
    'GenAI':            r'(?i)\b(genai|generative ai|llm|prompt engineering)\b',
    'Deep Learning':    r'(?i)\b(deep learning|tensorflow|pytorch)\b',
    'NLP':              r'(?i)\b(nlp|natural language processing)\b',
    'Data Visualization': r'(?i)\b(data visualization|data viz)\b',
    'Hadoop':           r'(?i)\b(hadoop)\b',
    'Airflow':          r'(?i)\b(airflow|apache airflow)\b',
    'Docker':           r'(?i)\b(docker)\b',
    'BigQuery':         r'(?i)\b(bigquery|big query)\b',
    'SAS':              r'(?i)\b(sas)\b',
}

# extracting skills from job description
def extract_skills(row):
    # Fixed capitalization on 'Skills_Listed' to match the scraper output
    full_text=str(row['Description']).lower() + " " + str(row.get('Skills_Listed', '')).lower()

    extracted={}

    for skill,pattern in SKILL_PATTERNS.items():
        extracted[skill] = 1 if re.search(pattern,full_text) else 0
    return pd.Series(extracted)

#creating a dataframe with extracted skills
print("[*] Extracting skills from job descriptions...")
skills_df = df.apply(extract_skills, axis=1)

cleaned_df = pd.concat([df, skills_df], axis=1)

#printing report
print("\n" + "="*45)
print("      INDIA DA JOB MARKET INTELLIGENCE")
print("="*45)
print(f"Total Jobs Analyzed: {len(cleaned_df)}")
print("-"*45)

#sorting skills by demand
skill_counts = {}

for skill in SKILL_PATTERNS.keys():
    skill_counts[skill] = cleaned_df[skill].sum()

sorted_skills = sorted(
    skill_counts.items(),
    key=lambda x: x[1],
    reverse=True
)

#visuals
print(f"{'Skill':<22} {'Jobs':>5}   {'Demand %':>8}")
print("-"*45)
for skill, count in sorted_skills:
    percentage = (count / len(cleaned_df)) * 100
    bar = '#' * int(percentage / 5)  # visual bar
    print(f"{skill:<22} {count:>5}   {percentage:>6.1f}%  {bar}")

print("="*45)

print(f"\n[*] Skills per job:")
skill_columns = list(SKILL_PATTERNS.keys())
cleaned_df['total_skills_found'] = cleaned_df[skill_columns].sum(axis=1)
print(f"    Average : {cleaned_df['total_skills_found'].mean():.1f} skills per job")
print(f"    Max     : {cleaned_df['total_skills_found'].max()} skills in one job")
print(f"    Min     : {cleaned_df['total_skills_found'].min()} skills in one job")
print(f"    Jobs with 0 skills matched: {(cleaned_df['total_skills_found'] == 0).sum()}")

# Save the DataFrame with extracted skills
output_file = "data/all_market_data_with_skills.csv"
cleaned_df.to_csv(output_file, index=False)
print(f"\n[*] Saved dataset with skill flags to {output_file}")