import pandas as pd
import os

def merge_datasets():
    # Ensure the output directory exists
    os.makedirs('data', exist_ok=True)

    # Define the exact file paths we are using
    naukri_file = 'data/naukri_data_analyst_jobs.csv'
    foundit_file = 'data/foundit_data_analyst_jobs.csv'
    output_file = 'data/all_market_data_raw.csv'

    print("\n" + "="*50)
    print("[*] STARTING DATA MERGER...")
    print("="*50)

    dfs = []

    if os.path.exists(naukri_file):
        try:
            df_naukri = pd.read_csv(naukri_file)
            dfs.append(df_naukri)
            print(f"[OK] Loaded {len(df_naukri)} jobs from Naukri.")
        except Exception as e:
            print(f"[ERROR] Could not read Naukri file: {e}")
    else:
        print("[WARNING] Naukri file not found. Skipping...")

    if os.path.exists(foundit_file):
        try:
            df_foundit = pd.read_csv(foundit_file)
            dfs.append(df_foundit)
            print(f"[OK] Loaded {len(df_foundit)} jobs from Foundit.")
        except Exception as e:
            print(f"[ERROR] Could not read Foundit file: {e}")
    else:
        print("[WARNING] Foundit file not found. Skipping...")

    if dfs:
        # Combine all dataframes into one
        master_df = pd.concat(dfs, ignore_index=True)
        initial_count = len(master_df)
        
        # --- THE NEWLINE FIX ---
        # This replaces any hidden "Enters" (\n) or returns (\r) with a simple space
        master_df = master_df.replace('\n', ' ', regex=True).replace('\r', ' ', regex=True)
        # -----------------------
        
        # Deduplicate across platforms based on Title and Company
        # If the exact same company posted the exact same job on both sites, we drop one.
        master_df = master_df.drop_duplicates(subset=['Title', 'Company'])
        final_count = len(master_df)
        
        print(f"\n[*] Merged dataset contains {initial_count} total scraped jobs.")
        print(f"[-] Removed {initial_count - final_count} cross-platform duplicates.")
        
        # Save the final raw master file
        master_df.to_csv(output_file, index=False)
        print(f"\n[SUCCESS] Master raw dataset saved to: {output_file}")
        print(f"[TOTAL] Total Unique Market Jobs: {final_count}")
        print("="*50 + "\n")
    else:
        print("\n[ERROR] No data files found to merge. Run your scrapers first!")

if __name__ == "__main__":
    merge_datasets()