"""
Facebook API helper
"""
import os
import re
import json
from http.cookies import SimpleCookie

import requests
from dotenv import load_dotenv

load_dotenv()


HEADERS = {
    "Connection": "keep-alive",
    "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    + "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}


def load_cookies() -> dict:
    """Load cookies from environment variable

    Returns:
        dict: dict of cookies
    """
    raw_cookie = os.getenv("COOKIES")
    if raw_cookie is None:
        raise ValueError("No cookies set in Env Var.")
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    cookies = {}
    for key, morsel in cookie.items():
        cookies[key] = morsel.value
    return cookies


class Fbook:
    """
    Facebook API helper
    """

    def __init__(self, cookies) -> None:
        self.cookies = cookies
        self.user_id = cookies["c_user"]
        self.dtsg = self.get_dtsg()

    def get_dtsg(self) -> str:
        """Get fb_dtsg from cookies

        Returns:
            str: fb_dtsg string
        """
        response = requests.get(
            "https://www.facebook.com/", headers=HEADERS, cookies=self.cookies
        )
        regex = r'DTSGInitialData",\[\],{"token":"([\d\w:]+)"'
        fb_dtsg = re.search(regex, response.content.decode(), re.S | re.M).group(1)
        return fb_dtsg

    def get_advertiser_list(self) -> list:
        """Get "seen_advertisers" list

        Returns:
            list: list of advertisers with data
        """
        response = requests.get(
            "https://www.facebook.com/adpreferences/advertisers",
            headers=HEADERS,
            cookies=self.cookies,
        )
        regex = r"tc_seen_advertisers(.*)tc_hidden_advertiser"
        parsed = re.search(regex, response.content.decode(), re.S | re.M).group(1)
        json_data = json.loads(parsed[slice(2, -2)])  # remove unecessary strings
        return json_data

    def hide_advertiser(self, page_id) -> bool:
        """Hide all ads from advertiser

        Args:
            page_id (str): page id to hide

        Returns:
            bool: hide status
        """
        variables = {
            "input": {
                "client_mutation_id": "1",
                "actor_id": self.user_id,
                "is_undo": False,
                "page_id": page_id,
            }
        }
        data = {
            "fb_dtsg": self.dtsg,
            "variables": json.dumps(variables),
            "doc_id": "3717265144980552",
        }

        response = requests.post(
            "https://www.facebook.com/api/graphql/",
            headers=HEADERS,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()
        try:
            if result["data"]["advertiser_hide"]["advertiser"]["is_hidden"] == True:
                return True
        except IndexError:
            print("Response is: ", result)
            return False
