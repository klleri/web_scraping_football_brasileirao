import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

# Define the years you want to collect 
years_to_scrape = list(range(2024, 2022, -1)) # Will get 2024 and 2023


base_standings_url = "https://fbref.com/en/comps/24/{year}/{year}-Serie-A-Stats"

all_matches_data = [] # List to store DataFrames for each team/year
request_delay = 5.5 # Seconds to wait between requests to avoid overloading the site

print(f"Starting scraping for years: {years_to_scrape}")

# --- Main Loop by Year ---
for year in years_to_scrape:
    standings_url = base_standings_url.format(year=year)
    print(f"\n Processing Year: {year}")
    print(f"Fetching standings from: {standings_url}")

    try:
        standings_response = requests.get(standings_url)
        standings_response.raise_for_status() # Check for HTTP errors
        time.sleep(request_delay)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching standings for {year}: {e}")
        print("Skipping to the next year...")
        continue

    # Team Link Extraction
    standings_soup = BeautifulSoup(standings_response.text, 'html.parser') 

    # Try to find the standings table (the ID might change, inspect the page)
    # <table class="stats_table sortable min_width force_mobilize" id="results2024_24_1" data-cols-to-freeze=",1">
    standings_table = standings_soup.select_one(f'table#results{year}_24_1') 
    if not standings_table:
         standings_table = standings_soup.select_one('table.stats_table')

    if not standings_table:
        print(f"Could not find standings table for {year} at {standings_url}")
        print("Skipping to the next year...")
        continue

    team_links = [a.get("href") for a in standings_table.find_all('a')]
    team_links = [link for link in team_links if link and '/squads/' in link]
    team_urls = [f"https://fbref.com{link}" for link in team_links]

    if not team_urls:
        print(f"Could not find any team links for {year}.")
        continue

    print(f"Found {len(team_urls)} teams for {year}.")

    # Loop Through Teams
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        print("  Processing team: {team_name} ({year})")

        try:
            # Team Page Request
            team_response = requests.get(team_url)
            team_response.raise_for_status()
            time.sleep(request_delay) # Wait

            team_page_content = team_response.text # Store the HTML to reuse

            # "Scores & Fixtures" Table Extraction
            try:
                matches = pd.read_html(StringIO(team_page_content), match="Scores & Fixtures")[0]
                print("    'Scores & Fixtures' table found.")
            except ValueError:
                print("    WARNING: 'Scores & Fixtures' table not found for {team_name} ({year}). Skipping team.")
                continue # Skip to the next team

            # "Shooting" Link and Data Extraction
            team_soup = BeautifulSoup(team_page_content, 'html.parser')
            shooting_links = [a.get("href") for a in team_soup.find_all('a')]
            # Specifically look for the 'all_comps' shooting link
            shooting_link = next((link for link in shooting_links if link and '/all_comps/shooting/' in link), None)

            shooting = pd.DataFrame() # Initialize DataFrame

            if shooting_link:
                shooting_url = f"https://fbref.com{shooting_link}"
                print("    Fetching 'Shooting' data from: {shooting_url}")
                try:
                    shooting_response = requests.get(shooting_url)
                    shooting_response.raise_for_status()
                    time.sleep(request_delay)

                    # Extract the Shooting table
                    try:
                        shooting = pd.read_html(StringIO(shooting_response.text), match="Shooting")[0]
                        print("    'Shooting' table found.")
                        # Clean columns (check if it's MultiIndex first)
                        if isinstance(shooting.columns, pd.MultiIndex):
                            shooting.columns = shooting.columns.droplevel()
                        else:
                             print("    WARNING: 'Shooting' table columns for {team_name} ({year}) are not MultiIndex.")
                    except ValueError:
                        print("    WARNING: 'Shooting' table not found at {shooting_url}.")
                    except Exception as e:
                         print("    ERROR processing 'Shooting' table: {e}")

                except requests.exceptions.RequestException as e:
                    print("    Error fetching shooting data for {team_name} ({year}): {e}")
                except Exception as e: 
                     print("    UNEXPECTED ERROR processing shooting data for {team_name} ({year}): {e}")
            else:
                print("    WARNING: Link for 'Shooting' data not found for {team_name} ({year}).")

            # Data Merging 
            required_shooting_cols = ["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]

            # Check if the shooting table was loaded and has the necessary columns
            if not shooting.empty and all(col in shooting.columns for col in required_shooting_cols):
                try:
                    # Select only necessary columns BEFORE the merge
                    shooting_subset = shooting[required_shooting_cols]
                    # Use left merge to keep all matches, even if there's no corresponding shooting data
                    team_data = pd.merge(matches, shooting_subset, on="Date", how="left")
                    print("    'Matches' and 'Shooting' data merged.")
                except Exception as e:
                    print("    ERROR during merge for {team_name} ({year}): {e}")
                    # If merge fails, continue with only 'matches' data
                    team_data = matches.copy()
                    # Add empty columns to keep the structure consistent
                    for col in required_shooting_cols:
                         if col != "Date" and col not in team_data.columns:
                            team_data[col] = pd.NA
            else:
                if shooting.empty:
                    print("    'Shooting' data is empty or was not found. Using only 'Matches' data.")
                else:
                    print("    'Shooting' data does not contain all required columns ({required_shooting_cols}). Using only 'Matches' data.")
                    print("    Available columns in Shooting: {list(shooting.columns)}")
                # If no valid shooting data, use only matches data
                team_data = matches.copy()
                # Add empty columns to keep the structure consistent
                for col in required_shooting_cols:
                    if col != "Date" and col not in team_data.columns:
                        team_data[col] = pd.NA

            # Final Filtering and Appending to List
            # Check if 'Comp' column exists before filtering
            if "Comp" in team_data.columns:
                team_data_filtered = team_data[team_data["Comp"] == "Série A"].copy() 

                # Check if any data remains after filtering
                if not team_data_filtered.empty:
                    team_data_filtered['Season'] = year 
                    team_data_filtered['Team'] = team_name
                    all_matches_data.append(team_data_filtered)
                    print("    Added {len(team_data_filtered)} Série A matches for {team_name} ({year}).")
                else:
                    print("    No 'Série A' matches found for {team_name} ({year}) after filtering.")
            else:
                print("    WARNING: 'Comp' column not found in data for {team_name} ({year}). Cannot filter by 'Série A'.")
               

        except requests.exceptions.RequestException as e:
            print("  GENERAL request error processing {team_name} ({year}): {e}")
            # Continue to the next team
        except Exception as e: # Catch any other unexpected errors in the team loop
            print("  UNEXPECTED ERROR processing team {team_name} ({year}): {e}")
            # Continue to the next team

# --- Finalization ---
print("\nScraping finished.")

# Combine all DataFrames into a single one
if all_matches_data:
    final_df = pd.concat(all_matches_data, ignore_index=True)
    print(f"\nTotal Série A matches collected: {len(final_df)}")
    print(f"Teams collected: {final_df['Team'].unique()}")
    print(f"Seasons collected: {final_df['Season'].unique()}")
    # print(final_df.head())
    # print(final_df.info())
else:
    print("\nNo match data was collected.")
