# Facebook adlist remover

Disclaimer: use this repo at your risk.
## What does it do?

Businesses will have your info when you use their services (playing games, listening to music...). Then they will upload the info to Facebook and Facebook will use that info to serve you personalized ads.

This repo will help you to:
* Exclude yourself (opt-out) from business adlist.
* Hide all ads from the page that served you ads.
* Remove all interests that FB collected.

By doing this:
* You will be served unrelated ads.
* By doing it long enough, you will exclude yourself from every ad wave that Facebook is trying to serve to you.

That means, you will not see any ads for a long time (2-3 months), **then they will come back**. Run this repo again for 1-2 days, you will see no ads anymore.

This is my experience using this method for **more than 3 years** and it has been working perfectly for me, but it **might not work for you**.

## Docker

[User Guide](https://github.com/jackblk/facebook_remove_adlist/wiki/User-Guide-for-Docker-image)

[Development Guide](https://github.com/jackblk/facebook_remove_adlist/wiki/Development-Guide-for-Docker-image)

## Installation
### Install dependencies

Python version: >=3.8

`python -m pip install -r requirements.txt`

### Setting up
Create a file `.env` in this folder, copy your Facebook cookies from browser to this file:
```
FB_COOKIES="your_cookies"
```
Or you can set it to enviroment variable `FB_COOKIES` from your OS.

## Usage

To view all commands & helps, run `python fb_adlist.py`

To run all commands at once:
```bash
python fb_adlist.py all
```

### Hide all ads from page

Advertisers will load as a list, by default it will try to hide 2 lists.
Use option `--count` or `-c` to load more than 2 lists.
```bash
python fb_adlist.py del-ad -c 10
```

You can check the result here: [Advertisers](https://www.facebook.com/adpreferences/advertisers)
### Opt out from business adlist & Removing interests
```bash
# Opt-out of business adlist
python fb_adlist.py opt-out
# Remove all interests
python fb_adlist.py rm-interest
```

Check the result here: [Ad settings](https://www.facebook.com/adpreferences/ad_settings), Audience-based advertising & Interest categories.
