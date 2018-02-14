You have to add twitter credentials in the cred parameter in app.py. Also to test other keywords, change the list _keywords. 

```
$ sudo apt-get install -y libatlas-base-dev gfortran python-dev build-essential g++
$ sudo apt-get install libffi-dev libssl-dev

```
# Setup the virtual environment
```
$ virtualenv --dist venv
$ source venv/bin/activate
$ pip install -r requirements.txt 
```
OR 
# If you don't want virtualenv
```
$ sudo pip install -r requirements.txt
```

# Run the server
```
$ sudo python app.py 
```
# Checkout the output in the browser. 
```
http://127.0.0.1:5000
```
Database Schema:
tweetdb
	tweetCollection
	userCollection
	
sample URLs
-->http://localhost:5000/api1?keyword=modi
-->http://localhost:5000/api2?searchFilter=username&posFilter=endsWith&inputval=beck&sortDate=y&page=1
