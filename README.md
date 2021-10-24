## Local setup:
```
python3 -m venv .venv
source .vent/bin/activate
pip install -r requirements.txt
```
create `env.conf` with following keys:
```
[secrets]
device_token = {get_it_from_robinhood}
auth_token = {get_it_from_robinhood}
refresh_token = {get_it_from_robinhood}
fcm_api_key = {get_it_from_fcm}
```

To add new package: `pip install <package> && pip freeze > requirements.txt`

#### Bitcoin tracker
Record bitcoin price in a interval and % change, will export data to csv

run `python3 main.py`

#### Stock portfolio
Robinhood stock profolio in pie chart

run `python3 portfolio_pie.py`

### Stock intrinsic value 
Using some stock intrinsic value model to calculate stock value (-__-!!)

run `python3 stock_evaluator.py {TICKER}`, or using flask `/value/{ticker}` endpoint


### Web server
run `python3 webapp.py`, host is 3000

or run `waitress-serve --port=8080 webapp:app`
host: `http://127.0.0.1:8080`

endpoints:
 - `/stocks/{ticker}/info`: get yahoo finance data about the ticker
 - `/stocks/{ticker}/evaluation`: get intrinsic value of a stock 
 - `/stocks/tracking`: record stock tracking

### Code formatting
`black .` at root