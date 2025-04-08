# Brazilian Série A Match Data: Scraper (fbref.com) and Outcome Prediction

## Description

This Python script scrapes historical football match data for teams participating in the Brazilian Série A league from the website [fbref.com](https://fbref.com/). It collects information from the "Scores & Fixtures" and "Shooting" tables for each team across specified seasons.

The script is designed to handle potential issues like missing data tables or HTTP request errors and includes delays between requests to be respectful to the source website's servers.

## Features

* Scrapes match data for specified years (currently configured for 2024 and 2023).
* Fetches team URLs from the main league standings page for each season.
* Extracts "Scores & Fixtures" data for each team.
* Extracts detailed "Shooting" statistics (Shots, Shots on Target, Distance, Free Kicks, Penalties) for each team, when available.
* Merges "Scores & Fixtures" data with corresponding "Shooting" data based on the match date.
* Handles cases where "Shooting" data might be missing or incomplete.
* Filters the collected data to include only matches from the "Série A" competition.
* Adds 'Season' and 'Team' identifiers to the data.
* Includes configurable delays between web requests to prevent overloading the server.

## How it Works

1.  **Initialization:** Defines the years to scrape and the base URL structure.
2.  **Year Iteration:** Loops through each specified year.
3.  **Standings Fetch:** Retrieves the league standings page for the current year to get links to individual team pages.
4.  **Team Iteration:** Loops through each team found in the standings.
5.  **Data Fetching:**
    * Retrieves the main team page.
    * Parses the "Scores & Fixtures" table using pandas.
    * Finds the link to the "Shooting" statistics page (usually under 'all_comps').
    * Retrieves the "Shooting" page and parses the relevant table.
6.  **Data Merging:** Merges the "Scores & Fixtures" data with selected columns from the "Shooting" data using the 'Date' column. If shooting data is unavailable, it proceeds with only match data, adding placeholder columns.
7.  **Filtering & Augmenting:** Filters the combined data for "Série A" competition matches and adds 'Season' and 'Team' information.
8.  **Aggregation:** Appends the processed data for each team/year to a master list.
9.  **Final Output:** Concatenates all collected data into a single pandas DataFrame and saves it to `matches.csv`.

## Requirements

You need Python 3 installed, along with the following libraries:

* `requests`
* `beautifulsoup4`
* `pandas`
* `lxml` (often required by `pandas.read_html`)

You can install them using pip:
```bash
pip install requests beautifulsoup4 pandas lxml
