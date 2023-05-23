import pybaseball
import requests
import json
import time
from pybaseball import lahman
from pybaseball import schedule_and_record
from pybaseball import statcast, playerid_lookup, statcast_pitcher
from pybaseball import pitching_stats
from pybaseball import cache
from datetime import datetime
from bs4 import BeautifulSoup
import mlbstatsapi

# cache.enable()
def getPlayer(id):
    mlb = mlbstatsapi.Mlb()

    stats = ['career']
    groups = ['hitting', 'pitching']

    status = {}
    player_status = mlb.get_player_stats(id, stats, groups)

    if 'hitting' in player_status:
        status['hitting'] = player_status['hitting']['career'].splits[0].stat.__dict__
        
        if 'winloss' in player_status['hitting']:
            print(player_status['hitting']['winloss'].__dict__)
    if 'pitching' in player_status:
        status['hitting'] = player_status['pitching']['career'].splits[0].stat.__dict__

    return json.dumps(status)

def getPlayers(teamId=None):
    start = time.time()
    if teamId is not None:
        response = requests.get("https://statsapi.mlb.com/api/v1/teams/" + teamId + "/roster/fullName")

        players = response.text
        return players
    else:
        mlb = mlbstatsapi.Mlb()
        people = mlb.get_people()
        teams = mlb.get_teams()
        players = []

        mlbteams = {}
        for team in teams:
            mlbteams['{}'.format(team.id)] = team

        limit = 10
        i = -1
        while i < limit:
            i = i + 1
            person = people[i]

            player = {
                'id': person.id,
                'fullname': person.fullname,
                'age': person.currentage,
                'team': mlbteams['{}'.format(person.currentteam['id'])].name,
                'position': person.primaryposition.name
            }

            stats = ['career']
            groups = ['hitting', 'pitching']
            params = {'season': 2022}
            player_status = mlb.get_player_stats(person.id, stats, groups, **params)

            hitting_stat = {}
            pitching_stat = {}

            if 'hitting' in player_status:
                hitting_stat = player_status['hitting']['career'].splits[0].stat.__dict__
            if 'pitching' in player_status:
                pitching_stat = player_status['pitching']['career'].splits[0].stat.__dict__

            player['hittingstat'] = hitting_stat
            player['pitchingstat'] = pitching_stat

            # players.append(player[0]['splits'][0])
            players.append(player)

    print('execusion time: {}'.format(time.time() - start))
    # return json.dumps(players)

def getTeams():
    response = requests.get("http://statsapi.mlb.com/api/v1/teams?sportId=1")

    # Parse the JSON response
    teams = response.text

    return teams

def getSchedule(date):
    # today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get("https://statsapi.mlb.com/api/v1/schedule?gameType=R&sportId=1&date=" + date)

    # Parse the JSON response
    schedule = response.text

    return schedule