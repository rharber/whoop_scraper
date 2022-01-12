#!/usr/bin/env python3

import requests  # for getting URL
import pytz  # timezone adjusting
import time
import sys
import os
from datetime import datetime, timedelta, date  # datetime parsing
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

WHOOP_USERNAME = os.getenv("WHOOP_USERNAME")
WHOOP_PASSWORD = os.getenv("WHOOP_PASSWORD")


def main():
    try:
        user = WhoopUser(WHOOP_USERNAME, WHOOP_PASSWORD)
        user.print_line_protocol()

    except Exception as e:
        print(f'error msg="{e}" {time.time_ns()}')


#################################################################
class WhoopUser:
    """Creates an an instance of a WhoopUser with a validated access token and heartrate data.

    Arguments:
        username: (string - REQUIRED) The Whoop login username. (eg. 'ryan@gmail.com')
        password: (string - REQUIRED) The Whoop login password.
        start_date: (datetime.date - OPTIONAL) The datetime.date object of the
                    desired day to start the polling.
        window_s: (int - OPTIONAL) The length of the window to poll heartrate data from the api.
                    e.g. 480 (for 8 mins of heartrate data)
        interval_s: (int - OPTIONAL) The interval between BPM data points.
                    e.g. 6 (for BPM data point every 6 seconds)
    """

    def __init__(
        self, username, password, start_date=None, window_s=480, interval_s=6
    ) -> None:
        self.username = username
        self.password = password
        self.get_token()
        self.start_date = start_date
        self.set_start_dt()
        self.window_seconds = window_s
        self.interval_seconds = interval_s
        self.get_data()

    def get_token(self):
        # Post credentials
        r = requests.post(
            "https://api-7.whoop.com/oauth/token",
            json={
                "grant_type": "password",
                "issueRefresh": False,
                "password": self.password,
                "username": self.username,
            },
        )
        # Exit if fail
        if r.status_code != 200:
            msg = "Fail - Credentials rejected."
            print(f'error msg="{msg}" {time.time_ns()}')
            exit()

        # Set userid/token variables
        self.userid = r.json()["user"]["id"]
        self.access_token = r.json()["access_token"]

    def get_data(self):
        # Compute api start/end timestamps for desired window range
        api_end_time = self.start_datetime.replace(tzinfo=pytz.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        api_start_time = (
            (self.start_datetime - timedelta(seconds=self.window_seconds))
            .replace(tzinfo=pytz.utc)
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )

        # Download heartrate data
        url = "https://api-7.whoop.com/users/{}/metrics/heart_rate".format(self.userid)

        params = {
            "start": api_start_time,
            "end": api_end_time,
            # "step": self.interval_seconds,
            "step": self.interval_seconds,
        }
        # (FORMAT) params = {"start": "2022-01-01T00:00:00.000Z", "end": "2030-01-01T00:00:00.000Z"}

        headers = {"Authorization": "bearer {}".format(self.access_token)}

        r = requests.get(url, params=params, headers=headers)

        # Check if user/auth are accepted
        if r.status_code != 200:
            msg = "Fail - User ID / auth token rejected."
            print(f'error msg="{msg}" {time.time_ns()}')
            exit()

        # Convert to JSON
        self.data_raw = r.json()

    def print_line_protocol(self):
        try:
            for heartrate in self.data_raw["values"]:
                bpm = heartrate["data"]
                ns = heartrate["time"] * 1000000
                # Output line protocol
                print(f"heartrate,user_id={self.userid} bpm={bpm} {ns}")
        except Exception as e:
            print(f'error msg="{e}" {time.time_ns()}')
            exit()

    def set_start_dt(self):
        self.start_datetime = (
            datetime.combine(self.start_date, datetime.min.time())
            if self.start_date
            else datetime.utcnow()
        )


#################################################################

if __name__ == "__main__":
    main()
