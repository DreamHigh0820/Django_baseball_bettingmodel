import pandas as pd
import numpy as np
import requests
import datetime
import mlbstatsapi
import json

from keras.models import Sequential
from keras.layers import Dense, LSTM
from .models import Venue, Settings
from .utils import parseFloat, parseInt

def train():
	mlb = mlbstatsapi.Mlb()
	setting = Settings.objects.first()

	print(setting.last_train_date)

	if setting:
		True
	else:
		print('Initialize setting')
		Settings.objects.create(
			last_train_date = datetime.datetime.strptime("2023-01-01", "%Y-%m-%d")
		).save()
		setting = Settings.objects.first()
	
	startDate = (setting.last_train_date + datetime.timedelta(days=1)).isoformat()[0:10]
	endDate = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()[0:10]

	print("Train Data")
	print("StartDate: ", startDate)

	if(startDate >= endDate):
		print("Already up to date.")
		return

	params = {"startDate": startDate, "endDate": endDate, "hydrate": "weather", "gameType": "R"}
	schedule = requests.get("http://statsapi.mlb.com/api/v1/schedule?sportId=1", params=params).json()

	# # create a sequential model
	model = Sequential()

	# add an LSTM layer with 32 memory units and input shape of (1, 17)
	model.add(LSTM(64, input_shape=(1, 19)))

	# add a dense output layer with linear activation and 2 units
	model.add(Dense(2, activation='linear'))

	# compile the model with mean squared error loss and adam optimizer
	model.compile(loss='mean_squared_error', optimizer='adam', metrics=['accuracy'])

	# train the model for 100 epochs using a batch size of 32
	# or load modal weights
	model.load_weights("model_weights.h5")

	if len(schedule['dates']) > 0:
		for date in schedule['dates']:
			factorsList = []
			scoresList = []

			if len(date['games']) > 0:
				for game in date['games']:
					boxscore = mlb.get_game_box_score(game['gamePk'])
					homeTeam = boxscore.teams.home
					awayTeam = boxscore.teams.away

					# Get venue
					venueName = boxscore.teams.home.team.venue.name

					# Get Latitude and Longitude of the venue
					venue = Venue.objects.filter(name=f'{venueName}').first()
					if venue:
						lat = venue.lat
						lon = venue.lon
					else:
						location = requests.get(f'https://nominatim.openstreetmap.org/search?q={venueName}&format=json&limit=1').json()[0]

						lat = location['lat']
						lon = location['lon']

						Venue.objects.create(
							name = venueName,
							lat = lat,
							lon = lon
						).save()

					weather = game['weather']

					homeHittingStats = homeTeam.teamstats['batting']
					homePitchingStats = homeTeam.teamstats['pitching']
					homeFieldingStats = homeTeam.teamstats['fielding']
					awayHittingStats = awayTeam.teamstats['batting']
					awayPitchingStats = awayTeam.teamstats['pitching']
					awayFieldingStats = awayTeam.teamstats['fielding']

					try:
						factors = [
							homeTeam.team.id,
							awayTeam.team.id,
							parseFloat(homeHittingStats['avg']),
							parseFloat(homeHittingStats['obp']),
							parseFloat(homeHittingStats['slg']),
							parseFloat(homePitchingStats['obp']),
							parseFloat(homePitchingStats['whip']),
							parseFloat(homePitchingStats['strikepercentage']),
							parseFloat(homePitchingStats['earnedruns']) / parseFloat(homePitchingStats['inningspitched']) if parseFloat(homePitchingStats['inningspitched']) != 0 else 0,
							parseFloat(homeFieldingStats['putouts']) / parseFloat(homeFieldingStats['chances']) if parseFloat(homeFieldingStats['chances']) != 0 else 0,
							parseFloat(awayHittingStats['avg']),
							parseFloat(awayHittingStats['obp']),
							parseFloat(awayHittingStats['slg']),
							parseFloat(awayPitchingStats['whip']),
							parseFloat(awayPitchingStats['stolenbasepercentage']),
							parseFloat(awayPitchingStats['earnedruns']) / parseFloat(awayPitchingStats['inningspitched']) if parseFloat(awayPitchingStats['inningspitched']) != 0 else 0,
							parseFloat(awayFieldingStats['putouts']) / parseFloat(awayFieldingStats['chances']) if parseFloat(awayFieldingStats['chances']) != 0 else 0,
							(parseFloat(weather['temp']) - 32) * 5 / 9,
							parseInt(weather['wind']),
						]
						
						homeScore = game['teams']['home']['score']
						awayScore = game['teams']['away']['score']

						factorsList.append(factors)
						scoresList.append([homeScore, awayScore])
					except Exception as e:
						print('An error occured from gameId: ', game['gamePk'], e)
					finally:
						True

			x_new = np.array(factorsList)
			x_new = x_new.reshape(x_new.shape[0], 1, x_new.shape[1])
			y_new = np.array(scoresList)

			model.fit(x_new, y_new)

			factorsList.clear()
			scoresList.clear()

			setting.last_train_date = datetime.datetime.strptime(date['date'], "%Y-%m-%d")
			setting.save()

			print("Train to : ", date['date'])
			model.save_weights('model_weights.h5')

def predict_date(curDate):
	# # create a sequential model
	model = Sequential()

	# add an LSTM layer with 32 memory units and input shape of (1, 17)
	model.add(LSTM(64, input_shape=(1, 19)))

	# add a dense output layer with linear activation and 2 units
	model.add(Dense(2, activation='linear'))

	# compile the model with mean squared error loss and adam optimizer
	model.compile(loss='mean_squared_error', optimizer='adam', metrics=['accuracy'])

	# train the model for 100 epochs using a batch size of 32
	# or load modal weights
	model.load_weights("model_weights.h5")

	# ----------- Get schedule ---------- #
	response = requests.get(f"https://statsapi.mlb.com/api/v1/schedule?gameType=R&sportId=1&date={curDate}&hydrate=weather")

	# Parse the JSON response
	schedule = response.json()

	mlb = mlbstatsapi.Mlb()

	result = []
	current_year = parseInt(curDate[:4])
	yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()[:10]
	
	if schedule['totalGames'] > 0:
		games = schedule['dates'][0]['games']

		# for j in range(5):
		# 	game = games[j]
		for game in games:
			homeId = game['teams']['home']['team']['id']
			awayId = game['teams']['away']['team']['id']

			# if game['status']['abstractGameState'] == 'Final':
			# 	result.append({'home': -1, 'away': -1})
			# 	continue

			homeTeamScheduleResponse = requests.get(f'https://statsapi.mlb.com/api/v1/schedule?teamId={homeId}&season={current_year}&sportId=1').json()['dates']
			awayTeamScheduleResponse = requests.get(f'https://statsapi.mlb.com/api/v1/schedule?teamId={awayId}&season={current_year}&sportId=1').json()['dates']

			homeTeamScheduleResponse.reverse()
			awayTeamScheduleResponse.reverse()

			homeTeamScheduleId = next(element for element in homeTeamScheduleResponse if element['date'] <= curDate and element['games'][0]['status']['codedGameState'] == 'F')['games'][0]['gamePk']
			awayTeamScheduleId = next(element for element in awayTeamScheduleResponse if element['date'] <= curDate and element['games'][0]['status']['codedGameState'] == 'F')['games'][0]['gamePk']

			print(homeTeamScheduleId)

			homeTeam = mlb.get_game_box_score(homeTeamScheduleId).teams.home
			awayTeam = mlb.get_game_box_score(awayTeamScheduleId).teams.away

			# homeTeamSeason = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{homeId}/stats?stats=season&group=hitting,pitching,fielding').json()
			# awayTeamSeason = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{awayId}/stats?stats=season&group=hitting,pitching,fielding').json()

			# Get venue
			venueName = game['venue']['name']

			# Get Latitude and Longitude of the venue
			venue = Venue.objects.filter(name=f'{venueName}').first()
			if venue:
				lat = venue.lat
				lon = venue.lon
			else:
				location = requests.get(f'https://nominatim.openstreetmap.org/search?q={venueName}&format=json&limit=1').json()[0]

				lat = location['lat']
				lon = location['lon']

				Venue.objects.create(
					name = venueName,
					lat = lat,
					lon = lon
				).save()

			# Get weather data
			url = "https://weatherapi-com.p.rapidapi.com/forecast.json"

			querystring = {"q":f"{lat},{lon}","days":"3","dt":f"{curDate}"}

			headers = {
				"X-RapidAPI-Key": "243fc92eebmsh454b88e22f9f25ap1646a9jsnb09cf8afda22",
				"X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
			}

			response = requests.get(url, headers=headers, params=querystring).json()

			hour = datetime.datetime.strptime(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ").hour

			if game['gameDate'] > yesterday:
				weather = response['forecast']['forecastday'][0]['hour'][hour]
			else:
				weather = game['weather']

			# homeHittingStatsSeason = homeTeamSeason['stats'][0]['splits'][0]['stat']
			# homePitchingStatsSeason = homeTeamSeason['stats'][1]['splits'][0]['stat']
			# homeFieldingStatsSeason = homeTeamSeason['stats'][2]['splits'][0]['stat']
			# awayHittingStatsSeason = awayTeamSeason['stats'][0]['splits'][0]['stat']
			# awayPitchingStatsSeason = awayTeamSeason['stats'][1]['splits'][0]['stat']
			# awayFieldingStatsSeason = awayTeamSeason['stats'][2]['splits'][0]['stat']

			homeHittingStats = homeTeam.teamstats['batting']
			homePitchingStats = homeTeam.teamstats['pitching']
			homeFieldingStats = homeTeam.teamstats['fielding']
			awayHittingStats = awayTeam.teamstats['batting']
			awayPitchingStats = awayTeam.teamstats['pitching']
			awayFieldingStats = awayTeam.teamstats['fielding']

			# factorsSeason = [
			# 	homeTeam.team.id,
			# 	awayTeam.team.id,
			# 	parseFloat(homeHittingStatsSeason['avg']),
			# 	parseFloat(homeHittingStatsSeason['obp']),
			# 	parseFloat(homeHittingStatsSeason['slg']),
			# 	parseFloat(homePitchingStatsSeason['obp']),
			# 	parseFloat(homePitchingStatsSeason['whip']),
			# 	parseFloat(homePitchingStatsSeason['strikePercentage']),
			# 	parseFloat(homePitchingStatsSeason['earnedRuns']) / parseFloat(homePitchingStatsSeason['inningsPitched']) if parseFloat(homePitchingStatsSeason['inningsPitched']) != 0 else 0,
			# 	parseFloat(homeFieldingStatsSeason['putOuts']) / parseFloat(homeFieldingStatsSeason['chances']) if parseFloat(homeFieldingStatsSeason['chances']) != 0 else 0,
			# 	parseFloat(awayHittingStatsSeason['avg']),
			# 	parseFloat(awayHittingStatsSeason['obp']),
			# 	parseFloat(awayHittingStatsSeason['slg']),
			# 	parseFloat(awayPitchingStatsSeason['whip']),
			# 	parseFloat(awayPitchingStatsSeason['stolenBasePercentage']),
			# 	parseFloat(awayPitchingStatsSeason['earnedRuns']) / parseFloat(awayPitchingStatsSeason['inningsPitched']) if parseFloat(awayPitchingStatsSeason['inningsPitched']) != 0 else 0,
			# 	parseFloat(awayFieldingStatsSeason['putOuts']) / parseFloat(awayFieldingStatsSeason['chances']) if parseFloat(awayFieldingStatsSeason['chances']) != 0 else 0,
			# 	parseFloat(weather['temp_c']),
			# 	parseInt(weather['wind_mph']),
			# ]

			# factors = [
			# 	homeTeam.team.id,
			# 	awayTeam.team.id,
			# 	(factorsSeason[2] + parseFloat(homeHittingStats['avg'])) / 2,
			# 	(factorsSeason[3] + parseFloat(homeHittingStats['obp'])) / 2,
			# 	(factorsSeason[4] + parseFloat(homeHittingStats['slg'])) / 2,
			# 	(factorsSeason[5] + parseFloat(homePitchingStats['obp'])) / 2,
			# 	(factorsSeason[6] + parseFloat(homePitchingStats['whip'])) / 2,
			# 	(factorsSeason[7] + parseFloat(homePitchingStats['strikepercentage'])) / 2,
			# 	(factorsSeason[8] + (parseFloat(homePitchingStats['earnedruns']) / parseFloat(homePitchingStats['inningspitched']) if parseFloat(homePitchingStats['inningspitched']) != 0 else 0)) / 2,
			# 	(factorsSeason[9] + (parseFloat(homeFieldingStats['putouts']) / parseFloat(homeFieldingStats['chances']) if parseFloat(homeFieldingStats['chances']) != 0 else 0)) / 2,
			# 	(factorsSeason[10] + parseFloat(awayHittingStats['avg'])) / 2,
			# 	(factorsSeason[11] + parseFloat(awayHittingStats['obp'])) / 2,
			# 	(factorsSeason[12] + parseFloat(awayHittingStats['slg'])) / 2,
			# 	(factorsSeason[13] + parseFloat(awayPitchingStats['whip'])) / 2,
			# 	(factorsSeason[14] + parseFloat(awayPitchingStats['stolenbasepercentage'])) / 2,
			# 	(factorsSeason[15] + (parseFloat(awayPitchingStats['earnedruns']) / parseFloat(awayPitchingStats['inningspitched']) if parseFloat(awayPitchingStats['inningspitched']) != 0 else 0)) / 2,
			# 	(factorsSeason[16] + (parseFloat(awayFieldingStats['putouts']) / parseFloat(awayFieldingStats['chances']) if parseFloat(awayFieldingStats['chances']) != 0 else 0)) / 2,
			# 	parseFloat(weather['temp_c']),
			# 	parseInt(weather['wind_mph']),
			# ]

			try:
				temperature = parseFloat(weather['temp_c']) if 'temp_c' in weather else parseFloat(weather['temp'])
				windspeed = parseInt(weather['wind_mph']) if 'wind_mph' in weather else parseInt(weather['wind'])
			except Exception:
				result.append({'home': -1, 'away': -1})
				continue
			finally:
				True

			factors = [
				homeTeam.team.id,
				awayTeam.team.id,
				parseFloat(homeHittingStats['avg']),
				parseFloat(homeHittingStats['obp']),
				parseFloat(homeHittingStats['slg']),
				parseFloat(homePitchingStats['obp']),
				parseFloat(homePitchingStats['whip']),
				parseFloat(homePitchingStats['strikepercentage']),
				parseFloat(homePitchingStats['earnedruns']) / parseFloat(homePitchingStats['inningspitched']) if parseFloat(homePitchingStats['inningspitched']) != 0 else 0,
				parseFloat(homeFieldingStats['putouts']) / parseFloat(homeFieldingStats['chances']) if parseFloat(homeFieldingStats['chances']) != 0 else 0,
				parseFloat(awayHittingStats['avg']),
				parseFloat(awayHittingStats['obp']),
				parseFloat(awayHittingStats['slg']),
				parseFloat(awayPitchingStats['whip']),
				parseFloat(awayPitchingStats['stolenbasepercentage']),
				parseFloat(awayPitchingStats['earnedruns']) / parseFloat(awayPitchingStats['inningspitched']) if parseFloat(awayPitchingStats['inningspitched']) != 0 else 0,
				parseFloat(awayFieldingStats['putouts']) / parseFloat(awayFieldingStats['chances']) if parseFloat(awayFieldingStats['chances']) != 0 else 0,
				temperature,
				windspeed,
			]

			# define the input data
			input_data = np.array([factors])

			input_data_reshaped = input_data.reshape((input_data.shape[0], 1, input_data.shape[1]))

			# print(model.get_weights())

			# model.save_weights('model_weights.h5')
			score = model.predict(input_data_reshaped)

			homeScore = round(score[0][0])
			awayScore = round(score[0][1])

			if homeScore < 0:
				homeScore = 0
			if awayScore < 0:
				awayScore = 0

			if homeScore == awayScore:
				if score[0][0] > score[0][1]:
					homeScore = homeScore + 1
				else:
					awayScore = awayScore + 1
			
			result.append({'home': homeScore, 'away': int(awayScore)})

	return json.dumps(result)
