from django.shortcuts import render
import mlbstatsapi
import asyncio
import json

from . import statizdetail
from . import predict
from django.http import HttpResponse
from django.core import serializers

# Create your views here.
def getDataAsync(request):
    requestData = request.POST
    type = requestData['type']

    if(type == 'players'):
        if 'teamId' in requestData:
            result = statizdetail.getPlayers(requestData['teamId'])
        else:
            result = statizdetail.getPlayers()
    elif(type == 'player'):
        result = statizdetail.getPlayer(requestData['id'])
    elif(type == 'schedule'):
        result = statizdetail.getSchedule(requestData['date'])
    elif(type == 'teams'):
        result = statizdetail.getTeams()
    elif(type == 'predict'):
        result = predict.predict_date(requestData['date'])
    elif(type == 'train'):
        result = {}
        predict.train()

    return HttpResponse(result)
    # return players

def home(request):
    return render(request, 'statiz/home.html')

def teams(request):
    return render(request, 'statiz/teams.html')

def players(request):
    return render(request, 'statiz/players.html')