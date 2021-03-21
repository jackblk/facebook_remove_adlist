import sys
from rich import print  # pylint: disable=redefined-builtin

from api.api_config import Fbook
from api.api_config import load_cookies

print("Loading cookies from environment variable.")
COOKIES = load_cookies()
fb = Fbook(COOKIES)

if __name__ == "__main__":
    LOAD_NUM = 2
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == "load":
            LOAD_NUM = int(sys.argv[2])
    print(f"Will try to load advertiser list for {LOAD_NUM} time(s).\n")

    for counter in range(LOAD_NUM):
        print(f"Getting Advertisers list no {counter+1}.")
        ad_list = fb.get_advertiser_list()
        if len(ad_list) == 0:
            print("No advertiser found!")
            break

        print("\nHiding Advertisers.")
        for ad_page in ad_list:
            page_id = ad_page["advertiser_id"]
            page_name = ad_page["name"]
            print(f"Hiding page '{page_name}', id '{page_id}'", end="")
            STATUS = fb.hide_advertiser(page_id)
            print(f" Hidden: '{STATUS}'.")
