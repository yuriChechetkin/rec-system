from django.shortcuts import render
from django.contrib.auth.models import User, Group
from diploma.recsystems.models import  recommendations
from rest_framework import viewsets
from diploma.recsystems.serializers import UserSerializer, GroupSerializer, RecSerializer, recommendationsSerializer
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django_pandas.io import read_frame
from rest_pandas import PandasView
import sys, os, csv, re
import pandas as pd
import math


"""
1)  описание, 5 страниц минимум, как получится
2)  структура врб, mindmap
3)  github
4)  ~
"""


#http://localhost:8000/api/3/score/
#http://localhost:8000/api/4/colloborative/
#http://localhost:8000/api/3q4/score/

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class RecViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """
    queryset = recommendations.objects.all()
    serializer_class = RecSerializer


    @list_route(methods=['post'])
    def rec(self, request):
        #data = csv.reader('A1Ratings.csv')
        #file = open('A1Ratings.csv', 'r')
        #data = [row for row in csv.reader(file)]
        row = self.request.data.get("row")
        cell = self.request.data.get("cell")
        df = pd.read_csv('A1Ratings.csv')
        if row:
            if cell:
                return  Response({df.columns[int(row)]+ " at " + str(cell) + " score": df[df.columns[int(row)]][int(cell)]})
            else:
                return  Response({df.columns[int(row)]: df[df.columns[int(row)]]})
        else:
            return Response({"Error: look at the full table": df})


    @list_route(methods=['post'])
    def test(self, request):
        #rec = makeRecommendation ('ivan', ReadFile(), 5, 5)
        """
        http://habrahabr.ru/post/150399/
        привести A1Ratings.csv к виду словарю
        аналогия с файлом Ratings.csv
        df = pd.read_csv('A1Ratings.csv')
        if row:
            if cell:
                return  Response({df.columns[int(row)]+ " at " + str(cell) + " score": df[df.columns[int(row)]][int(cell)]})
            else:
                return  Response({df.columns[int(row)]: df[df.columns[int(row)]]})
        """
        user = self.request.data.get("row")
        df = pd.read_csv('A1Ratings.csv')
        id =  str(df[df.columns[int(0)]][int(user)])
        rec = makeRecommendation(id, File(), 5, 5)
        result = "succes: our reccomendations for user: " + id
        return Response({result: rec})






    @list_route()
    def lists(self, request):
        txt=""
        txt2=""
        f = open('rating.txt', 'r')
        for line in f:
           line =  line.split(',')
           if(txt2==""):
               txt2=line
           txt= txt + '  ' + line[0]# + ' ' + line[1]
           for score in line:
                txt2 = txt2 #+ score

        f.close()
        return Response({"list of Users id": txt, "list of films":txt2})

    @detail_route()
    def score(self, request, pk=None):
        txt=""
        result=0
        count=0
        f = open('rating.txt', 'r')
        if(pk.__len__()>2):
            for line in f:
               line =  line.split(',')
               txt = txt + '  ' + line[int(pk[0])]# + ' ' + line[1]

            f.close()
            return Response({"cell/row": txt[int(pk[2])]})
        else:
            for line in f:
               line =  line.split(',')
               txt = txt + '  ' + line[int(pk[0])]# + ' ' + line[1]
               if line[int(pk[0])].isdigit():
                   result = result + int(line[int(pk[0])])
                   count = count + 1
            result = result / count
            f.close()
            return Response({"countOfScores": str(count), "avgScore": str(result),"row": txt})


    @detail_route(methods=['post'])
    def colloborative(self, request, pk=None):
        row = self.request.data.get("row")
        cell = self.request.data.get("cell")
        txt=""
        result=0
        count=0
        f = open('rating.txt', 'r')
        for line in f:
            line =  line.split(',')
            txt = txt + '  ' + line[int(row)]# + ' ' + line[1]
            if line[int(row)].isdigit():
                result = result + int(line[int(row)])
                count = count + 1
        result = result / count
        f.close()
        return Response({"countOfScores": str(count), "avgScore": str(result),"id": pk, "row": row, "cell": cell, "row/cell":txt[int(cell)]})


def ReadFile (filename = "Ratings.csv"):
        f = open(filename)
        r = csv.reader(f)
        mentions = dict()
        for line in r:
            user    = line[0]
            product = line[1]
            rate    = float(line[2])
            if not user in mentions:
                mentions[user] = dict()
            mentions[user][product] = rate
        f.close()
        return mentions


def File(filename = "A1Ratings.csv"):
        i = 0;
        filename = "A1Ratings.csv"
        f = open(filename)
        r = csv.reader(f)
        df = pd.read_csv('A1Ratings.csv')
        mentions = dict()
        for line in r:
            if line[0]!='User':
                for column in df.columns:
                    if column != 'User':
                        user    = line[0]
                        product =  column
                        rate    = float(df[column][i])
                        if not user in mentions:
                            mentions[user] = dict()
                        if df[column][i]>-1:
                            mentions[user][product] = rate
            else:
                i=i-1
            i=i+1
        f.close()
        return mentions


def distCosine (vecA, vecB):
    def dotProduct (vecA, vecB):
            d = 0.0
            for dim in vecA:
                if dim in vecB:
                    d += vecA[dim]*vecB[dim]
            return d
    return dotProduct (vecA,vecB) / math.sqrt(dotProduct(vecA,vecA)) / math.sqrt(dotProduct(vecB,vecB))

def makeRecommendation (userID, userRates, nBestUsers, nBestProducts):
    matches = [(u, distCosine(userRates[userID], userRates[u])) for u in userRates if u != userID]
    bestMatches = sorted(matches, key=lambda xy:(xy[1],xy[0]), reverse=True)[:nBestUsers]
    #print "Most correlated with '%s' users:" % userID
    #for line in bestMatches:
        #print "  UserID: %6s  Coeff: %6.4f" % (line[0], line[1])
    sim = dict()
    sim_all = sum([x[1] for x in bestMatches])
    bestMatches = dict([x for x in bestMatches if x[1] > 0.0])
    for relatedUser in bestMatches:
        for product in userRates[relatedUser]:
            if not product in userRates[userID]:
                if not product in sim:
                    sim[product] = 0.0
                sim[product] += userRates[relatedUser][product] * bestMatches[relatedUser]
    for product in sim:
        sim[product] /= sim_all
    bestProducts = sorted(sim.items(), key=lambda xy:(xy[1],xy[0]), reverse=True)[:nBestProducts]
    #print "Most correlated products:"
    #for prodInfo in bestProducts:
        #print "  ProductID: %6s  CorrelationCoeff: %6.4f" % (prodInfo[0], prodInfo[1])
    return [(x[0], x[1]) for x in bestProducts]

