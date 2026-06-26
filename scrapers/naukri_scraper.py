import time
import pandas as pd
from bs4 import BeautifulSoup 
from playwright.sync_api import sync_playwright

target_url="https://www.naukri.com/data-analyst-jobs"

def scrape_naukri_pages(base_url, total_pages=20, delay_seconds=8):
    print(f"Launching browser and navigating to : {base_url}")

    all_jobs = []

    with sync_playwright() as p:
        browser= p.chromium.launch(headless=False , slow_mo=50)
        context= browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        page=context.new_page()

        try:
            for page_number in range(1, total_pages + 1):
                page_url = base_url if page_number == 1 else f"{base_url}-{page_number}"
                print(f"Navigating to page {page_number}: {page_url}")
                page.goto(page_url)

                print("Waiting for job cards to load...")
                page.wait_for_selector('div.srp-jobtuple-wrapper[data-job-id], div.jobTuple', timeout=15000)

                for i in range(1,6):
                    page.mouse.wheel(0,1000)
                    page.wait_for_timeout(1000)

                html_content = page.content()
                page_jobs = parse_jobs(html_content)
                all_jobs.extend(page_jobs)

                if page_number < total_pages:
                    print(f"Waiting {delay_seconds} seconds before moving to the next page...")
                    time.sleep(delay_seconds)
        finally:
            browser.close()

    return all_jobs

def parse_jobs(html_content):
    print("Parsing HTML with BeautifulSoup...")
    soup = BeautifulSoup(html_content, "html.parser")
    
    job_cards = soup.select('div.srp-jobtuple-wrapper[data-job-id]')
    if not job_cards:
        job_cards = soup.find_all('div', class_=lambda x: x and 'jobTuple' in x)
    
    print(f" Found {len(job_cards)} job postings on this page.")
    
    scraped_jobs = []
    
    for card in job_cards:
        job_id = card.get('data-job-id', 'N/A')
        
        # Extract Job Title
        title_elem = card.select_one('h2 a.title') or card.find('a', class_='title')
        title = title_elem.text.strip() if title_elem else "N/A"
        job_url = title_elem.get('href', 'N/A') if title_elem else "N/A"
        
        # Extract Company Name
        company_elem = card.select_one('.comp-name') or card.find('a', class_=lambda x: x and 'comp-name' in x)
        if not company_elem: # Fallback class name
            company_elem = card.find('a', class_='subTitle')
        company = company_elem.text.strip() if company_elem else "N/A"
        
        # Extract Experience Required
        exp_elem = card.select_one('.expwdth') or card.find('span', class_=lambda x: x and 'expwdth' in x)
        experience = exp_elem.text.strip() if exp_elem else "N/A"
        
        # Extract Location
        loc_elem = card.select_one('.locWdth') or card.find('span', class_=lambda x: x and 'locWdth' in x)
        location = loc_elem.text.strip() if loc_elem else "N/A"
        
        desc_elem = card.select_one('.job-desc') or card.find('span', class_=lambda x: x and 'job-desc' in x)
        description = desc_elem.text.strip() if desc_elem else "N/A"
        
        date_elem = card.select_one('.job-post-day') or card.find('span', class_=lambda x: x and 'job-post-day' in x)
        posted_date = date_elem.text.strip() if date_elem else "N/A"
        
        # Extract specific Skills/Tags listed at the bottom of the card
        tags_ul = card.select_one('ul.tags') or card.find('ul', class_=lambda x: x and 'tags' in x)
        skills = []
        if tags_ul:
            for li in tags_ul.find_all('li'):
                skills.append(li.text.strip())
        
        scraped_jobs.append({
            'job_id': job_id,
            'Title': title,
            'Company': company,
            'Experience': experience,
            'Location': location,
            'Description': description,
            'Posted_Date': posted_date,
            'Skills_Listed': ", ".join(skills),
            'Job_URL': job_url
        })
        
    return scraped_jobs


if __name__ == "__main__":
    # 1. Scrape multiple pages via Playwright
    jobs_data = scrape_naukri_pages(target_url, total_pages=20, delay_seconds=5)

    # 2. Save to Pandas DataFrame and Export
    if jobs_data:
        df = pd.DataFrame(jobs_data)
        from datetime import datetime
        before = len(df)
        df = df.drop_duplicates(subset=['job_id'])
        after = len(df)
        df['date_scraped'] = datetime.now().strftime('%Y-%m-%d')
        print("\n Preview of Extracted Data:")
        print(df.head())
        
        # Save to CSV in the data folder
        csv_filename = "data/naukri_data_analyst_jobs.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\n Successfully saved {len(df)} jobs to {csv_filename}")
    else:
        print("\nWARNING: No jobs found. Naukri might have changed their CSS class names or blocked the request.")