import numpy as np
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import requests
from collections import defaultdict
import os
from datetime import date
from datetime import timedelta
import re
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from dictKeys import hit_team_names_dict, field_team_names_dict

cwd = os.getcwd()

def get_hitter_dict(date):
    s = Service('C:/Users/conor/chromedriver.exe')
    browser = webdriver.Chrome(service=s)

    if os.path.isfile(os.path.join(cwd, 'hitter', 'hitterPickles', f'hitter_dict{date}.pickle')):
        with open(os.path.join(cwd, 'hitter', 'hitterPickles', f'hitter_dict{date}.pickle'), 'rb') as handle:
            hitter_dict = pickle.load(handle)
        print(f'Hitter dictionary already exists. Delete the file if you need an update for {date}.')
        return hitter_dict

    hitters_l7 = []
    hitters_vl = []
    hitters_vr = []
    hitters_main = []
    hitters_extended = []
    hitter_dict_draft = defaultdict(list)
    hitter_dict = {
        'hitterID': [],
        'hitterName': [],
        'hitTeamName': [],
        'pas': [],
        'hits': [],
        'walks': [],
        'strikeouts': [],
        'avg': [],
        'babip': [],
        'avgl7': [],
        'avgVL': [],
        'avgVR': []
    }

    print('Getting hitter stats from last 7 games.')
    l7_url = 'https://www.mlb.com/stats/plate-appearances?page=1&playerPool=ALL&timeframe=-6'
    browser.get(l7_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pages = int(
        soup.select('div[aria-label="pagination"]')[0].findChildren(recursive=False)[0].findChildren(recursive=False)[
            -1].find('span').text)
    for page in range(1, pages + 1):
        print(f'Processing last 7 games page {page}')
        l7_url = f'https://www.mlb.com/stats/plate-appearances?page={page}&playerPool=ALL&timeframe=-6'
        browser.get(l7_url)
        time.sleep(5)
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
            team_name = cols[0].text
            hitter_dict_draft[hitter_id].append(hitter_name)
            hitter_dict_draft[hitter_id].append(team_name)
            hitter_dict_draft[hitter_id].append(player_avg_l7)
            hitters_l7.append(hitter_id)

    vl_url = 'https://www.mlb.com/stats/plate-appearances?page=1&split=vl&playerPool=ALL'
    browser.get(vl_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pages = int(
        soup.select('div[aria-label="pagination"]')[0].findChildren(recursive=False)[0].findChildren(recursive=False)[
            -1].find('span').text)
    print('Getting hitter stats from vs. lefties.')
    for page in range(1, pages + 1):
        print(f'Processing lefties page {page}')
        vl_url = f'https://www.mlb.com/stats/plate-appearances?page={page}&split=vl&playerPool=ALL'
        browser.get(vl_url)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('tbody')
        rows = table.select('tr')
        for row in rows:
            header = row.find('th')
            hitter_anchor = header.find('a')
            hitter_id = hitter_anchor['href'].split('/')[2]
            if hitter_id in hitters_l7:
                cols = row.select('td')
                vl_avg = cols[13].text
                hitter_dict_draft[hitter_id].append(vl_avg)
                hitters_vl.append(hitter_id)

    vr_url = 'https://www.mlb.com/stats/plate-appearances?page=1&split=vr&playerPool=ALL'
    browser.get(vr_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pages = int(soup.select('div[aria-label="pagination"]')[0].findChildren(recursive=False)[0].findChildren(recursive=False)[-1].find('span').text)

    print('Getting hitter stats vs. righties.')
    for page in range(1, pages + 1):
        print(f'Processing righties page {page}')
        vr_url = f'https://www.mlb.com/stats/plate-appearances?page={page}&split=vr&playerPool=ALL'
        browser.get(vr_url)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('tbody')
        rows = table.select('tr')
        for row in rows:
            header = row.find('th')
            hitter_anchor = header.find('a')
            hitter_id = hitter_anchor['href'].split('/')[2]
            if hitter_id in hitters_vl:
                cols = row.select('td')
                vr_avg = cols[13].text
                hitter_dict_draft[hitter_id].append(vr_avg)
                hitters_vr.append(hitter_id)

    main_url = 'https://www.mlb.com/stats/plate-appearances?page=1&playerPool=ALL'
    browser.get(main_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pages = int(
        soup.select('div[aria-label="pagination"]')[0].findChildren(recursive=False)[0].findChildren(recursive=False)[
            -1].find('span').text)

    print('Getting hitter stats from main.')
    for page in range(1, pages + 1):
        print(f'Processing main page {page}')
        main_url = f'https://www.mlb.com/stats/plate-appearances?page={page}&playerPool=ALL'
        browser.get(main_url)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('tbody')
        rows = table.select('tr')
        for row in rows:
            header = row.find('th')
            hitter_anchor = header.find('a')
            hitter_id = hitter_anchor['href'].split('/')[2]
            if hitter_id in hitters_vr:
                cols = row.select('td')
                player_hits = cols[4].text
                player_walks = cols[9].text
                player_strikeouts = cols[10].text
                player_avg = cols[13].text
                hitter_dict_draft[hitter_id].append(player_hits)
                hitter_dict_draft[hitter_id].append(player_walks)
                hitter_dict_draft[hitter_id].append(player_strikeouts)
                hitter_dict_draft[hitter_id].append(player_avg)
                hitters_main.append(hitter_id)

    extended_url = 'https://www.mlb.com/stats/plate-appearances?expanded=true&page=1&playerPool=ALL'
    browser.get(extended_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pages = int(
        soup.select('div[aria-label="pagination"]')[0].findChildren(recursive=False)[0].findChildren(recursive=False)[
            -1].find('span').text)

    # We won't be including players with less than 20 pas anyway, so stop loading pages after we stop seeing players with 20 pas
    stop_loading = False

    print('Getting hitter stats from extended.')
    for page in range(1, pages + 1):
        print(f'Processing extended page {page}')
        extended_url = f'https://www.mlb.com/stats/plate-appearances?expanded=true&page={page}&playerPool=ALL'
        browser.get(extended_url)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('tbody')
        rows = table.select('tr')
        for row in rows:
            header = row.find('th')
            hitter_anchor = header.find('a')
            hitter_id = hitter_anchor['href'].split('/')[2]
            if hitter_id in hitters_main:
                cols = row.select('td')
                hitter_pas = int(cols[1].text)
                if hitter_pas < 20:
                    stop_loading = True
                    break
                hitter_babip = cols[10].text
                hitter_dict_draft[hitter_id].append(hitter_pas)
                hitter_dict_draft[hitter_id].append(hitter_babip)
                hitters_extended.append(hitter_id)
        if stop_loading:
            break

    current_hitters = list(hitter_dict_draft)
    for hitter in current_hitters:
        if hitter not in hitters_extended:
            hitter_dict_draft.pop(hitter)
    current_hitters = list(hitter_dict_draft)

    for hitter in current_hitters:
        hitter_dict['hitterID'].append(hitter)
        hitter_dict['hitterName'].append(hitter_dict_draft[hitter][0])
        hitter_dict['hitTeamName'].append(hit_team_names_dict[hitter_dict_draft[hitter][1]])
        hitter_dict['pas'].append(hitter_dict_draft[hitter][9])
        hitter_dict['hits'].append(hitter_dict_draft[hitter][5])
        hitter_dict['walks'].append(hitter_dict_draft[hitter][6])
        hitter_dict['strikeouts'].append(hitter_dict_draft[hitter][7])
        hitter_dict['avg'].append(hitter_dict_draft[hitter][8])
        hitter_dict['babip'].append(hitter_dict_draft[hitter][10])
        hitter_dict['avgl7'].append(hitter_dict_draft[hitter][2])
        hitter_dict['avgVL'].append(hitter_dict_draft[hitter][3])
        hitter_dict['avgVR'].append(hitter_dict_draft[hitter][4])


    print(hitter_dict)
    hitter_pickle_path = os.path.join(cwd, 'hitter', 'hitterPickles')
    if not os.path.exists(hitter_pickle_path):
        os.makedirs(hitter_pickle_path)
    with open(os.path.join(hitter_pickle_path, f'hitter_dict{date}.pickle'), 'wb') as handle:
        pickle.dump(hitter_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return hitter_dict

def get_team_stats_dict(date):
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')

    s = Service('C:/Users/conor/chromedriver.exe')
    browser = webdriver.Chrome(chrome_options=options, service=s)

    if os.path.isfile(os.path.join(cwd, 'team', 'teamPickles', f'team_stats_dict{date}.pickle')):
        with open(os.path.join(cwd, 'team', 'teamPickles', f'team_stats_dict{date}.pickle'), 'rb') as handle:
            team_stats_dict = pickle.load(handle)
        print(f'Team stats dictionary already exists. Delete the file if you need an update for {date}.')
        return team_stats_dict

    team_fielding_url = 'http://www.fieldingbible.com/TeamDefensiveRunsSaved'
    team_games_url = 'https://www.mlb.com/stats/team'
    team_stats_dict = defaultdict(list)


    # Get team games played
    browser.get(team_games_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all('tr')[1:]
    for row in rows:
        team_name = row.find('a')['href'].split('/')[1]
        team_stats_dict[team_name].append(int(row.select('td')[1].text))


    # Get team defense stats
    browser.get(team_fielding_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find_all('table')[2]
    rows = table.select('tr', class_='odd even')
    for row in rows[4:]:
        cols = row.select('td')
        team_name = cols[1].text.strip()
        def_runs_saved = int(cols[14].text.strip())
        team_stats_dict[field_team_names_dict[team_name]].append(def_runs_saved)

    # Get team bullpen stats
    team_bullpen_url = 'https://www.mlb.com/stats/team/pitching?split=rp'
    browser.get(team_bullpen_url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all('tr')[1:]
    for row in rows:
        team_name = row.find('a')['href'].split('/')[1]
        team_bullpen_whip = float(row.select('td')[18].text)
        team_bullpen_baa = float(row.select('td')[19].text)
        team_stats_dict[team_name].append(team_bullpen_whip)
        team_stats_dict[team_name].append(team_bullpen_baa)

    print(team_stats_dict)
    team_pickle_path = os.path.join(cwd, 'team', 'teamPickles')
    if not os.path.exists(team_pickle_path):
        os.makedirs(team_pickle_path)
    with open(os.path.join(team_pickle_path, f'team_stats_dict{date}.pickle'), 'wb') as handle:
        pickle.dump(team_stats_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return team_stats_dict

def get_starter_dict(date):
    s = Service('C:/Users/conor/chromedriver.exe')
    browser = webdriver.Chrome(service=s)
    griditem_regex = re.compile('.*GridItemWrapper.*')
    playermatchup_regex = re.compile('.*PlayerMatchupLayer.*')
    teamwrapper_regex = re.compile('.*teamstyle__OuterWrapper.*')
    games_url_today = f'https://www.mlb.com/scores/{date}'


    # Gets today's mlb.com/scores page HTML
    browser.get(games_url_today)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Selects divs that have a grid item (divs with info for a game preview)
    today_divs = soup.find_all('div', class_=griditem_regex)

    # Get existing starter ids so we don't add duplicate data
    existing_starter_ids = []
    if os.path.isfile(os.path.join(cwd, 'starter', 'starterPickles', f'starter_dict{date}.pickle')):
        print(f'Starter dictionary already exists. Adding new starters for {date} if there are any updates.')
        with open(os.path.join(cwd, 'starter', 'starterPickles', f'starter_dict{date}.pickle'), 'rb') as handle:
            starter_dict = pickle.load(handle)
            for starter in starter_dict:
                existing_starter_ids.append(starter)
    else:
        starter_dict = {}

    # Iterate over games
    for today_div in today_divs:

        # Make sure game hasn't started or ended yet. This would affect stats and probably make scraping harder
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

        #get game id. Link could be to gameday or preview state page
        gameday_anchor = today_div.select('a[data-mlb-test="productlink-gameday"]')
        preveiw_anchor = today_div.select('a[data-mlb-test="productlink-preview"]')
        anchors = gameday_anchor + preveiw_anchor
        game_id = anchors[0]['href'].split('/')[4]

        pitcher_matchup = today_div.find('div', class_=playermatchup_regex)
        pitcher_spots = pitcher_matchup.findChildren(recursive=False)[0].findChildren(recursive=False)[1].findChildren(recursive=False)

        away_pitcher_id = None
        home_pitcher_id = None
        # Away pitcher is decided
        if pitcher_spots[0].name == 'a':
            pitcher_anchor = pitcher_spots[0]
            away_pitcher_id = pitcher_anchor['href'].split('/')[4].split('-')[-1]

        if pitcher_spots[1].name == 'a':
            pitcher_anchor = pitcher_spots[1]
            home_pitcher_id = pitcher_anchor['href'].split('/')[4].split('-')[-1]

        # For some reason there are two divs with the same exact content?
        team_wrappers = today_div.find_all('div', class_=teamwrapper_regex)[:2]

        team_base_urls = [team_wrapper.find('a')['href'] for team_wrapper in team_wrappers]
        # Only include team if opposing pitcher is decided
        away_team_name = team_base_urls[0].split('/')[3]
        home_team_name = team_base_urls[1].split('/')[3]

        if home_pitcher_id and home_pitcher_id not in existing_starter_ids:
            print(f'Getting starter stats for {home_team_name} in game {game_id}.')

            # Get home pitcher stats
            home_pitcher_url = f'https://mlb.com/player/{home_pitcher_id}'
            browser.get(home_pitcher_url)
            time.sleep(5)
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

                starter_dict[home_pitcher_id] = [game_id, home_team_name, home_pitcher_whip, home_pitcher_baa, round(innings_l3, 2), hits_l3, throws, away_team_name]
            else:
                print('Starter missing stats for last 3 games. Skipping.')
                pass

        if away_pitcher_id and away_pitcher_id not in existing_starter_ids:
            print(f'Getting starter stats for {away_team_name} in game {game_id}.')

            # Get away pitcher stats
            home_pitcher_url = f'https://mlb.com/player/{away_pitcher_id}'
            browser.get(home_pitcher_url)
            time.sleep(5)
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

                starter_dict[away_pitcher_id] = [game_id, away_team_name, away_pitcher_whip, away_pitcher_baa, round(innings_l3, 2), hits_l3, throws, home_team_name]
            else:
                print('Starter missing stats for last 3 games. Skipping.')
                pass

    print(starter_dict)
    starter_pickle_path = os.path.join(cwd, 'starter', 'starterPickles')
    if not os.path.exists(starter_pickle_path):
        os.makedirs(starter_pickle_path)
    with open(os.path.join(starter_pickle_path, f'starter_dict{date}.pickle'), 'wb') as handle:
        pickle.dump(starter_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return starter_dict


def picklesToCSV(date):
    hitter_csv_path = os.path.join(cwd, 'hitter', 'hitterCSVs')
    if not os.path.exists(hitter_csv_path):
        os.makedirs(hitter_csv_path)
    hitter_pickle_path = os.path.join(cwd, 'hitter', 'hitterPickles', f'hitter_dict{date}.pickle')
    if os.path.isfile(hitter_pickle_path):
        with open(hitter_pickle_path, 'rb') as handle:
            hitter_dict = pickle.load(handle)
        hitter_df = pd.DataFrame(hitter_dict)
        hitter_df.to_csv(os.path.join(hitter_csv_path, f'hitter{date}.csv'), index=False)
        print(f'Sending hitter_dict{date}.pickle to hitter_dict{date}.csv')
    else:
        print(f'Could not find hitter_dict{date}.pickle')

    team_csv_path = os.path.join(cwd, 'team', 'teamCSVs')
    if not os.path.exists(team_csv_path):
        os.makedirs(team_csv_path)
    team_pickle_path = os.path.join(cwd, 'team', 'teamPickles', f'team_stats_dict{date}.pickle')
    if os.path.isfile(team_pickle_path):
        with open(team_pickle_path, 'rb') as handle:
            team_stats_dict = pickle.load(handle)
        team_stats_df = pd.DataFrame.from_dict(team_stats_dict, orient='index', columns=['teamGames', 'defRunsSaved', 'bullpenWHIP', 'bullpenBAA']).rename_axis('defTeamName').reset_index()
        team_stats_df.to_csv(os.path.join(team_csv_path, f'team{date}.csv'), index=False)
        print(f'Sending team_stats_dict{date}.pickle to team_stats_dict{date}.csv')
    else:
        print(f'Could not find team_stats_dict{date}.pickle')

    starter_csv_path = os.path.join(cwd, 'starter', 'starterCSVs')
    if not os.path.exists(starter_csv_path):
        os.makedirs(starter_csv_path)
    starter_pickle_path = os.path.join(cwd, 'starter', 'starterPickles', f'starter_dict{date}.pickle')
    if os.path.isfile(starter_pickle_path):
        with open(os.path.join(cwd, 'starter', 'starterPickles', f'starter_dict{date}.pickle'), 'rb') as handle:
            starter_dict = pickle.load(handle)
        starter_df = pd.DataFrame.from_dict(starter_dict, orient='index', columns=['gameID', 'defTeamName', 'starterWHIP', 'starterBAA', 'starterl3ip', 'starterl3hits', 'starterThrows', 'hitTeamName']).rename_axis('starterID').reset_index()
        starter_df.to_csv(os.path.join(starter_csv_path, f'starter{date}.csv'), index=False)
        print(f'Sending starter_dict{date}.pickle to starter_dict{date}.csv')
    else:
        print(f'Could not find starter_dict{date}.pickle')
    return

def loadPickles(date):
    hitter_pickle_path = os.path.join(cwd, 'hitter', 'hitterPickles', f'hitter_dict{date}.pickle')
    if os.path.isfile(hitter_pickle_path):
        with open(hitter_pickle_path, 'rb') as handle:
            hitter_dict = pickle.load(handle)

    team_pickle_path = os.path.join(cwd, 'team', 'teamPickles', f'team_stats_dict{date}.pickle')
    if os.path.isfile(team_pickle_path):
        with open(team_pickle_path, 'rb') as handle:
            team_stats_dict = pickle.load(handle)

    starter_pickle_path = os.path.join(cwd, 'starter', 'starterPickles', f'starter_dict{date}.pickle')
    if os.path.isfile(starter_pickle_path):
        with open(starter_pickle_path, 'rb') as handle:
            starter_dict = pickle.load(handle)

    return hitter_dict, team_stats_dict, starter_dict

def loadCSVs(date):
    hitter_csv_path = os.path.join(cwd, 'hitter', 'hitterCSVs', f'hitter{date}.csv')
    if os.path.isfile(hitter_csv_path):
        hitter_df = pd.read_csv(hitter_csv_path)
    else:
        print(f'No hitter CSV for {date}')
        return

    team_csv_path = os.path.join(cwd, 'team', 'teamCSVs', f'team{date}.csv')
    if os.path.isfile(team_csv_path):
        team_stats_df = pd.read_csv(team_csv_path)
    else:
        print(f'No team CSV for {date}')
        return

    starter_csv_path = os.path.join(cwd, 'starter', 'starterCSVs', f'starter{date}.csv')
    if os.path.isfile(starter_csv_path):
        starter_df = pd.read_csv(starter_csv_path)
    else:
        print(f'No team CSV for {date}')
        return

    return hitter_df, team_stats_df, starter_df


def getMasterCSV(date):
    hitter_dict, team_stats_dict, starter_dict = loadPickles(date)
    hitter_df, team_stats_df, starter_df = loadCSVs(date)
    hitter_df = pd.DataFrame(hitter_dict)

    facing_starter_dfs = []

    starters = list(starter_dict)
    for starter in starters:
        starter_info = starter_dict[starter]
        game_id = starter_info[0]
        def_team_name = starter_info[1]
        starter_throws = starter_info[6]
        hit_team_name = starter_info[7]

        # Subset hitter df to get players on team facing current starter. Add gameID and defTeamName, then add to new hitter_dict_final
        facing_starter_df = hitter_df.loc[hitter_df['hitTeamName'] == hit_team_name].copy()
        facing_starter_df['gameID'] = game_id
        facing_starter_df['defTeamName'] = def_team_name
        if starter_throws == 'L':
            facing_starter_df = facing_starter_df.drop('avgVR', axis=1)
            facing_starter_df = facing_starter_df.rename(columns={'avgVL': 'matchupAvg'})
        else:
            facing_starter_df = facing_starter_df.drop('avgVL', axis=1)
            facing_starter_df = facing_starter_df.rename(columns={'avgVR': 'matchupAvg'})
        facing_starter_dfs.append(facing_starter_df)

    hitter_df_master = pd.concat(facing_starter_dfs)
    print(hitter_df_master)
    defense_df_master = starter_df.merge(team_stats_df, how='left', on='defTeamName')
    hitter_df_master = hitter_df_master.astype({'gameID': 'int64'})
    master_df = hitter_df_master.merge(defense_df_master, how='left', on=['gameID', 'hitTeamName', 'defTeamName'])
    master_df = master_df[['hitterID', 'hitterName', 'gameID', 'hitTeamName', 'defTeamName', 'starterID', 'pas', 'hits', 'walks', 'strikeouts', 'avg', 'babip', 'avgl7', 'matchupAvg', 'starterWHIP', 'starterBAA', 'starterl3ip', 'starterl3hits', 'teamGames', 'defRunsSaved', 'bullpenWHIP', 'bullpenBAA']]

    if not os.path.exists(os.path.join(cwd, 'master', 'drafts')):
        os.makedirs(os.path.join(cwd, 'master', 'drafts'))
    master_df.to_csv(os.path.join(cwd, 'master', 'drafts', f'master{date}.csv'), index=False)
    print(f'Master csv has been output for {date}')
    return

def getHits(date):
    team_regex = re.compile('.*TeamTableWrapper.*')
    player_regex = re.compile('.*PlayerLink.*')
    substitute_regex = re.compile('.*SubstitutePlayerWrapper.*')
    s = Service('C:/Users/conor/chromedriver.exe')
    browser = webdriver.Chrome(service=s)

    master_path = os.path.join(cwd, 'master')
    if os.path.isfile(os.path.join(master_path, 'drafts', f'master{date}.csv')):
        master_df = pd.read_csv(os.path.join(master_path, 'drafts', f'master{date}.csv'))
    else:
        print(f'No master csv for {date}.')
        return
    master_df['lineup'] = np.nan
    master_df['hitsInGame'] = np.nan
    master_df = master_df.astype({'gameID': str, 'hitterID': str, 'starterID': str})
    yesterday_game_ids = master_df['gameID'].unique()
    for game_id in yesterday_game_ids:
        game_url = f'https://mlb.com/gameday/{game_id}#game_state=final,game_tab=box'
        browser.get(game_url)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Gets team names
        team_names = browser.current_url.split('/')[4].split('-vs-')
        away_team_name, home_team_name = team_names[0], team_names[1]

        # Gets all "TeamTable" boxes
        team_divs = soup.find_all('div', class_=team_regex)
        if not team_divs:
            print(f'Game {game_id} may have been postponed. Skipping.')
            continue

        # This selects the hitting boxes. Away pitching would be at index 1, home pitching at index 3
        hitter_divs = (team_divs[0], team_divs[2])

        away_starter_id = team_divs[1].select_one('tbody').find('tr').find('a', class_=player_regex, href=True)['href'].split('/')[4]
        home_starter_id = team_divs[3].select_one('tbody').find('tr').find('a', class_=player_regex, href=True)['href'].split('/')[4]

        away_team_rows = master_df.loc[(master_df['gameID'] == game_id) & (master_df['defTeamName'] == away_team_name)]
        home_team_rows = master_df.loc[(master_df['gameID'] == game_id) & (master_df['defTeamName'] == home_team_name)]
        if not away_team_rows.empty:
            if away_starter_id != away_team_rows['starterID'].iloc[0]:
                master_df = master_df.drop(master_df[(master_df['gameID'] == game_id) & (master_df['defTeamName'] == away_team_name)].index)
                print(f'{away_team_name} Starting Pitcher Changed in Game {game_id}. Removing Corresponding Rows in Tables and Skipping.')
            else:
                pass

        if not home_team_rows.empty:
            if home_starter_id != home_team_rows['starterID'].iloc[0]:
                master_df = master_df.drop(master_df[(master_df['gameID'] == game_id) & (master_df['defTeamName'] == home_team_name)].index)
                print(f'{home_team_name} Starting Pitcher Changed in Game {game_id}. Removing Corresponding Rows in Tables and Skipping.')
            else:
                pass

        for hitter_div in hitter_divs:
            box = hitter_div.select_one('tbody')
            rows = box.find_all('tr')
            lineup = 1

            # Last row is empty
            for row in rows[:-1]:

                # Only include players who were in the starting lineup
                substitute_span = row.find('span', class_=substitute_regex)
                if not substitute_span:
                    player_anchor = row.find('a', class_=player_regex, href=True)
                    hitter_id = player_anchor['href'].split('/')[4]
                    cols = row.select('td')
                    hits_in_game = int(cols[2].find('span').text)
                    master_df.loc[(master_df['hitterID'] == hitter_id) & (master_df['gameID'] == game_id), 'lineup'] = lineup
                    master_df.loc[(master_df['hitterID'] == hitter_id) & (master_df['gameID'] == game_id), 'hitsInGame'] = hits_in_game
                    lineup += 1
    before_rows = master_df.shape[0]
    master_df = master_df.dropna()
    after_rows = master_df.shape[0]
    print(f'Removed {before_rows - after_rows} rows with missing data.')
    if not os.path.exists(os.path.join(master_path, 'withHits')):
        os.mkdir(os.path.join(master_path, 'withHits'))
    master_df.to_csv(os.path.join(master_path, 'withHits', f'masterHits{date}.csv'), index=False)
    print(f'Output new masterHits csv for {date} with lineup spots and hits in game to {os.path.join(master_path), "withHits", f"masterHits{date}.csv"}.')
    return
