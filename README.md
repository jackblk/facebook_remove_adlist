## Facebook adlist remover

Disclaimer: use this repo at your risk.
### What does it do?

Businesses will have your info when you use their services (playing games, listening to music...). Then they will upload the info to Facebook and Facebook will use that info to serve you personalized ads.

This repo will help you to:
* Exclude yourself (opt-out) from business adlist.
* Hide all ads from the page that served you ads.

By doing this:
* You will be served unrelated ads.
* By doing it long enough, you will exclude yourself from every ad wave that Facebook is trying to serve to you.

That means, you will not see any ads for a long time (2-3 months), **then they will come back**. Run this repo again for 1-2 days, you will see no ads anymore.

This is my experience using this method for **more than 3 years** and it has been working perfectly for me, but it **might not work for you**.

### Setting up
Create a file `.env` in this folder, copy your Facebook cookies from browser to this file:
```
COOKIES="your_cookies"
```
Or you can set it to enviroment variable `COOKIES` from your OS (not recommended).

### Hide all ads from page
Run `python del_advertisers.py`

You can check the result here: [Advertisers](https://www.facebook.com/adpreferences/advertisers)
### Opt out from business adlist & removing interests
Run `python opt_out_business_adlist.py` and `python remove_interest.py`

Check the result here: [Ad settings](https://www.facebook.com/adpreferences/ad_settings), Audience-based advertising & Interest categories.
