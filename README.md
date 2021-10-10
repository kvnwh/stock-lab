## Local setup:
```
python3 -m venv .venv
source .vent/bin/activate
python3 -m pip install -r requirements.txt
```
create `env.conf` with following keys:
```
[secrets]
device_token = {get_it_from_robinhood}
auth_token = {get_it_from_robinhood}
refresh_token = {get_it_from_robinhood}
fcm_api_key = {get_it_from_fcm}
```

To add new package: `python3 -m pip install <package> && python3 -m pip freeze > requirements.txt`

#### Bitcoin tracker
Record bitcoin price in a interval and % change, will export data to csv

run `python3 main.py`

#### Stock portfolio
Robinhood stock profolio in pie chart

run `python3 portfolio_pie.py`

### Stock intrinsic value 
Using some stock intrinsic value model to calculate stock value (-__-!!)

run `python3 stock_evaluator.py {TICKER}`, or using flask `/value/{ticker}` endpoint


### Flask
run `export FLASK_APP=app` specify which app to run

run `flask run`

host: `http://127.0.0.1:5000`
endpoints:
 - `/info/{ticker}`: get yahoo finance data about the ticker
 - `/value/{ticker}`: get intrinsic value of a stock 

### Code formatting
`black .` at root