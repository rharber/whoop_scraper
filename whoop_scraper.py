#!/usr/bin/env python3

import requests  # for getting URL
import time
import pytz
import sys
import os
from datetime import datetime, timedelta, date, timezone  # datetime parsing
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
        self.window_seconds = window_s
        self.interval_seconds = interval_s
        # self.heartrate_data = {"values": []}
        self.get_heartrate_data()
        self.get_cycle_data()

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

    def set_api_timestamps(self, data_type="heartrate"):
        self.start_datetime = (
            datetime.combine(self.start_date, datetime.min.time())
            if self.start_date
            else datetime.utcnow()
        )

        if data_type == "cycle":
            self.window_seconds = 432000  # make window 5 days for cycle data only

        # Compute api start/end timestamps for desired window range
        self.api_end_time = self.start_datetime.replace(tzinfo=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.api_start_time = (
            (self.start_datetime - timedelta(seconds=self.window_seconds))
            .replace(tzinfo=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )

    def get_heartrate_data(self):
        self.set_api_timestamps()

        url = f"https://api-7.whoop.com/users/{self.userid}/metrics/heart_rate"

        params = {
            "start": self.api_start_time,
            "end": self.api_end_time,
            "step": self.interval_seconds,
        }  # (FORMAT) params = {"start": "2022-01-01T00:00:00.000Z", "end": "2030-01-01T00:00:00.000Z"}

        headers = {"Authorization": f"bearer {self.access_token}"}

        r = requests.get(url, params=params, headers=headers)

        # Check if user/auth are accepted
        if r.status_code != 200:
            msg = "Fail - User ID / auth token rejected."
            print(f'error msg="{msg}" {time.time_ns()}')
            exit()

        # Convert to JSON
        self.heartrate_data = r.json()

    def get_cycle_data(self):
        self.set_api_timestamps("cycle")

        url = f"https://api-7.whoop.com/users/{self.userid}/cycles"

        params = {
            "start": self.api_start_time,
            "end": self.api_end_time,
        }  # (FORMAT) params = {"start": "2022-01-01T00:00:00.000Z", "end": "2030-01-01T00:00:00.000Z"}

        headers = {"Authorization": f"bearer {self.access_token}"}

        r = requests.get(url, params=params, headers=headers)

        # Check if user/auth are accepted
        if r.status_code != 200:
            msg = "Fail - User ID / auth token rejected."
            print(f'error msg="{msg}" {time.time_ns()}')
            exit()

        # Convert to JSON
        self.sleep_workout_data = r.json()

    def print_line_protocol(self):
        try:
            for heartrate in self.heartrate_data["values"]:
                bpm = heartrate["data"]
                ns = heartrate["time"] * 1000000
                print(f"heartrate,user_id={self.userid} bpm={bpm} {ns}")

            for day in self.sleep_workout_data:
                if day["sleep"] and day["sleep"]["state"] == "complete":
                    dt = datetime.strptime(day["days"][0], "%Y-%m-%d")
                    ns = int(round(dt.timestamp())) * 1000 * 1000000
                    sleep = day["sleep"]
                    print(
                        f"sleep,user_id={self.userid} sleep_score={sleep['score']} {ns}"
                    )
                if day["strain"] and day["strain"]["workouts"]:
                    for workout in day["strain"]["workouts"]:
                        dt = datetime.strptime(day["days"][0], "%Y-%m-%d")
                        ns = int(round(dt.timestamp())) * 1000 * 1000000
                        print(
                            f"workout,user_id={self.userid} max_heartrate={workout['maxHeartRate']} {ns}"
                        )

        except Exception as e:
            print(f'error msg="{e}" {time.time_ns()}')
            exit()


#################################################################

if __name__ == "__main__":
    main()
