"""
Facebook API helper
"""
import os
import re
import json
import logging
import hashlib
import uuid
from http.cookies import SimpleCookie
from typing import Dict

import requests
from dotenv import load_dotenv
from rich.logging import RichHandler
import mintotp

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
log = logging.getLogger(__name__)


# login method from Pidgin plugin https://github.com/dequis/purple-facebook
# this method gets checkpoint, but only first time, next time it will return cookies

# alternate way, but always get checkpoint, save here for reference
# https://b-api.facebook.com/method/auth.login?access_token=237759909591655%25257C0f140aabedfb65ac27a739ed1a2263b1&format=json&sdk_version=2&email=XXXX&locale=en_US&password=XXXX&sdk=ios&generate_session_cookies=1&sig=3f555f99fb61fcd7aa0c44f58f522ef
class BaseFBAPI:  # pylint: disable=too-few-public-methods
    """Base const for FB API"""

    # FB Auth
    LOGIN_URL = "https://b-api.facebook.com/method/auth.login"
    LOGIN_HEADERS = {
        "Host": "b-api.facebook.com",
        "Connection": "Keep-Alive",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Facebook Helper / FRA / 1.0 "
        "[FBAN/Orca-Android;FBAV/537.0.0.31.101;FBPN/com.facebook.orca;FBLC/en_US;FBBV/52182662]",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }
    FB_ANDROID_MESSENGER_API_ID = "256002347743983"
    FB_ANDROID_MESSENGER_SECRET_KEY = "374e60f8b9bb6b8cbb30f78030438895"

    # FB GRAPH API
    GRAPH_URL = "https://www.facebook.com/api/graphql/"
    GRAPH_HEADERS = {
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


class FbAuth(BaseFBAPI):
    """Facebook Auth Helper"""

    def __init__(self) -> None:
        # Basic info
        load_dotenv()
        self.fb_email = os.getenv("FB_EMAIL")
        self.fb_password = os.getenv("FB_PASSWORD")
        self.fb_cookies = os.getenv("FB_COOKIES")
        self.fb_totp_2fa_secret = os.getenv("FB_TOTP_2FA_SECRET")
        self.credentials = {}

        # For Auth
        self.session = requests.Session()
        self.device_id = str(uuid.uuid4())

    @property
    def base_data(self):
        """Base data for FB Auth"""
        return {
            "fb_api_req_friendly_name": "authenticate",
            "locale": "en",
            "email": self.fb_email,
            "password": self.fb_password,
            "format": "json",
            "api_key": self.FB_ANDROID_MESSENGER_API_ID,
            "method": "auth.login",
            "generate_session_cookies": "1",
            "generate_machine_id": "1",
            "device_id": self.device_id,
        }

    def load_cookies(self) -> Dict[str, str]:
        """Load cookies from environment variable

        Returns:
            dict: dict of cookies
        """
        if self.fb_email:
            log.info("Generating FB cookies")
            raw_cookie = self.get_cookies_string()
        else:
            log.info("Getting FB cookies from Env Var")
            raw_cookie = self.fb_cookies
            if raw_cookie is None:
                raise ValueError("No cookies set in Env Var.")

        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value
        return cookies

    def format_data(self, data_dict: Dict[str, str]) -> str:
        """Data signature calculation

        https://stackoverflow.com/questions/3324444/is-auth-token-and-sig-the-same-thing-in-facebook-api/3324546#3324546
        https://mau.dev/mautrix/facebook

        Args:
            data_dict (Dict[str, str]): Dict of data to send

        Returns:
            str: signed data
        """
        pre_signed_data = "".join(
            f"{key}={value}" for key, value in sorted(data_dict.items())
        )
        pre_signed_data += self.FB_ANDROID_MESSENGER_SECRET_KEY
        data_dict["sig"] = hashlib.md5(pre_signed_data.encode("utf-8")).hexdigest()
        return "&".join(f"{key}={value}" for key, value in sorted(data_dict.items()))

    def get_fb_credentials(self) -> dict:
        """Get FB credentials

        Token, cookies, machine id

        Returns:
            dict: credentials of user
        """
        data_dict = self.base_data

        response = self.session.post(
            self.LOGIN_URL,
            headers=self.LOGIN_HEADERS,
            data=self.format_data(data_dict),
        )

        if "error_data" in response.json():
            error_data = json.loads(response.json()["error_data"])
            # if there's login_first_factor, then try approving 2fa
            if "login_first_factor" in error_data:
                self.credentials = self.approve_2fa(error_data)
                return self.credentials
            # else, it will just return the response, then Exception will be raised

        self.credentials = response.json()
        return self.credentials

    def approve_2fa(self, error_data: Dict[str, str]) -> dict:
        """Approve 2FA via 2FA code

        Args:
            error_data (Dict[str, str]): Error data from checkpoint

        Returns:
            dict: credentials from user
        """
        data = self.base_data
        if self.fb_totp_2fa_secret:
            data["twofactor_code"] = mintotp.totp(self.fb_totp_2fa_secret)
        else:
            data["twofactor_code"] = input("2fa code here: ")

        data["credentials_type"] = "two_factor"
        data["error_detail_type"] = "button_with_disabled"
        data["first_factor"] = error_data["login_first_factor"]
        data["password"] = data["twofactor_code"]
        data["userid"] = error_data["uid"]
        data["machine_id"] = error_data["machine_id"]
        # data_dict["currently_logged_in_userid"] = data_dict["0"]

        response = self.session.post(
            self.LOGIN_URL,
            headers=self.LOGIN_HEADERS,
            data=self.format_data(data),
        )
        return response.json()

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


class Fbook(BaseFBAPI):
    """
    Facebook API helper
    """

    def __init__(self, cookies: Dict[str, str]) -> None:
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
            headers=self.GRAPH_HEADERS,
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
            headers=self.GRAPH_HEADERS,
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
            self.GRAPH_URL,
            headers=self.GRAPH_HEADERS,
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
            self.GRAPH_URL,
            headers=self.GRAPH_HEADERS,
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
            self.GRAPH_URL,
            headers=self.GRAPH_HEADERS,
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
            self.GRAPH_URL,
            headers=self.GRAPH_HEADERS,
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
            self.GRAPH_URL,
            headers=self.GRAPH_HEADERS,
            cookies=self.cookies,
            data=data,
        )
        result = response.json()
        if "errors" in result["data"]:
            log.info(f"Something went wrong. Response: \n{result}")
            return False
        return True
