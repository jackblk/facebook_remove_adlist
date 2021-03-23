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


RETRY = 3
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
GRAPHQL_API_URL = "https://www.facebook.com/api/graphql/"


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
        self.headers = HEADERS
        self.cookies = cookies
        self.user_id = cookies["c_user"]
        self.dtsg = self.get_dtsg()

    def get_dtsg(self) -> str:
        """Get fb_dtsg from cookies via API

        Returns:
            str: fb_dtsg string
        """
        # regex = r'DTSGInitialData",\[\],{"token":"([\d\w:]+)"'  # getting in script tag
        regex = r'name="fb_dtsg" value="([\d\w:]+)"'
        for retry_ in range(RETRY):
            response = requests.get(
                "https://m.facebook.com/", headers=self.headers, cookies=self.cookies
            )
            fb_dtsg = re.search(regex, response.content.decode(), re.S | re.M)
            if fb_dtsg is None:
                print(f"Error getting DTSG, retry {retry_+1}.")
                continue
            else:
                break
        if fb_dtsg is None:
            raise Exception(f"Cannot get DTSG after {RETRY} tries.")
        return fb_dtsg.group(1)

    def get_advertiser_list(self) -> list:
        """Get "seen_advertisers" list

        Returns:
            list: list of advertisers with data
        """
        response = requests.get(
            "https://www.facebook.com/adpreferences/advertisers",
            headers=self.headers,
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
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdPreferencesHideAdvertiserMutation",
            "variables": json.dumps(variables),
            "doc_id": "3717265144980552",
        }

        response = requests.post(
            GRAPHQL_API_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()
        try:
            if result["data"]["advertiser_hide"]["advertiser"]["is_hidden"] is True:
                return True
            return False
        except IndexError:
            print("Failed to hide. Response is: ", result)
            return False

    def get_business_adlist(self, no_filter: bool = False) -> list:
        """Get a list of businesses that uploaded adlist about you.

        Will only return businesses that you have not Opt-out of adlist yet.
        Use `no_filter=True` for a full list.

        Args:
            no_filter (bool, optional): will return full list if True. Defaults to False.

        Returns:
            list: list of businesses that uploaded adlist about you.
        """
        data = {
            "av": self.user_id,
            "__user": self.user_id,
            "fb_dtsg": self.dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdPreferencesListBasedLandingPageQuery",
            "variables": "{}",
            "server_timestamps": "true",
            "doc_id": "3226537680809256",
        }
        response = requests.post(
            GRAPHQL_API_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()["data"]["tc_businesses_with_ca"]
        if no_filter is True:
            return result
        parsed_result = [
            ad_business
            for ad_business in result
            if ad_business["dfca_inclusion_opted_out"] is False
            and ad_business["business_id"] is not None
        ]
        return parsed_result

    def opt_out_business(self, business_id) -> bool:
        """Opt out of a business adlist.

        Args:
            business_id (str): business id to opt out.

        Returns:
            bool: opt out status
        """
        variables = {
            "input": {
                "client_mutation_id": "2",
                "actor_id": self.user_id,
                "business_id": business_id,
                "operation": "DONT_ALLOW",
                "type": "INCLUSION",
            }
        }
        data = {
            "av": self.user_id,
            "__user": self.user_id,
            "fb_dtsg": self.dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdPreferencesDFCABusinessOptOutMutation",
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "2693764404041988",
        }
        response = requests.post(
            GRAPHQL_API_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()
        try:
            id_ = result["data"]["update_dfca_optout"]["business_info"]["id"]
            if id_ == "eyJ0eXBlIjoiVENCdXNpbmVzc0lEIiwiYmlkIjpudWxsLCJwaWQiOm51bGx9":
                print(f"'{business_id}' is not a valid id (response null).")
            return True
        except IndexError:
            print("Something went wrong. Response: \n", result)
            return False

    def get_interest_list(self) -> list:
        """Get interest list from user

        Returns:
            list: list of interests
        """
        data = {
            "av": self.user_id,
            "__user": self.user_id,
            "fb_dtsg": self.dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdPreferencesInterestCategoriesPageQuery",
            "variables": "{}",
            "server_timestamps": "true",
            "doc_id": "2916949545027630",
        }
        response = requests.post(
            GRAPHQL_API_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()["data"]["tc_user_interests"]
        return result

    def remove_interest(self, interest_id) -> bool:
        """Remove interest of ad preference

        Args:
            interest_id (str): interest id

        Returns:
            bool: status of removing
        """
        variables = {"interestID": interest_id, "isUndo": False}
        data = {
            "av": self.user_id,
            "__user": self.user_id,
            "fb_dtsg": self.dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdPreferencesInterestCategoryOptOutMutation",
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "3765701203502096",
        }
        response = requests.post(
            GRAPHQL_API_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()
        if "errors" in result["data"]:
            print("Something went wrong. Response: \n", result)
            return False
        return True
