"""
Generate token and cookies from app password
"""
from getpass import getpass
from api.fbook import FbAuth

if __name__ == "__main__":
    # get app password here
    # https://www.facebook.com/settings?tab=security&section=per_app_passwords
    email_ = input("Enter email or username:")
    password_ = getpass()
    auth = FbAuth(email_, password_)
    env_str_cookie = f'FB_COOKIES="{auth.get_cookies_string()}"'

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_str_cookie)
