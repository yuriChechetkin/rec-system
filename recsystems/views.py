from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from diploma.recsystems.serializers import UserSerializer, GroupSerializer, RecSerializer, recommendationsSerializer
from diploma.recsystems.models import  recommendations
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
import json
import urllib
from pandas import sparse, io
import numpy as np


"""
шаги по запуску из консоли:
1) перейти в директорию diploma
2) virtualenv ENVdiploma
3) ENVdiploma\Scripts\activate
4) python manage.py runserver
"""


#http://localhost:8000/api/3/score/
#http://localhost:8000/api/4/colloborative/
#http://localhost:8000/api/3q4/score/

items = pd.read_csv('content-items2.csv', index_col=0)
users = pd.read_csv('content-users2.csv', index_col=0)

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


#############################################################CONTETN-BASED###################################################################################
class ContentBasedViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """
    queryset = recommendations.objects.all()
    serializer_class = RecSerializer


    """показать все items
    input - none
    output - items

    """
    @list_route(methods=['post'])
    def showitems(self, request):
        try:
            return Response({"result": items})
        except:
            return Response("Error")

    """показать всех users
    input - none
    output - users

    """
    @list_route(methods=['post'])
    def showusers(self, request):
        try:
            return Response({"result": users})
        except:
            return Response({"Error"})

    """добавить item
    input - id из API kudago.com
    output - successfulness

    """
    #http://kudago.com/public-api/v1/events/?fields=id,dates,title,tags&order_by=-publication_date&page_size=100
    @list_route(methods=['post'])
    def additem(self, request):
        try:
            id = self.request.data.get("row")
            addItem(int(id))
            return Response({"result": "success"})
        except:
            return Response({"Error"})

    """добавить user
    input - имя/идентификатор пользователя
    output - successfulness

    """
    @list_route(methods=['post'])
    def adduser(self, request):
        try:
            name = self.request.data.get("row")
            addUser(name)
            return Response({"result": "success"})
        except:
            return Response({"Error"})

    """добавить оценку
    input - id объетк из API kudago.com, оценка, имя/идентификатор пользователя
    output - successfulness, список пользователей

    """
    @list_route(methods=['post'])
    def addUserScore(self, request):
        try:
            name = self.request.data.get("row")
            id = self.request.data.get("cell")
            score = int(self.request.data.get("score"))
            if(score==1 or score==-1 or score==0):
                users=addUserScore(id, score, name)
                return Response({"result": users})
            else:
                return Response({"Error": "score must be 1, 0 or -1"})
        except:
            return Response({"Error"})


    """получить рекомендации content-based
    input - имя/идентификатор пользователя, количество оценок
    output - content-based рекомендации

    """
    @list_route(methods=['post'])
    def recommendations(self, request):
        try:
            user = self.request.data.get("row")
            n = self.request.data.get("cell")
            recommendations = getRec(int(user), int(n))
            result = "succes: our reccomendations for user: " + users.columns[int(user)]
            return Response({result: recommendations})
        except:
            return Response({"Error"})


#############################################################CRUD-CONTENT-BASED###################################################################################
"""добавить оценку
    input - id объетк из API kudago.com, оценка, имя/идентификатор пользователя
    output - список пользователей

"""
def addUserScore(Id, score, name):
    url = 'http://kudago.com/public-api/v1/events/' + str(Id) +  '/?fields=id,title,categories,tags&order_by=-publication_date'
    r = urllib.request.urlopen(url)
    event = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    title = event['title']
    item = str(Id) + " : " + title
    if(str(users).find(str(Id))!=-1):
        users[name][item]=score
    else:
        addItem(Id)
        addUserScore(Id, score, name)
    users.to_csv('content-users2.csv', sep=',', encoding='utf-8')
    return users


"""добавить item
    input - id из API kudago.com
    output - none

"""
def addItem(Id):
    #pass
    countItems = items.columns.size
    countUsers = users.columns.size

    url = 'http://kudago.com/public-api/v1/events/' + str(Id) +  '/?fields=id,title,categories,tags&order_by=-publication_date'
    r = urllib.request.urlopen(url)
    event = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    attributes = event['tags']
    title = event['title']
    name = str(Id) + " : " + title

    attributes.sort()

    if(str(items).find(str(Id))==-1 ):
        #если запись новая
        #print('noncon')
        for i in range(0, len(attributes)):
            if(str(items.columns).find(attributes[i])==-1):
                addAttribute(attributes[i])
        countItems = items.columns.size
        item = np.zeros(countItems)
        for j in range(0, len(attributes)):
            if(str(items.columns).find(attributes[j])!=-1):
                item[index(attributes[j])]=1 #получить номер колонки по названию
        newpd = pd.DataFrame(item)
        items.loc[name]=item
        items['Total attributes'][name] = newpd[newpd>0].count()
        user = np.zeros(countUsers)
        users.loc[name]=user
    else:
        #print('con')
        for i in range(0, len(attributes)):
            if(str(items.columns).find(attributes[i])==-1):
                addAttribute(attributes[i])
        item = items.loc[name]
        for j in range(0, len(attributes)):
            if(str(items.columns).find(attributes[j])!=-1):
                item[index(attributes[j])]=1 #получить номер колонки по названию
        newpd = pd.DataFrame(item[1:])
        items.loc[name]=item
        items['Total attributes'][name] = newpd[newpd>0].count()
        user = np.zeros(countUsers)
        users.loc[name]=user
    users.to_csv('content-users2.csv', sep=',', encoding='utf-8')
    items.to_csv('content-items2.csv', sep=',', encoding='utf-8')




def index(attr):
    for i in range(0, items.columns.size):
        if(attr==items.columns[i]):
            return i

"""добавить user
    input - имя/идентификатор пользователя
    output - none

"""
def addUser(name):
    #pass
    userEmptyScores = np.zeros(users.size/users.columns.size)
    users[name]=userEmptyScores
    users.to_csv('content-users2.csv', sep=',', encoding='utf-8')

"""добавить атрибут
    input - имя/идентификатор атрибута
    output - none

"""
def addAttribute(name):
    #pass
    attributeEmptyVector = np.zeros(items.size/items.columns.size)
    items[name]=attributeEmptyVector
    items.to_csv('content-items2.csv', sep=',', encoding='utf-8')


################################################################CONTEN-BASED-ALORITHMS#######################################################################


"""получить рекомендации content-based
    input - имя/идентификатор пользователя, количество оценок
    output - content-based рекомендации

"""
def getRec(num, nBestProducts):

    """
    calcucalate support data
    n-count of attributes without Totat Attributes
    m-count of articles
    u-count of uesrs
    """
    _items=items;
    _users=users;

    n = _items.columns.size
    m = int(_items.size/_items.columns.size)
    u = _users.columns.size

    for j in range(0, m):
        for i in range(1, n):
            if(_items[_items.columns[i]][j]>0):
                _items[_items.columns[i]][j] = 1/math.sqrt(_items['Total attributes'][j])

    article = np.zeros((m,n-1))
    for j in range(0, m):
        for i in range(1, n):
            article[j][i-1] = _items[_items.columns[i]][j]


    user1 = np.zeros(n-1)
    usersVec = np.zeros((u, n-1))
    DF = np.zeros(n-1)
    IDF = np.zeros(n-1)
    for k in range(0, u):
        for i in range(1,n):
            s = _items.columns[i]
            DF[i-1] = _items[s][_items[s]>0].count()
            IDF[i-1] = np.log10(10/DF[i-1])
            for j in range(0, m):
                usersVec[k][i-1] += _items[_items.columns[i]][j]*_users[_users.columns[k]][j]

    result = np.zeros((m,u))
    user1 = np.zeros(m)
    one = dict()
    for i in range(0,u):
        for j in range(0, m):
            result[j][i] = dotProduct3(article[j], usersVec[i], IDF, n)
            user1[j] = dotProduct3(article[j], usersVec[num], IDF, n)
            #one[j] = [user1[j], items.iloc[[j]].index.tolist()[0]]
            one[items.iloc[[j]].index.tolist()[0]] = user1[j]
            #res = [items.iloc[[j]].index.tolist()[0], user1[j]]

    bestProducts = sorted(one.items(), key=lambda xy:(xy[1],xy[0]), reverse=True)[:nBestProducts]
    res = [(x[0], x[1]) for x in bestProducts]

    return res;


"""скалярное произведение
    input - 3 вектора
    output - результат скалярного произведения

"""
def dotProduct3 (vecA, vecB, vecC, n):
            d = 0.0
            for i in range(1, n-1):
                d += vecA[i-1]*vecB[i-1]*vecC[i-1]
            return d




#################################################################COLLOBORATIVE######################################################################

class CollaborativeViewSet(viewsets.ModelViewSet):
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


    @list_route(methods=['post'])
    def recommendations(self, request):
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
        try:
            user = self.request.data.get("row")
            df = pd.read_csv('A1Ratings.csv')
            id =  str(df[df.columns[int(0)]][int(user)])
            n = self.request.data.get("cell")
            rec = makeRecommendation(id, File(), 5, int(n))
            result = "succes: our reccomendations for user: " + id
            return Response({result: rec})
        except:
            return Response({"Error"})

    """добавить item
    input - имя/идентификатор item
    output - successfulness

    """
    @list_route(methods=['post'])
    def additem(self, request):
        try:
            name = self.request.data.get("row")
            addItem2(name)
            return Response({"result": "success"})
        except:
            return Response({"Error"})

    """добавить user
    input - имя/идентификатор пользователя
    output - successfulness

    """
    @list_route(methods=['post'])
    def adduser(self, request):
        try:
            userid = self.request.data.get("row")
            addUser2(int(userid))
            return Response({"result": "success"})
        except:
            return Response({"Error"})

    """добавить оценку
    input - имя/идентификатор item, имя/идентификатор пользователя, оценка
    output - successfulness, список пользователей

    """
    @list_route(methods=['post'])
    def addUserScore(self, request):
        try:
            usernumber = self.request.data.get("row")
            itemnumber = self.request.data.get("cell")
            score = int(self.request.data.get("score"))
            if(score>0 and score<6):
                users=addUserScore2(int(usernumber), int(itemnumber), score)
                return Response({"result": "success"})
            else:
                return Response({"Error": "score must be from 1 to 5"})
        except:
            return Response({"Error"})


#################################################################COLLABORATIVE-CRUD#####################################################################

def addUser2(userId):
    #pass
    df = pd.read_csv('A1Ratings.csv')
    countUsers = df.columns.size
    countItems = df.size/df.columns.size
    user = np.zeros(countUsers)
    for j in range(0, len(user)):
        user[j]=np.nan
    user[0]=userId
    df.loc[countItems] = user
    df.to_csv('A1Ratings.csv', sep=',', encoding='utf-8', index=False)

def addItem2(name):
    #pass
    df = pd.read_csv('A1Ratings.csv')
    newItem = np.zeros(df.size/df.columns.size)
    for j in range(0, len(newItem)):
        newItem[j]=np.nan
    df[name]=newItem
    df.to_csv('A1Ratings.csv', sep=',', encoding='utf-8', index=False)

def addUserScore2(userNumber, itemNumber, score):
    #pass
    df = pd.read_csv('A1Ratings.csv')
    df[df.columns[itemNumber+1]][userNumber]=score
    df.to_csv('A1Ratings.csv', sep=',', encoding='utf-8', index=False)


#################################################################COLLABORATIVE-ALGORITHMS#####################################################################


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
    try:
        return dotProduct (vecA,vecB) / math.sqrt(dotProduct(vecA,vecA)) / math.sqrt(dotProduct(vecB,vecB))
    except:
        return 0

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

