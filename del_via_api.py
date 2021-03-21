from rich import print

from api.api_config import Fbook
from api.api_config import load_cookies

print("Loading cookies from environment variable.")
COOKIES = load_cookies()
fb = Fbook(COOKIES)
print("Getting Advertisers.")
ad_list = fb.get_advertiser_list()

print("\nHiding Advertisers.")
for ad_page in ad_list:
    page_id = ad_page["advertiser_id"]
    page_name = ad_page["name"]
    print(f"Hiding page '{page_name}', id '{page_id}'", end="")
    STATUS = fb.hide_advertiser(page_id)
    print(f"Status: '{STATUS}''.")
