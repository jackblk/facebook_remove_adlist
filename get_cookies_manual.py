"""
Generate token and cookies from app password
"""
from getpass import getpass
import click
from api.fbook import FbAuth


@click.command()
@click.option("--email", default=None, help="Email or username")
def get_cookies(email):
    """Get cookies and export to .env file

    Args:
        email (string): email for username
    """
    if email is None:
        email = input("Enter email or username: ")
    password_ = getpass()
    auth = FbAuth()
    auth.fb_email = email
    auth.fb_password = password_
    env_str_cookie = f'FB_COOKIES="{auth.get_cookies_string()}"'

    with open(".env", "w", encoding="utf-8") as file:
        file.write(env_str_cookie)


if __name__ == "__main__":
    get_cookies()  # pylint: disable=no-value-for-parameter
