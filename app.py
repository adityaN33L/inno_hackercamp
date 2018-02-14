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
import csv

async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

from helper import filter1,filter2,filter3,filter4,filter5,filter6,patternGen,compStrSymbol

##enter your host ip address in here
host_ip_address='127.0.0.1'

cred = {
            "access_key": "------enter access key---------", 
            "access_secret": "--------enter access secret---------", 
            "consumer_key": "------------enter consumer_key-----------", 
            "consumer_secret": "------------enter consumer_secret-----------"
        }


MONGO_HOST='mongodb://localhost/tweetdb'
client = MongoClient(MONGO_HOST)
db=client.tweetdb

auth = tweepy.OAuthHandler(cred['consumer_key'], cred['consumer_secret'])
auth.set_access_token(cred['access_key'], cred['access_secret'])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

class StdOutListener(StreamListener):
    def __init__(self):
        pass 
        
    def on_data(self, data):
        try: 
            tweetfile={}
            userfile={}
            all_data = json.loads(data)

            if 'text' in all_data:

                #created_at format conversion
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(all_data['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
                tweetfile["created_at"]     = ts   
                tweetfile["id_str"]         = all_data["id_str"]                               #string
                tweetfile["tweet"]          = all_data["text"]                                 #string
                tweetfile["source"]         = all_data["source"]                               #string
                tweetfile["truncated"]      = all_data["truncated"]                            #bool
                tweetfile["username"]       = all_data["user"]["name"]                         #string
                tweetfile["screen_name"]    = all_data["user"]["screen_name"]                  #string

                quote_count,reply_count,retweet_count,favorite_count=0,0,0,0
                if "retweeted_status" in all_data:  
                    quote_count     = all_data["retweeted_status"]["quote_count"]       #int
                    reply_count     = all_data["retweeted_status"]["reply_count"]       #int
                    retweet_count   = all_data["retweeted_status"]["retweet_count"]     #int        
                    favorite_count  = all_data["retweeted_status"]["favorite_count"]    #int
                tweetfile["quote_count"]    =quote_count
                tweetfile["reply_count"]    =reply_count
                tweetfile["retweet_count"]  =retweet_count
                tweetfile["favorite_count"] =favorite_count

                urls=[]
                for i in all_data["entities"]["urls"]:
                    urls.append(i["display_url"])
                tweetfile["urls"]            = urls                                 #list

                user_mentions=[]
                for i in all_data["entities"]["user_mentions"]:
                    user_mentions.append(i["name"])
                tweetfile["user_mentions"]   = user_mentions                        #list

                tweetfile["retweeted"]       = all_data["retweeted"]                #bool
                tweetfile["favorited"]       = all_data["favorited"]                #bool
                
                if 'possibly_sensitive' in all_data:
                    possibly_sensitive  = str(all_data["possibly_sensitive"])       #bool
                else:
                    possibly_sensitive  = "Not verified"

                tweetfile["possibly_sensitive"]=possibly_sensitive                  #bool
                tweetfile["lang"]       = all_data["lang"]                          #string


                #---------------------user details--------------------------#
                userfile["username"]        = all_data["user"]["name"]                          #string
                userfile["screen_name"]     = all_data["user"]["screen_name"]                   #string
                userfile["user_id"]         = all_data["user"]["id_str"]                        #string
                userfile["user_location"]   = all_data["user"]["location"]
                userfile["verified"]        = all_data["user"]["verified"]                      #bool
                userfile["friends_count"]   = all_data["user"]["friends_count"]                 #int
                userfile["followers_count"] = all_data["user"]["followers_count"]               #int
                userfile["favourites_count"]      = all_data["user"]["favourites_count"]        #int
                userfile["profile_img"]     = all_data["user"]["profile_image_url_https"]       #string
                #---------------------user details--------------------------#

                ##inserting relevant data to collections
                db.tweetCollection.insert(tweetfile)
                db.userCollection.insert(userfile)

            socketio.emit('stream_channel',all_data,namespace='/demo_streaming')
            #print json.dumps(all_data, indent=4, sort_keys=True)
        except: 
            pass 

    def on_error(self, status):
        print 'Error status code', status
        exit()


##index page invoked
@app.route('/')
def index():
    return render_template('index.html')


def background_thread_api1(keyword):
    if keyword:
        stream = Stream(auth, StdOutListener())
        key_list=keyword.split(",")
        stream.filter(track=key_list)


##api1 invoked
@app.route('/api1')
def api1():
    
    keyword=request.args.get('keyword')
    thread = Thread(target=background_thread_api1,args=(keyword,))
    thread.daemon = True
    thread.start()    
    return render_template('api1.html')


##api2 invoked
@app.route('/api2')
def api2():
    output=[]

    #------------------URL VARIABLES------------------#
    try:
        page          =int(request.args.get('page'))     ## pageNo
        inputval      =request.args.get('inputval')      ## value entered (integer / string)
        comparator    =request.args.get('comparator')    ## equals / greater_than / less_than
        searchFilter  =request.args.get('searchFilter')  ## tweet / username / screen_name
        posFilter     =request.args.get('posFilter')     ## contains / exactMatch / startsWith / endsWith
        tcnt          =request.args.get('tcnt')          ## tweet_count / reply_count / quote_count / favorite_count
        usercnt       =request.args.get('usercnt')       ## friends_count / followers_count
        lang          =request.args.get('lang')          ## en / es etc.
        startDate     =request.args.get('startDate')     ## YYYY-MM-DD
        endDate       =request.args.get('endDate')       ## YYYY-MM-DD
        entitiesFilter=request.args.get('entitiesFilter')## user_mentions / urls
        sortDate      =request.args.get('sortDate')      ## y / n
    except:
        return render_template('api2.html')

    #------------------URL VARIABLES------------------#
    if not sortDate:
        sortDate='n'
    if sortDate!='n' and sortDate!='y' and sortDate!='Y':
        return render_template('api2.html')

    ##---------------filter using tweet text, username and screen name
    if searchFilter and posFilter and inputval:
        output=filter1(searchFilter,posFilter,inputval,sortDate)

    ##--------------filter using retweet count, reply count, favorite count, quote count
    elif tcnt and inputval and comparator:
        output=filter2(tcnt,comparator,inputval,sortDate)
    
    ##--------------filter using friend's count and follower's count  
    elif usercnt and inputval and comparator:  
        output=filter3(usercnt,comparator,inputval,sortDate)

    ##--------------filter using tweet language
    elif lang:
        output=filter4(lang,sortDate)

    ##--------------filter using date range YYYY-MM-DD
    elif endDate and startDate:
        output=filter5(startDate,endDate,sortDate)

    ##--------------filter using entities like user_mentions and urls
    elif inputval and entitiesFilter and posFilter:
        output=filter6(entitiesFilter,posFilter,inputval,sortDate)

    
    try:

        #-----------------------API3 implementation--------------------------#
        keys = output[0].keys()
        fieldnames=[]
        if len(keys)==16:
            fieldnames = ['tweet','id_str','username','retweet_count', 'possibly_sensitive','created_at','lang']
        elif len(keys)==9:
            fieldnames=['username','screen_name','friends_count','followers_count','profile_img','verified','user_id']

        with open('output.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(output)):
                writer.writerow({fieldnames[0]: output[i][fieldnames[0]].encode('utf-8'), fieldnames[1]: output[i][fieldnames[1]].encode('utf-8'),fieldnames[2]: str(output[i][fieldnames[2]]).encode('utf-8'), fieldnames[3]: str(output[i][fieldnames[3]]).encode('utf-8'), fieldnames[4]: output[i][fieldnames[4]].encode('utf-8'), fieldnames[5]: output[i][fieldnames[5]].encode('utf-8'), fieldnames[6]: output[i][fieldnames[6]].encode('utf-8')})

        #-----------------------API3 implementation--------------------------#

        #-----------------------Pagination mathematics-----------------------#
        start=(page-1)*10
        end=(start+10)-1
        if end > len(output)-1:
            end=len(output) -1
        #-----------------------Pagination mathematics-----------------------#

        result=[]
        for i in range(start,end+1):
            result.append(output[i])

        return jsonify({'result':result}) 
    except:
        return render_template('api2.html')


if __name__ == '__main__':
    socketio.run(app, debug=True, host=host_ip_address) 
