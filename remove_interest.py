from rich import print  # pylint: disable=redefined-builtin

from api.fbook import Fbook
from api.fbook import load_cookies

print("Loading cookies from environment variable.")
COOKIES = load_cookies()
fb = Fbook(COOKIES)

if __name__ == "__main__":
    print("Loading interest list.")
    interest_list = fb.get_interest_list()
    print(f"Found '{len(interest_list)}' interest(s).")
    for interest in interest_list:
        name_ = interest["name"]
        id_ = interest["interest_id"]
        print(f"Removing interest '{name_}' with id '{id_}'.", end="")
        STATUS = fb.remove_interest(interest["interest_id"])
        print(f" Status: {STATUS}.")
