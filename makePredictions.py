import datetime
import os
from datetime import date
import time
from datetime import timedelta
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import re
from bs4 import BeautifulSoup
import pickle
import fnmatch

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier

from getstatfunctions import get_hitter_dict, get_team_stats_dict, get_starter_dict, getMasterCSV, getHits, picklesToCSV, loadPickles, loadCSVs
now = datetime.datetime.now()
timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
today = date.today()
yesterday = today - timedelta(days=1)
yesterday_eve = today - timedelta(days=2)
tomorrow = today + timedelta(days=1)
cwd = os.getcwd()


master_path = os.path.join(cwd, 'master', 'withHits')


master_files = fnmatch.filter(os.listdir(master_path), '*[0-9]-[0-9][0-9]-[0-9][0-9].csv')
master_files = [os.path.join(master_path, file) for file in master_files]


master_df = pd.concat(map(pd.read_csv, master_files))
master_df = master_df.reset_index(drop=True)

master_df['H/PA'] = master_df['hits']/master_df['pas']
master_df['BB/PA'] = master_df['walks']/master_df['pas']
master_df['SO/PA'] = master_df['strikeouts']/master_df['pas']
master_df['starterl3hitsip'] = master_df['starterl3hits']/master_df['starterl3ip']

min_dict = {
    'H/PA': master_df['H/PA'].min(),
    'BB/PA': master_df['BB/PA'].min(),
    'SO/PA': master_df['SO/PA'].min(),
    'babip': master_df['babip'].min(),
    'avgl7': master_df['avgl7'].min(),
    'matchupAvg': master_df['matchupAvg'].min(),
    'pas': master_df['pas'].min(),
    'lineup': master_df['lineup'].min(),
    'starterl3hitsip': master_df['starterl3hitsip'].min(),
    'starterBAA': master_df['starterBAA'].min(),
    'starterWHIP': master_df['starterWHIP'].min(),
    'bullpenBAA': master_df['bullpenBAA'].min(),
    'bullpenWHIP': master_df['bullpenWHIP'].min(),
    'defRunsSaved': master_df['defRunsSaved'].min()
}

max_dict = {
    'H/PA': master_df['H/PA'].max(),
    'BB/PA': master_df['BB/PA'].max(),
    'SO/PA': master_df['SO/PA'].max(),
    'babip': master_df['babip'].max(),
    'avgl7': master_df['avgl7'].max(),
    'matchupAvg': master_df['matchupAvg'].max(),
    'pas': master_df['pas'].max(),
    'lineup': master_df['lineup'].max(),
    'starterl3hitsip': master_df['starterl3hitsip'].max(),
    'starterBAA': master_df['starterBAA'].max(),
    'starterWHIP': master_df['starterWHIP'].max(),
    'bullpenBAA': master_df['bullpenBAA'].max(),
    'bullpenWHIP': master_df['bullpenWHIP'].max(),
    'defRunsSaved': master_df['defRunsSaved'].max()
}













file_path = os.path.join(cwd, 'master', 'drafts', f'master{today}.csv')
today_df = pd.read_csv(file_path)
print(today_df)

today_df['lineup'] = np.nan

s = Service('C:/Users/conor/chromedriver.exe')
browser = webdriver.Chrome(service=s)
griditem_regex = re.compile('.*GridItemWrapper.*')
playermatchup_regex = re.compile('.*PlayerMatchupLayer.*')
teamwrapper_regex = re.compile('.*teamstyle__OuterWrapper.*')
game_ids = today_df['gameID'].unique()

for game_id in game_ids:
    game_url = f'https://www.mlb.com/gameday/{game_id}'

    browser.get(game_url)
    time.sleep(5)
    updated_url = browser.current_url
    teams = updated_url.split('/')[4].split('-vs-')
    away_team = teams[0]
    home_team = teams[1]
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    pregame_matchup = soup.find('section', class_='pregamematchup')
    if pregame_matchup:
        data_view_type = pregame_matchup['data-view-type']
        if data_view_type == '0':
            lineups = pregame_matchup.find('section').select('section')
            away_lineup = lineups[0].select('ul')
            home_lineup = lineups[1].select('ul')
            for batter in away_lineup[1:]:
                batter_anchor = batter.find('li').find('a')
                order = batter_anchor.find('span', class_='batting-order')
                if order:
                    hitter_id = int(batter_anchor['href'].split('/')[4])
                    spot = order.text
                    today_df.loc[(today_df['hitterID'] == hitter_id) & (today_df['gameID'] == game_id), 'lineup'] = spot
                else:
                    print(f'{away_team} lineup not announced yet in game {game_id}. Skipping.')
                    break
            for batter in home_lineup[1:]:
                batter_anchor = batter.find('li').find('a')
                order = batter_anchor.find('span', class_='batting-order')
                if order:
                    hitter_id = int(batter_anchor['href'].split('/')[4])
                    spot = order.text
                    today_df.loc[(today_df['hitterID'] == hitter_id) & (today_df['gameID'] == game_id), 'lineup'] = spot
                else:
                    print(f'{home_team} lineup not announced yet in game {game_id}. Skipping.')
                    break
        else:
            print(f'Lineups not announced yet for game {game_id}, {away_team} vs. {home_team}. Skipping.')
    else:
        print(f'Game {game_id}, {away_team} vs. {home_team} already started. Skipping.')
predictable_df = today_df.dropna()
predictable_df['H/PA'] = predictable_df['hits']/predictable_df['pas']
predictable_df['BB/PA'] = predictable_df['walks']/predictable_df['pas']
predictable_df['SO/PA'] = predictable_df['strikeouts']/predictable_df['pas']
predictable_df['starterl3hitsip'] = predictable_df['starterl3hits']/predictable_df['starterl3ip']
print(predictable_df)

def probToAmerican(odds):
    decimal = 1 / odds
    if decimal >= 2:
        return round((decimal - 1) * 100)
    else:
        return round(-100 / (decimal - 1))

with open('test_model.pickle', 'rb') as handle:
    model = pickle.load(handle)

predictions = model.predict_proba(predictable_df.filter(['H/PA', 'BB/PA', 'SO/PA', 'babip', 'avgl7', 'matchupAvg', 'pas', 'lineup', 'starterl3hitsip', 'starterBAA', 'starterWHIP', 'bullpenBAA', 'bullpenWHIP', 'defRunsSaved']))[:, 1]
prediction_df = predictable_df.filter(['hitterName', 'hitTeamName'])
prediction_df['prediction'] = predictions
prediction_df['prediction'] = prediction_df['prediction'].map(probToAmerican)
prediction_df.to_csv(f'predictions{timestamp}.csv')

browser.close()