import sys
import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

TARGET_URL = "https://www.foundit.in/srp/results?query=data+analyst&location=India"

def scrape_foundit(base_url, max_jobs=300, delay_seconds=2):
    print("Launching browser for Foundit.in...")
    all_jobs = []
    saved_jobs_key = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=30)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800} # Set a consistent viewport
        )
        page = context.new_page()

        try:
            page.goto(base_url)
            page.wait_for_timeout(5000)

            scroll_attempts = 0
            max_scroll_attempts = 100
            consecutive_no_new = 0

            # --- THE FIX: Target the scrollable list container ---
            # We hover over the first job card to ensure the mouse is positioned 
            # over the left-hand list panel before we start scrolling.
            first_card = page.query_selector('div.cardContainer')
            if first_card:
                first_card.hover()
            # -----------------------------------------------------

            while len(all_jobs) < max_jobs and scroll_attempts < max_scroll_attempts:
                cards = page.query_selector_all('div.cardContainer')
                print(f"\nVisible cards: {len(cards)} | Total saved: {len(all_jobs)}")

                # Find new cards by title+company key
                new_cards = []
                for card in cards:
                    try:
                        card_html = card.inner_html()
                        card_soup = BeautifulSoup(card_html, 'html.parser')

                        title_elem = card_soup.find('div', id='jobCardTitle') or \
                                     card_soup.find('div', class_='jobTitle')
                        temp_title = title_elem.text.strip() if title_elem else ""

                        company_elem = card_soup.find('div', class_='companyName')
                        temp_company = company_elem.find('p').text.strip() \
                            if company_elem and company_elem.find('p') else ""

                        job_key = f"{temp_title}|{temp_company}"

                        if job_key not in saved_jobs_key and temp_title:
                            new_cards.append((job_key, card, card_soup))
                    except:
                        continue

                print(f"New cards to process: {len(new_cards)}")

                if len(new_cards) == 0:
                    consecutive_no_new += 1
                    print(f"No new cards — scrolling attempt {scroll_attempts + 1}")

                    if consecutive_no_new >= 5:
                        print("5 consecutive scrolls with no new cards — stopping")
                        break
                    
                    # --- THE FIX: Scroll while hovering over the list ---
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(3000)
                    # ----------------------------------------------------
                    
                    scroll_attempts += 1
                    continue

                consecutive_no_new = 0

                for job_key, card, card_soup in new_cards:
                    if len(all_jobs) >= max_jobs:
                        break

                    try:
                        # Extract from pre-parsed card_soup
                        title_elem = card_soup.find('div', id='jobCardTitle') or \
                                     card_soup.find('div', class_='jobTitle')
                        title = title_elem.text.strip() if title_elem else "N/A"

                        company_elem = card_soup.find('div', class_='companyName')
                        company = company_elem.find('p').text.strip() \
                            if company_elem and company_elem.find('p') else "N/A"

                        exp_elem = card_soup.find('span', class_='details')
                        experience = exp_elem.text.strip() if exp_elem else "N/A"

                        loc_elem = card_soup.find(
                            'div', class_=lambda x: x and 'location' in x
                        )
                        location = loc_elem.text.strip() if loc_elem else "N/A"

                        date_elem = card_soup.find('p', class_='timeText')
                        posted_date = date_elem.text.strip() if date_elem else "N/A"

                        # India filter
                        indian_keywords = [
                            'bengaluru', 'bangalore', 'hyderabad', 'mumbai',
                            'pune', 'delhi', 'gurugram', 'noida', 'chennai',
                            'kolkata', 'ahmedabad', 'jaipur', 'india', 'remote',
                            'navi mumbai', 'thane', 'gurgaon', 'chandigarh',
                            'indore', 'nagpur', 'coimbatore', 'kochi', 'bhopal',
                            'vizag', 'surat', 'lucknow', 'bhubaneswar'
                        ]
                        if not any(kw in location.lower() for kw in indian_keywords):
                            print(f"[SKIP] Non-India: {location}")
                            saved_jobs_key.add(job_key)
                            continue

                        # Click card to load detail panel
                        card.scroll_into_view_if_needed()
                        card.click()
                        page.wait_for_timeout(2000)

                        # Extract skills
                        panel_html = page.content()
                        panel_soup = BeautifulSoup(panel_html, 'html.parser')

                        skills = []
                        pills_container = panel_soup.find('div', class_='pillsContainer')
                        if pills_container:
                            pill_items = pills_container.find_all('div', class_='pillItem')
                            skills = [pill.text.strip() for pill in pill_items
                                     if pill.text.strip()]

                        desc_elem = panel_soup.find(
                            'div', class_=lambda x: x and 'jobDescription' in x
                        ) or panel_soup.find(
                            'div', class_=lambda x: x and 'description' in x
                        )
                        description = desc_elem.text.strip()[:500] \
                            if desc_elem else "N/A"

                        all_jobs.append({
                            'job_id': job_key.replace('|', '_')[:30],
                            'Title': title,
                            'Company': company,
                            'Experience': experience,
                            'Location': location,
                            'Description': description,
                            'Posted_Date': posted_date,
                            'Skills_Listed': ', '.join(skills),
                            'Job_URL': f"https://www.foundit.in/srp/results?query=data+analyst",
                            'source': 'Foundit'
                        })

                        saved_jobs_key.add(job_key)
                        print(f"[OK] {title[:40]} | {company[:20]} | {len(skills)} skills")
                        
                        # Re-hover the list panel before scrolling to ensure we stay in the scrollable area
                        card.hover()
                        
                        time.sleep(delay_seconds)

                    except Exception as e:
                        print(f"[ERROR] {job_key}: {e}")
                        saved_jobs_key.add(job_key)
                        continue

                # Scroll after processing batch
                # Hover over the last processed card to ensure focus is on the list
                if new_cards:
                     new_cards[-1][1].hover()
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(3000)
                scroll_attempts += 1

        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            browser.close()

    return all_jobs


if __name__ == "__main__":
    jobs_data = scrape_foundit(TARGET_URL, max_jobs=300, delay_seconds=2)

    if jobs_data:
        df = pd.DataFrame(jobs_data)
        df['date_scraped'] = datetime.now().strftime('%Y-%m-%d')

        before = len(df)
        df = df.drop_duplicates(subset=['job_id'])
        print(f"\nRemoved {before - len(df)} duplicates")

        print(f"\nTotal jobs saved: {len(df)}")
        print(f"Jobs with skills: {(df['Skills_Listed'] != '').sum()} / {len(df)}")

        print(f"\nLocation distribution:")
        print(df['Location'].value_counts().head(10))

        print(f"\nPreview:")
        print(df[['Title', 'Company', 'Location', 'Skills_Listed']].head(5))
        
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/foundit_data_analyst_jobs.csv', index=False)
        print(f"\nSaved to data/foundit_data_analyst_jobs.csv")

    else:
        print("No jobs found.")