# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

#Global vars
TIMEOUT = 10 #sec
TIMEOUT_ELE = 15 #sec
TIMEOUT_DONT_ALLOW = 3 #sec
PATH = os.path.sep + os.path.dirname(os.path.realpath(__file__)) + os.path.sep
SETUP = False
# Login info
LOGIN_CONFIG = False
TIMEOUT_LOGIN = 3 #sec

#Config
chromeProfile_dir = '--user-data-dir=' + os.path.dirname(os.path.realpath(__file__)) \
                    + os.path.sep +'/ChromeProfile'
FB_URL = 'https://www.facebook.com/adpreferences/advertisers'

# ============================
# Locators
see_more_btn = (By.XPATH, '//span[text()="See More"]')
hide_ads_btn = (By.XPATH, '//span[text()="Hide Ads"]')


class RemoveAdlist:
    def __init__(self, url, setup=False):
        self.url = url
        self.setup = setup
        self.driver = init_chrome()
        self.failure = 0

    def get_element_visible(self, elem_loc, ordinal=0):
        elem = WebDriverWait(self.driver, TIMEOUT_ELE).until(\
            EC.visibility_of_all_elements_located(elem_loc))
        if ordinal == 'list':
            return elem
        else:
            return elem[ordinal]

    def wait_clickable(self, elem_loc):
        return WebDriverWait(self.driver, TIMEOUT_ELE).until(\
            EC.element_to_be_clickable(elem_loc))

    def scroll_to_view(self, elem):
        self.driver.execute_script("arguments[0].scrollIntoView();", elem)

    def _hide_ad(self):
        print(f"Hid ad!")

    def load_avertisers(self):
        self.driver.get(self.url)
        if self.setup:
            time.sleep(300) # wait for 5 mins then do absolutely nothing
            sys.exit()
        try:
            WebDriverWait(self.driver, 3).until(\
                        EC.visibility_of_element_located(see_more_btn)).click()
        except TimeoutException:
            pass

        time.sleep(1)
        print("Done loading advertisers.")

    def refresh(self):
        self.driver.refresh()

    def hide_ads(self):
        ad_list = self.get_element_visible(hide_ads_btn, 'list')
        for ad_btn in ad_list:
            ad_btn.click()
        time.sleep(2)

    def quit(self):
        self.driver.close()
        self.driver.quit()

def init_chrome(headless=False):
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('test-type')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument(chromeProfile_dir)
    chrome_options.add_argument('--remote-debugging-port=9222')
    prefs = {"profile.managed_default_content_settings.images": 2,}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1000,800)
    driver.set_page_load_timeout(TIMEOUT)
    return driver

def error_log(error_mess):
    print("\n", '*'*30)
    print("ERROR:\n")
    print(error_mess)
    print("\n", '*'*30)

def log_step(step):
    print(f"==> {step}")

if __name__ == "__main__":
    # os.environ["PATH"] += PATH + "driver"
    AD_NUM = 2
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == "debug":
            SETUP = True
        if sys.argv[1].lower() == "load":
            AD_NUM = int(sys.argv[2])
    log_step(chromeProfile_dir)
    fb = RemoveAdlist(FB_URL, SETUP)
    try:
        for counter in range(AD_NUM):
            log_step(f"Load newsfeed the {counter + 1} time.")
            fb.load_avertisers()
            fb.hide_ads()
    except Exception as er_log:
        error_log(er_log)
    fb.quit()
