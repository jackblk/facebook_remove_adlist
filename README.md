# Facebook Adlist Remover
## What does it do?
Auto remove Advertisers's list. This list will help Facebook to show you ads. Just remove it.
## Dependencies
`pip install -r requirements.txt`

## Setup
1. `python adlist_remove.py debug`. The browser will be open and stay for 5 mins.
2. Login your Facebook account.
3. Close the browser nicely. Close command line.

Setting up correctly will help you to create a folder `ChromeProfile` with logged in session.

## Run
`python adlist_remove.py`
Let it do its job :).


--------

## Removing via FB API (No UI)

WIP, will replace UI version later.

### Setting up
Create a file `.env` in this folder, copy your Facebook cookies from browser to this file:
```
COOKIES="your_cookies"
```
Or you can set it to enviroment variable `COOKIES` from your OS (not recommended).

Run `python del_via_api.py`