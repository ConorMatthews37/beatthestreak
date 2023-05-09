'''
Data from today
Features
AVG, Hits/PA, Opposing Pitcher WHIP, Opposing Pitcher BAA, Opposing Team Defense, AVG in Last 7 Days, Opposing Pitcher WHIP Last 30 Days

AVG, AVG in Last 5 Games
https://www.mlb.com/stats/

Opposing Pitcher WHIP, Opposing Pitcher BAA, Last 30 Days
https://www.mlb.com/stats/pitching?page=2&sortState=asc&timeframe=-29

Opposing Bullpen WHIP, Opposing Bullpen BAA
https://www.mlb.com/stats/team/pitching?split=rp&sortState=asc

Opposing Team Defense (Normalize Team Defensive Runs Saved)
http://www.fieldingbible.com/TeamDefensiveRunsSaved

Tables:
Starter
Starter Name, Starter Team, Starter Stats

Hitters
Hitter Name, Hitter Team, Hitter Stats

Team
Team Name, Team Defense, Bullpen Stats
'''
import time

import schedule
import numpy as np
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pandas as pd
import sys
import os
from datetime import date
from datetime import timedelta
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from collections import defaultdict

today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
cwd = os.getcwd()
hitter_path = os.path.join(cwd, 'hitter')
team_def_path = os.path.join(cwd, 'teamDef')


if not os.path.isdir(hitter_path):
    os.mkdir(hitter_path)
if not os.path.isdir(team_def_path):
    os.mkdir(team_def_path)


team_names_dict = {
    'dbacks': 'Arizona Diamondbacks',
    'braves': 'Atlanta Braves',
    'orioles': 'Baltimore Orioles',
    'redsox': 'Boston Red Sox',
    'whitesox': 'Chicago White Sox',
    'cubs': 'Chicago Cubs',
    'reds': 'Cincinnati Reds',
    'guardians': 'Cleveland Guardians',
    'rockies': 'Colorado Rockies',
    'tigers': 'Detroit Tigers',
    'astros': 'Houston Astros',
    'royals': 'Kansas City Royals',
    'angels': 'Los Angeles Angels',
    'dodgers': 'Los Angeles Dodgers',
    'marlins': 'Miami Marlins',
    'brewers': 'Milwaukee Brewers',
    'twins': 'Minnesota Twins',
    'yankees': 'New York Yankees',
    'mets': 'New York Mets',
    'athletics': 'Oakland Athletics',
    'phillies': 'Philadelphia Phillies',
    'pirates': 'Pittsburgh Pirates',
    'padres': 'San Diego Padres',
    'giants': 'San Francisco Giants',
    'mariners': 'Seattle Mariners',
    'cardinals': 'St. Louis Cardinals',
    'rays': 'Tampa Bay Rays',
    'rangers': 'Texas Rangers',
    'bluejays': 'Toronto Blue Jays',
    'nationals': 'Washington Nationals',
    'Arizona Diamondbacks': 'dbacks',
    'Atlanta Braves': 'braves',
    'Baltimore Orioles': 'orioles',
    'Boston Red Sox': 'redsox',
    'Chicago White Sox': 'whitesox',
    'Chicago Cubs': 'cubs',
    'Cincinnati Reds': 'reds',
    'Cleveland Guardians': 'guardians',
    'Colorado Rockies': 'rockies',
    'Detroit Tigers': 'tigers',
    'Houston Astros': 'astros',
    'Kansas City Royals': 'royals',
    'Los Angeles Angels': 'angels',
    'Los Angeles Dodgers': 'dodgers',
    'Miami Marlins': 'marlins',
    'Milwaukee Brewers': 'brewers',
    'Minnesota Twins': 'twins',
    'New York Yankees': 'yankees',
    'New York Mets': 'mets',
    'Oakland Athletics': 'athletics',
    'Philadelphia Phillies': 'phillies',
    'Pittsburgh Pirates': 'pirates',
    'San Diego Padres': 'padres',
    'San Francisco Giants': 'giants',
    'Seattle Mariners': 'mariners',
    'St Louis Cardinals': 'cardinals',
    'Tampa Bay Rays': 'rays',
    'Texas Rangers': 'rangers',
    'Toronto Blue Jays': 'bluejays',
    'Washington Nationals': 'nationals'
}

games_url_yesterday = f'https://www.mlb.com/scores/{yesterday}'
games_url_tomorrow = f'https://www.mlb.com/scores/{tomorrow}'
batting_url = 'https://www.mlb.com/stats/'
starter_url = 'https://www.mlb.com/stats/pitching?page=2&sortState=asc&timeframe=-29'
team_fielding_url = 'http://www.fieldingbible.com/TeamDefensiveRunsSaved'
team_games_url = 'https://www.mlb.com/stats/team'
team_pitching_url = 'https://www.mlb.com/stats/team/pitching?split=rp'



team_regex = re.compile('.*TeamTableWrapper.*')
player_regex = re.compile('.*PlayerLink.*')
griditem_regex = re.compile('.*GridItemWrapper.*')
teamwrapper_regex = re.compile('.*teamstyle__OuterWrapper.*')
playermatchup_regex = re.compile('.*PlayerMatchupLayer.*')
substitute_regex = re.compile('.*SubstitutePlayerWrapper.*')

#Add check for if starter changed. Don't include data
# Modify yesterday's date specific csv, remove rows that had 1 PA or less (if PA not in box AB + BB). Append to master
def getYesterdayHits(date):
    # Gets yesterday's hitter df
    yesterday_hitter_df = pd.read_csv(os.path.join(hitter_path, f'hitter{date}.csv'))
    yesterday_hitter_df['hitterID'] = yesterday_hitter_df['hitterID'].astype(int)
    yesterday_hitter_df['hitterID'] = yesterday_hitter_df['hitterID'].astype(str)
    yesterday_hitter_df['gameID'] = yesterday_hitter_df['gameID'].astype(str)
    yesterday_missing = yesterday_hitter_df[yesterday_hitter_df['hitsInGame'].isnull()]
    yesterday_missing_game_ids = yesterday_missing['gameID'].unique()

    yesterday_teamdef_df = pd.read_csv(os.path.join(team_def_path, f'teamDef{date}.csv'))
    yesterday_teamdef_df['gameID'] = yesterday_teamdef_df['gameID'].astype(int)
    yesterday_teamdef_df['starterID'] = yesterday_teamdef_df['starterID'].astype(int)
    yesterday_teamdef_df['gameID'] = yesterday_teamdef_df['gameID'].astype(str)
    yesterday_teamdef_df['starterID'] = yesterday_teamdef_df['starterID'].astype(str)



    # Gets yesterday's mlb.com/scores page HTML
    yesterday_request = requests.get(games_url_yesterday)
    soup = BeautifulSoup(yesterday_request.text, "html.parser")

    # Selects anchors with a link to a game's box score
    yesterday_anchors = soup.find_all('a', class_="trk-box")

    # Gets urls to box scores for each game
    yesterday_urls = []
    for game_anchor in yesterday_anchors:
        link = game_anchor['href']
        yesterday_urls.append(link)

    for url in yesterday_urls:

        # Gets game id from url
        game_id = url.split('/')[4]

        if game_id not in yesterday_missing_game_ids:
            continue

        # Loads page with chromedriver because it redirects from simple url to actual page. FTF might want to get full url and use requests to be faster
        browser.get(url)
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-mlb-test=gamedayBoxscoreTeamTable]')))
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Gets team names
        team_names = browser.current_url.split('/')[4].split('-vs-')
        away_team_name, home_team_name = team_names[0], team_names[1]

        # Gets all "TeamTable" boxes
        team_divs = soup.find_all('div', class_=team_regex)

        #This selects the hitting boxes. Away pitching would be at index 1, home pitching at index 3
        hitter_divs = (team_divs[0], team_divs[2])

        away_starter_id = team_divs[1].select_one('tbody').find('tr').find('a', class_=player_regex, href=True)['href'].split('/')[4]
        home_starter_id = team_divs[3].select_one('tbody').find('tr').find('a', class_=player_regex, href=True)['href'].split('/')[4]

        away_team_row = yesterday_teamdef_df.loc[(yesterday_teamdef_df['gameID'] == game_id) & (yesterday_teamdef_df['defTeamName'] == away_team_name)]
        home_team_row = yesterday_teamdef_df.loc[(yesterday_teamdef_df['gameID'] == game_id) & (yesterday_teamdef_df['defTeamName'] == home_team_name)]
        if not away_team_row.empty:
            if away_starter_id != away_team_row['starterID'].iloc[0]:
                yesterday_hitter_df = yesterday_hitter_df.drop(yesterday_hitter_df[(yesterday_hitter_df['gameID'] == game_id) & (yesterday_hitter_df['hitTeamName'] != away_team_name)].index)
                yesterday_teamdef_df = yesterday_teamdef_df.drop(yesterday_teamdef_df[(yesterday_teamdef_df['gameID'] == game_id) & (yesterday_teamdef_df['defTeamName'] == away_team_name)].index)
                print(f'{away_team_name} Starting Pitcher Changed in Game {game_id}. Removing Corresponding Rows in Tables and Skipping.')
            else:
                pass

        if not home_team_row.empty:
            if home_starter_id != home_team_row['starterID'].iloc[0]:
                yesterday_hitter_df = yesterday_hitter_df.drop(yesterday_hitter_df[(yesterday_hitter_df['gameID'] == game_id) & (yesterday_hitter_df['hitTeamName'] != home_team_name)].index)
                yesterday_teamdef_df = yesterday_teamdef_df.drop(yesterday_teamdef_df[(yesterday_teamdef_df['gameID'] == game_id) & (yesterday_teamdef_df['defTeamName'] == home_team_name)].index)
                print(f'{home_team_name} Starting Pitcher Changed in Game {game_id}. Removing Corresponding Rows in Tables and Skipping.')
            else:
                pass

        for hitter_div in hitter_divs:
            box = hitter_div.select_one('tbody')
            rows = box.find_all('tr')
            lineup = 1

            #Last row is empty
            for row in rows[:-1]:
                # Only include players who were in the starting lineup
                substitute_span = row.find('span', class_=substitute_regex)
                if not substitute_span:
                    player_anchor = row.find('a', class_=player_regex, href=True)
                    hitter_id = player_anchor['href'].split('/')[4]
                    cols = row.select('td')
                    hits_in_game = int(cols[2].find('span').text)
                    yesterday_hitter_df.loc[(yesterday_hitter_df['hitterID'] == hitter_id) & (yesterday_hitter_df['gameID'] == game_id), 'lineup'] = lineup
                    yesterday_hitter_df.loc[(yesterday_hitter_df['hitterID'] == hitter_id) & (yesterday_hitter_df['gameID'] == game_id), 'hitsInGame'] = hits_in_game
                    lineup += 1

    yesterday_hitter_df.to_csv(os.path.join(hitter_path, f'hitter{date}.csv'), index=False)
    yesterday_teamdef_df.to_csv(os.path.join(team_def_path, f'teamDef{date}.csv'), index=False)

#When loading data for preview try before all games start. If starters missing try again intermittently. If gameid has been
#filled don't bother checking again

def find(browser):
    button = browser.find_element(By.CSS_SELECTOR, '[aria-label=Expanded]')
    if button:
        return button
    else:
        browser.refresh()
        return False

def find2(browser):
    table = browser.find_element(By.CLASS_NAME, 'notranslate')
    if table:
        return table
    else:
        browser.refresh()
        return False

# Get data for today's games to be played
def getTodayStats(date):
    games_url_today = f'https://www.mlb.com/scores/{date}'

    # Initialize defaultdict for hitter stats (easier for keeping data indexed from two different pages)
    hitter_dict_draft = defaultdict(list)
    team_to_game_id = defaultdict(list)
    current_hitters = []
    hitters_ytd = []
    hitters_matchup = []

    # Initialize dictionary that will become DataFrame
    hitter_dict = {
        'hitterID': [],
        'hitterNames': [],
        'gameID': [],
        'hitTeamName': [],
        'defTeamName': [],
        'hits': [],
        'pas': [],
        'avg': [],
        'avgl7': [],
        'walks': [],
        'strikeouts': [],
        'babip': [],
        'matchupAvg': []
    }

    team_stats_dict = {
        'gameID': [],
        'defTeamName': [],
        'defRunsSaved': [],
        'bullpenWHIP': [],
        'bullpenBAA': [],
        'starterWHIP': [],
        'starterBAA': [],
        'starterl3ip': [],
        'starterl3hits': [],
        'starterID': [],
        'G': []
    }
    team_games_dict = {}
    team_matchup_dict = {}
    team_defense_dict = defaultdict(list)
    team_starter_dict = {}

    # Get team games played
    team_games_request = requests.get(team_games_url)
    soup = BeautifulSoup(team_games_request.text, "html.parser")
    rows = soup.find_all('tr')[1:]
    for row in rows:
        team_name = row.find('a')['href'].split('/')[1]
        team_games_dict[team_name] = int(row.select('td')[1].text)

    # Get team defense stats
    browser.get(team_fielding_url)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find_all('table')[2]
    rows = table.select('tr', class_='odd even')
    for row in rows[4:]:
        cols = row.select('td')
        team_name = cols[1].text.strip()
        def_runs_saved = int(cols[14].text.strip())
        team_defense_dict[team_names_dict[team_name]].append(def_runs_saved)

    # Gets today's mlb.com/scores page HTML
    today_request = requests.get(games_url_today)
    soup = BeautifulSoup(today_request.text, "html.parser")

    # Selects divs that have a grid item (divs with info for a game preview)
    today_divs = soup.find_all('div', class_=griditem_regex)

    # Get existing starter ids so we don't add duplicate data
    team_def_path = os.path.join(cwd, 'teamDef')
    team_def_file = os.path.join(team_def_path, f'teamDef{date}.csv')
    if os.path.exists(team_def_file):
        existing_df = pd.read_csv(team_def_file)
        existing_starter_ids = existing_df.starterID.astype(str).unique()
    else:
        existing_starter_ids = []

    # Iterate over games
    for today_div in today_divs:

        # Make sure game hasn't started or ended yet. This would affect stats and probably make scraping harder
        start_time_div = None
        start_time_div = today_div.select('div[data-mlb-test="gameStartTimesStateLabel"]')
        if start_time_div:
            start_time_div = start_time_div[0]
        else:
            print('Game Ended. Skipping.')
            continue
        start_time = start_time_div.text
        if 'ET' not in start_time:
            print('Game Started. Skipping.')
            continue

        #get game id
        preview_anchors = today_div.select('a', class_='trk-gameday trk-preview')

        # The second to last anchor seems to consistently be what I want with this selector regardless of whether the button says Gameday or Preview
        game_id = preview_anchors[-2]['href'].split('/')[4]

        pitcher_matchup = today_div.find('div', class_=playermatchup_regex)
        pitcher_spots = pitcher_matchup.findChildren(recursive=False)[0].findChildren(recursive=False)[1].findChildren(recursive=False)

        away_pitcher_id = None
        home_pitcher_id = None
        # Away pitcher is decided
        if pitcher_spots[0].name == 'a':
            pitcher_anchor = pitcher_spots[0]
            away_pitcher_id = pitcher_anchor['href'].split('/')[4].split('-')[2]

        if pitcher_spots[1].name == 'a':
            pitcher_anchor = pitcher_spots[1]
            home_pitcher_id = pitcher_anchor['href'].split('/')[4].split('-')[2]

        # For some reason there are two divs with the same exact content?
        team_wrappers = today_div.find_all('div', class_=teamwrapper_regex)[:2]

        team_base_urls = [team_wrapper.find('a')['href'] for team_wrapper in team_wrappers]
        use_team_base_urls = []
        # Only include team if opposing pitcher is decided
        away_team_name = team_base_urls[0].split('/')[3]
        home_team_name = team_base_urls[1].split('/')[3]

        team_matchup_dict[away_team_name] = home_team_name
        team_matchup_dict[home_team_name] = away_team_name

        if home_pitcher_id and home_pitcher_id not in existing_starter_ids:
            team_to_game_id[home_team_name] = game_id
            team_to_game_id[away_team_name] = game_id
            use_team_base_urls.append(team_base_urls[0])

            # Get home pitcher stats
            home_pitcher_url = f'https://mlb.com/player/{home_pitcher_id}'
            browser.get(home_pitcher_url)
            time.sleep(2)
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            career_div = soup.find('div', id='careerTable')
            career_table = career_div.find('table')
            rows = career_table.select('tr')
            current_row = rows[-2]
            cols = current_row.select('td')
            home_pitcher_whip = float(cols[24].text)
            home_pitcher_baa = float(cols[23].text)
            throws = soup.find('div', class_="player-header--vitals").select('li')[1].text.split('/')[2]

            last_3_div = soup.find('div', class_='player-splits--last-3')

            if last_3_div:
                last_3_table = last_3_div.find('table')
                rows = last_3_table.select('tr')
                innings_l3 = 0
                hits_l3 = 0
                for row in rows[1:]:
                    cols = row.select('td')
                    temp_innings = float(cols[4].text)
                    temp_innings = int(temp_innings) + (temp_innings - int(temp_innings)) * 10 / 3
                    innings_l3 += temp_innings
                    hits_l3 += int(cols[5].text)

                team_starter_dict[(game_id, home_team_name)] = (home_pitcher_whip, home_pitcher_baa, round(innings_l3, 2), hits_l3, home_pitcher_id, throws)
            else:
                pass

        if away_pitcher_id and away_pitcher_id not in existing_starter_ids:
            team_to_game_id[home_team_name] = game_id
            team_to_game_id[away_team_name] = game_id
            use_team_base_urls.append(team_base_urls[1])

            # Get away pitcher stats
            away_pitcher_url = f'https://mlb.com/player/{away_pitcher_id}'
            browser.get(away_pitcher_url)
            wait = WebDriverWait(browser, 10)
            wait.until(EC.visibility_of_element_located((By.ID, "careerTable")))
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            career_div = soup.find('div', id='careerTable')
            career_table = career_div.find('table')
            rows = career_table.select('tr')
            current_row = rows[-2]
            cols = current_row.select('td')
            away_pitcher_whip = float(cols[24].text)
            away_pitcher_baa = float(cols[23].text)
            throws = soup.find('div', class_="player-header--vitals").select('li')[1].text.split('/')[2]

            last_3_div = soup.find('div', class_='player-splits--last-3')
            if last_3_div:
                last_3_table = last_3_div.find('table')
                rows = last_3_table.select('tr')
                innings_l3 = 0
                hits_l3 = 0
                for row in rows[1:]:
                    cols = row.select('td')
                    temp_innings = float(cols[4].text)
                    temp_innings = int(temp_innings) + (temp_innings - int(temp_innings)) * 10 / 3
                    innings_l3 += temp_innings
                    hits_l3 += int(cols[5].text)

                team_starter_dict[(game_id, away_team_name)] = (away_pitcher_whip, away_pitcher_baa, round(innings_l3, 2), hits_l3, away_pitcher_id, throws)
            else:
                pass

        for team_base_url in use_team_base_urls:

            hit_team_name = team_base_url.split('/')[3]
            def_team_name = team_matchup_dict[hit_team_name]

            # Get hitter stats from last 7 days
            browser.get(team_base_url + '/stats/plate-appearances?timeframe=-6')
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find('tbody')
            rows = table.select('tr')
            for row in rows:
                header = row.find('th')
                hitter_anchor = header.find('a')
                hitter_id = hitter_anchor['href'].split('/')[2]
                hitter_name = hitter_anchor['aria-label']
                cols = row.select('td')
                player_avg_l7 = cols[13].text
                hitter_dict_draft[(game_id, hitter_id)].append(hitter_name)
                hitter_dict_draft[(game_id, hitter_id)].append(game_id)
                hitter_dict_draft[(game_id, hitter_id)].append(hit_team_name)
                hitter_dict_draft[(game_id, hitter_id)].append(def_team_name)
                hitter_dict_draft[(game_id, hitter_id)].append(player_avg_l7)

            current_hitters = list(hitter_dict_draft)

            # Need to remove last 7 days hitters who don't have enough PAs on the year to show up on first page of year to date

            browser.get(team_base_url + '/stats/plate-appearances')
            time.sleep(2)
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find('tbody')
            rows = table.select('tr')
            for row in rows:
                header = row.find('th')
                hitter_anchor = header.find('a')
                hitter_id = hitter_anchor['href'].split('/')[2]
                if (game_id, hitter_id) in current_hitters:
                    hitters_ytd.append((game_id, hitter_id))
                    cols = row.select('td')
                    player_hits = cols[4].text
                    player_walks = cols[9].text
                    player_strikeouts = cols[10].text
                    player_avg = cols[13].text
                    hitter_dict_draft[(game_id, hitter_id)].append(player_hits)
                    hitter_dict_draft[(game_id, hitter_id)].append(player_walks)
                    hitter_dict_draft[(game_id, hitter_id)].append(player_strikeouts)
                    hitter_dict_draft[(game_id, hitter_id)].append(player_avg)



            # Switch to expanded stats
            ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)
            button = WebDriverWait(browser, 10, ignored_exceptions=ignored_exceptions).until(find)
            button.click()
            button = WebDriverWait(browser, 10, ignored_exceptions=ignored_exceptions).until(find)
            button.click()
            button = WebDriverWait(browser, 10, ignored_exceptions=ignored_exceptions).until(find)
            button.click()
            wait = WebDriverWait(browser, 10)
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "notranslate")))
            time.sleep(6)
            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find('tbody')
            rows = table.select('tr')
            for row in rows:
                header = row.find('th')
                hitter_anchor = header.find('a')
                hitter_id = hitter_anchor['href'].split('/')[2]
                if (game_id, hitter_id) in current_hitters:
                    cols = row.select('td')
                    hitter_pas = cols[1].text
                    hitter_babip = cols[10].text
                    hitter_dict_draft[(game_id, hitter_id)].append(int(hitter_pas))
                    hitter_dict_draft[(game_id, hitter_id)].append(hitter_babip)

            # Remove hitters not on year to date first page
            for hitter in current_hitters:
                if hitter not in hitters_ytd:
                    hitter_dict_draft.pop(hitter)
            current_hitters = list(hitter_dict_draft)

            teams_with_starter = list(team_starter_dict)
            def_team_name = team_matchup_dict[hit_team_name]
            if (game_id, def_team_name) in teams_with_starter:
                throws = team_starter_dict[(game_id, def_team_name)][5].lower()
                matchup_url = team_base_url + '/stats/plate-appearances?split=v' + throws
                browser.get(matchup_url)
                time.sleep(2)
                html = browser.page_source
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find('tbody')
                rows = table.select('tr')
                for row in rows:
                    header = row.find('th')
                    hitter_anchor = header.find('a')
                    hitter_id = hitter_anchor['href'].split('/')[2]
                    if (game_id, hitter_id) in current_hitters:
                        hitters_matchup.append((game_id, hitter_id))
                        cols = row.select('td')
                        matchup_avg = cols[13].text
                        hitter_dict_draft[(game_id, hitter_id)].append(matchup_avg)

            # Remove hitters not on year to date first page
            for hitter in current_hitters:
                if hitter not in hitters_matchup:
                    hitter_dict_draft.pop(hitter)

    # Get team bullpen stats
    team_pitching_request = requests.get(team_pitching_url)
    soup = BeautifulSoup(team_pitching_request.text, "html.parser")
    rows = soup.find_all('tr')[1:]
    for row in rows:
        team_name = row.find('a')['href'].split('/')[1]
        team_bullpen_whip = float(row.select('td')[18].text)
        team_bullpen_baa = float(row.select('td')[19].text)
        team_defense_dict[team_name].append(team_bullpen_whip)
        team_defense_dict[team_name].append(team_bullpen_baa)

    active_def_teams = list(team_starter_dict)
    for def_team in active_def_teams:
        game_id = def_team[0]
        team_name = def_team[1]
        team_stats_dict['gameID'].append(game_id)
        team_stats_dict['defTeamName'].append(team_name)
        team_stats_dict['G'].append(team_games_dict[team_name])
        team_stats_dict['bullpenWHIP'].append(team_defense_dict[team_name][1])
        team_stats_dict['bullpenBAA'].append(team_defense_dict[team_name][2])
        team_stats_dict['defRunsSaved'].append(team_defense_dict[team_name][0])
        team_stats_dict['starterWHIP'].append(team_starter_dict[def_team][0])
        team_stats_dict['starterBAA'].append(team_starter_dict[def_team][1])
        team_stats_dict['starterl3ip'].append(team_starter_dict[def_team][2])
        team_stats_dict['starterl3hits'].append(team_starter_dict[def_team][3])
        team_stats_dict['starterID'].append(team_starter_dict[def_team][4])


    # Get hitter_dict from hitter_dict_draft
    current_hitters = list(hitter_dict_draft)
    for key in current_hitters:
        game_id = key[0]
        hitter_id = key[1]
        hit_team_name = hitter_dict_draft[key][2]
        def_team_name = team_matchup_dict[hit_team_name]
        if (game_id, def_team_name) in active_def_teams:
            print(hitter_id)
            hitter_dict['hitterID'].append(hitter_id)
            hitter_dict['hitterNames'].append(hitter_dict_draft[key][0])
            hitter_dict['gameID'].append(hitter_dict_draft[key][1])
            hitter_dict['hitTeamName'].append(hit_team_name)
            hitter_dict['defTeamName'].append(def_team_name)
            hitter_dict['avgl7'].append(hitter_dict_draft[key][4])
            hitter_dict['hits'].append(hitter_dict_draft[key][5])
            hitter_dict['walks'].append(hitter_dict_draft[key][6])
            hitter_dict['strikeouts'].append(hitter_dict_draft[key][7])
            hitter_dict['avg'].append(hitter_dict_draft[key][8])
            hitter_dict['pas'].append(hitter_dict_draft[key][9])
            hitter_dict['babip'].append(hitter_dict_draft[key][10])
            hitter_dict['matchupAvg'].append(hitter_dict_draft[key][11])

    # Convert dictionaries to DataFrames
    hitter_df = pd.DataFrame(hitter_dict)
    print(hitter_df)
    hitter_df = hitter_df[hitter_df['pas'] >= 20]
    hitter_df = hitter_df[(hitter_df != '-.--').all(axis=1)]
    hitter_df = hitter_df[(hitter_df != '.---').all(axis=1)]
    hitter_df['lineup'] = np.nan
    hitter_df['hitsInGame'] = np.nan
    team_df = pd.DataFrame(team_stats_dict)

    return hitter_df, team_df


def outputTodayStats(date):
    hitter_df, team_df = getTodayStats(date)
    hitter_file = os.path.join(hitter_path, f'hitter{date}.csv')
    team_file = os.path.join(team_def_path, f'teamDef{date}.csv')
    if os.path.exists(hitter_file):
        hitter_df_current = pd.read_csv(hitter_file)
        hitter_df_master = pd.concat([hitter_df_current, hitter_df])
        hitter_df_master = hitter_df_master.drop_duplicates(subset=['gameID', 'hitterID'], keep='last')
        hitter_df_master.to_csv(hitter_file, index=False)
    else:
        hitter_df.to_csv(hitter_file, index=False)
    if os.path.exists(team_file):
        team_df_current = pd.read_csv(team_file)
        team_df_master = pd.concat([team_df_current, team_df])
        team_df_master = team_df_master.drop_duplicates(subset=['gameID', 'defTeamName'], keep='last')
        team_df_master.to_csv(team_file, index=False)
    else:
        team_df.to_csv(team_file, index=False)

    return True


def performScraping():
    date = today
    error_count = 0
    result = None
    while result is None:
        try:
            result = outputTodayStats(date)
        except:
            error_count += 1
            print(f'Error number {error_count}')
    print(f'Failed {error_count} times')


s = Service('C:/Users/conor/chromedriver.exe')
browser = webdriver.Chrome(service=s)

outputTodayStats(tomorrow)
#getYesterdayHits(yesterday)

'''
schedule.every().day.at("04:00").do(performScraping)

while True:
    schedule.run_pending()
    time.sleep(60) # wait one minute
    '''

browser.close()
