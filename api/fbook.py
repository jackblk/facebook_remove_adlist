"""
Facebook API helper
"""
import os
import re
import json
import logging
import hashlib
from http.cookies import SimpleCookie

import requests
from dotenv import load_dotenv
from rich.logging import RichHandler

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
log = logging.getLogger(__name__)

RETRY = 3
HEADERS = {
    "Connection": "keep-alive",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    + "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}
GRAPHQL_API_URL = "https://www.facebook.com/api/graphql/"


def load_cookies(env_file_override: bool = False) -> dict:
    """Load cookies from environment variable

    Args:
        env_file (bool): override env var using env file

    Returns:
        dict: dict of cookies
    """
    log.info(f"Override from env file: {env_file_override}")
    load_dotenv(override=env_file_override)

    if email_ := os.getenv("FB_EMAIL"):
        log.info("Generating FB cookies from app password")
        password_ = os.getenv("FB_APP_PASSWORD", "")
        auth = FbAuth(email_, password_)
        raw_cookie = auth.get_cookies_string()
    else:
        log.info("Getting FB cookies from Env Var")
        raw_cookie = os.getenv("FB_COOKIES")
        if raw_cookie is None:
            raise ValueError("No cookies set in Env Var.")

    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    cookies = {}
    for key, morsel in cookie.items():
        cookies[key] = morsel.value
    return cookies


# login method from Pidgin plugin https://github.com/dequis/purple-facebook
# this method gets checkpoint, but only first time, next time it will return cookies

# alternate way, but always get checkpoint, save here for reference
# https://b-api.facebook.com/method/auth.login?access_token=237759909591655%25257C0f140aabedfb65ac27a739ed1a2263b1&format=json&sdk_version=2&email=XXXX&locale=en_US&password=XXXX&sdk=ios&generate_session_cookies=1&sig=3f555f99fb61fcd7aa0c44f58f522ef
class FbAuth:
    """Facebook Auth Helper"""

    def __init__(self, email: str = "", password: str = "") -> None:
        self.email = email
        self.password = password
        self.credentials = {}

    def get_fb_credentials(self) -> dict:
        """Get FB credentials

        Token, cookies, machine id

        Returns:
            dict: credentials of user
        """
        headers = {
            "Host": "b-api.facebook.com",
            "Connection": "Keep-Alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Facebook Helper / FRA / 1.0 "
            "[FBAN/Orca-Android;FBAV/192.0.0.31.101;"
            "FBPN/com.facebook.orca;FBLC/en_US;FBBV/52182662]",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        fb_android_messenger_api_key = "256002347743983"
        fb_android_messenger_secret_key = "374e60f8b9bb6b8cbb30f78030438895"

        data_dict = {
            "fb_api_req_friendly_name": "authenticate",
            "locale": "en",
            "email": self.email,
            "password": self.password,
            "format": "json",
            "api_key": fb_android_messenger_api_key,
            "method": "auth.login",
            "generate_session_cookies": "1",
        }

        # signature calculation
        # https://stackoverflow.com/questions/3324444/is-auth-token-and-sig-the-same-thing-in-facebook-api/3324546#3324546
        pre_signed_data = ""
        for key in sorted(data_dict.keys()):
            pre_signed_data = pre_signed_data + key + "=" + data_dict[key]
        pre_signed_data += fb_android_messenger_secret_key
        data_dict["sig"] = hashlib.md5(pre_signed_data.encode()).hexdigest()

        args = []
        for key in sorted(data_dict.keys()):
            args.append(f"{key}={data_dict[key]}")
        final_data = "&".join(args)

        response = requests.post(
            "https://b-api.facebook.com/method/auth.login",
            headers=headers,
            data=final_data,
        )
        self.credentials = response.json()
        return self.credentials

    def get_cookies_string(self) -> str:
        """Return cookies in string format

        Returns:
            str: cookies in string format
        """
        self.get_fb_credentials()
        try:
            cookies_dict = self.credentials["session_cookies"]
        except KeyError as err:
            log.error(f"Login error. Response:\n {self.credentials}")
            raise err
        cookies_list = []
        for cookie in cookies_dict:
            cookies_list.append(f"{cookie['name']}={cookie['value']}")
        raw_cookie = ";".join(cookies_list)
        return raw_cookie


class Fbook:
    """
    Facebook API helper
    """

    def __init__(self, cookies) -> None:
        self.headers = HEADERS
        self.cookies = cookies
        self.user_id: str = cookies["c_user"]
        self.dtsg: str = self.get_dtsg()

    def get_dtsg(self) -> str:
        """Get fb_dtsg from cookies via API

        Returns:
            str: fb_dtsg string
        """
        regex = r"fb_dtsg\\\" value=\\\"([\d\w:-]+)\\\""
        response = requests.get(
            "https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed",
            headers=self.headers,
            cookies=self.cookies,
        )
        if "Set-Cookie" in response.headers:
            raise Exception("Cookie is invalid.")
        fb_dtsg = re.search(regex, response.content.decode(), re.S | re.M)
        if fb_dtsg is None:
            log.error("Cannot get DTSG")
            raise TypeError
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
        result = re.search(regex, response.content.decode(), re.S | re.M)
        if result is None:
            log.error("Cannot find advertisers.")
            raise TypeError
        parsed = result.group(1)[slice(2, -2)]
        json_data = json.loads(parsed)  # remove unecessary strings
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
            log.error(f"Failed to hide. Response is: '{result}'")
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

    def opt_out_business(self, business_id: str) -> bool:
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
                log.warning(f"'{business_id}' is not a valid id (response null).")
            return True
        except IndexError:
            log.info(f"Something went wrong. Response: \n{result}")
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
            log.info(f"Something went wrong. Response: \n{result}")
            return False
        return True
