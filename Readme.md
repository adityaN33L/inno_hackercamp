# Twitter Streaming API  

You have to add twitter credentials in the cred parameter in app.py. Also to test other keywords, change the list _keywords. 

```
$ sudo apt-get install -y libatlas-base-dev gfortran python-dev build-essential g++ 
$ sudo apt-get install libffi-dev libssl-dev
```
## Setup the virtual environment
```
$ virtualenv --dist venv
$ source venv/bin/activate
$ pip install -r requirements.txt 
```
OR 
## If you don't want virtualenv
```
$ sudo pip install -r requirements.txt
```

## Run the server
```
$ sudo python app.py 
```
## Checkout the output in the browser. 
```
http://127.0.0.1:5000
```
### Database Schema:
- **db**: tweetdb
- **collections**: tweetCollection, userCollection
	
### sample URLs:
- http://localhost:5000/api1?keyword=modi
- http://localhost:5000/api2?searchFilter=username&posFilter=endsWith&inputval=beck&sortDate=y&page=1

### url parameters:
- **page** : pageNo  
- **inputval** : value entered (integer / string)  
- **comparator** : equals / greater_than / less_than  
- **searchFilter** : tweet / username / screen_name  
- **posFilter** : contains / exactMatch / startsWith / endsWith  
- **tcnt** : tweet_count / reply_count / quote_count / favorite_count  
- **usercnt** : friends_count / followers_count  
- **lang** : en / es etc.  
- **startDate** : YYYY-MM-DD  
- **endDate** : YYYY-MM-DD  
- **entitiesFilter** : user_mentions / urls  
- **sortDate** : y / n  
