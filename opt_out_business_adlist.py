from rich import print  # pylint: disable=redefined-builtin

from api.fbook import Fbook
from api.fbook import load_cookies

print("Loading cookies from environment variable.")
COOKIES = load_cookies()
fb = Fbook(COOKIES)

if __name__ == "__main__":
    print("Loading business adlist.")
    business_adlist = fb.get_business_adlist()
    print(f"Found '{len(business_adlist)}' business(es).")
    for business in business_adlist:
        name_ = business["name"]
        id_ = business["business_id"]
        if id_ is None:
            print(f"Business '{name_}' with id '{id_}' does not have adlist. Skipping.")
            continue
        print(f"Opting out business '{name_}' with id '{id_}'.", end="")
        STATUS = fb.opt_out_business(business["business_id"])
        print(f" Status: {STATUS}.")
