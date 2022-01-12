# Whoop API Scraper for InfluxDB

Python script that polls the [Whoop Unofficial API](https://app.swaggerhub.com/apis/DovOps/whoop-unofficial-api/2.0.1) and generates line protocol for use with InfluxDB.

## Getting Started

### Installing

* Clone the project and install requirements.
```
git clone https://github.com/rharber/whoop_scraper.git
cd whoop_scraper
pip install -r requirements.txt
```
* Create a '.env' file with your whoop login credentials
```
WHOOP_USERNAME={your whoop username}
WHOOP_PASSWORD={your whoop password}
```

### Executing program

```
python3 whoop_scraper.py
```

## Acknowledgments
* [jkreileder](https://gist.github.com/jkreileder)
