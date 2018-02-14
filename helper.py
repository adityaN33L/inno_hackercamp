import json 
import time
import re
from threading import Thread
from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
from tweepy.streaming import StreamListener
from tweepy import Stream
import tweepy 
from pymongo import MongoClient

MONGO_HOST='mongodb://localhost/tweetdb'
client = MongoClient(MONGO_HOST)
db=client.tweetdb

def patternGen(posFilter,keyword):
    if posFilter=="contains":
        pat=re.compile(r'%s' % keyword,re.IGNORECASE)
    elif posFilter=="exactMatch":
        pat=re.compile(r'%s\w*' % re.escape(keyword))
    elif posFilter=="startsWith":
        pat=re.compile(r'^%s' % re.escape(keyword),re.IGNORECASE)
    elif posFilter=="endsWith":
        pat=re.compile(r'%s$' % re.escape(keyword),re.IGNORECASE)
    return pat


def compStrSymbol(comp):
    if comp=="equals":
        return "$eq"
    elif comp=="greater_than":
        return "$gt"
    elif comp=="less_than":
        return "$lt"


##---------------filter using tweet text, username and screen name
def filter1(searchFilter,posFilter,keyword,sortDate):
    pattern=patternGen(posFilter,keyword)
    output=[]
    tab=db.tweetCollection.find({})
    if sortDate=='y' or sortDate=='Y':
        tab=db.tweetCollection.find({}).sort([("_id",-1)])

    for q in tab:
        txt=q[searchFilter]
        if re.search(pattern,txt):
            output.append({'tweet':q['tweet'],'id_str':q['id_str'],'username':q['username'],'screen_name':q['screen_name'],'created_at':q['created_at'],'source':q['source'],'retweet_count':q['retweet_count'],'quote_count':q['quote_count'],'reply_count':q['reply_count'],'favorite_count':q['favorite_count'],'urls':q['urls'],'user_mentions':q['user_mentions'],'retweeted':q['retweeted'],'favorited':q['favorited'],'possibly_sensitive':q['possibly_sensitive'],'lang':q['lang']})
    
    return output

##--------------filter using retweet count, reply count, favorite count, quote count
def filter2(tcnt,comparator,keyword,sortDate):
    keyword=int(keyword)
    comp=compStrSymbol(comparator) 
    output=[]
    tab=db.tweetCollection.find({tcnt:{comp:keyword}})
    if sortDate=='y' or sortDate=='Y':
        tab=db.tweetCollection.find({tcnt:{comp:keyword}}).sort([("_id",-1)])

    for q in tab:
        output.append({'tweet':q['tweet'],'id_str':q['id_str'],'username':q['username'],'screen_name':q['screen_name'],'created_at':q['created_at'],'source':q['source'],'retweet_count':q['retweet_count'],'quote_count':q['quote_count'],'reply_count':q['reply_count'],'favorite_count':q['favorite_count'],'urls':q['urls'],'user_mentions':q['user_mentions'],'retweeted':q['retweeted'],'favorited':q['favorited'],'possibly_sensitive':q['possibly_sensitive'],'lang':q['lang']})

    return output

##--------------filter using friend's count and follower's count 
def filter3(usercnt,comparator,keyword,sortDate):
    keyword=int(keyword)
    comp=compStrSymbol(comparator)
    ulist=[]
    tab=db.userCollection.find({usercnt:{comp:keyword}})
    if sortDate=='y' or sortDate=='Y':
        tab=db.userCollection.find({usercnt:{comp:keyword}}).sort([("_id",-1)])

    for rec in tab:
        temp={}
        temp["username"]=rec["username"]
        temp["screen_name"]=rec["screen_name"]
        temp["user_id"]=rec["user_id"]
        temp["user_location"]=rec["user_location"]
        temp["verified"]=rec["verified"]
        temp["friends_count"]=rec["friends_count"]
        temp["followers_count"]=rec["followers_count"]
        temp["favourites_count"]=rec["favourites_count"]
        temp["profile_img"]=rec["profile_img"]
        ulist.append(temp)

    new_ulist = []
    seen = set()
    for d in ulist:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_ulist.append(d)
    return new_ulist

##--------------filter using tweet language
def filter4(langFilter,sortDate):
    output=[]
    tab=db.tweetCollection.find({'lang':langFilter})
    if sortDate=='y' or sortDate=='Y':
        tab=db.tweetCollection.find({'lang':langFilter}).sort([("_id",-1)])

    for q in tab:
        output.append({'tweet':q['tweet'],'id_str':q['id_str'],'username':q['username'],'screen_name':q['screen_name'],'created_at':q['created_at'],'source':q['source'],'retweet_count':q['retweet_count'],'quote_count':q['quote_count'],'reply_count':q['reply_count'],'favorite_count':q['favorite_count'],'urls':q['urls'],'user_mentions':q['user_mentions'],'retweeted':q['retweeted'],'favorited':q['favorited'],'possibly_sensitive':q['possibly_sensitive'],'lang':q['lang']})
    return output

##--------------filter using date range YYYY-MM-DD
def filter5(d1,d2,sortDate):
    output=[]
    nd1=time.strptime(d1,"%Y-%m-%d")
    nd2=time.strptime(d2,"%Y-%m-%d")

    tab=db.tweetCollection.find({})
    if sortDate=='y' or sortDate=='Y':
        tab=db.tweetCollection.find({}).sort([("_id",-1)]) 

    for q in tab:
        nd3=time.strptime(q["created_at"][0:10],"%Y-%m-%d")
        if nd3>=nd1 and nd3<=nd2:
            output.append({'tweet':q['tweet'],'id_str':q['id_str'],'username':q['username'],'screen_name':q['screen_name'],'created_at':q['created_at'],'source':q['source'],'retweet_count':q['retweet_count'],'quote_count':q['quote_count'],'reply_count':q['reply_count'],'favorite_count':q['favorite_count'],'urls':q['urls'],'user_mentions':q['user_mentions'],'retweeted':q['retweeted'],'favorited':q['favorited'],'possibly_sensitive':q['possibly_sensitive'],'lang':q['lang']})

    return output

##--------------filter using entities like user_mentions and urls
def filter6(entitiesFilter,posFilter,keyword,sortDate):
    output=[]
    pattern=patternGen(posFilter,keyword)

    tab=db.tweetCollection.find({})
    if sortDate=='y' or sortDate=='Y':
        tab=db.tweetCollection.find({}).sort([("_id",-1)])
        

    for q in tab:
        arr=q[entitiesFilter]
        for i in arr:
            if re.search(pattern,i):
                output.append({'tweet':q['tweet'],'id_str':q['id_str'],'username':q['username'],'screen_name':q['screen_name'],'created_at':q['created_at'],'source':q['source'],'retweet_count':q['retweet_count'],'quote_count':q['quote_count'],'reply_count':q['reply_count'],'favorite_count':q['favorite_count'],'urls':q['urls'],'user_mentions':q['user_mentions'],'retweeted':q['retweeted'],'favorited':q['favorited'],'possibly_sensitive':q['possibly_sensitive'],'lang':q['lang']})

    return output