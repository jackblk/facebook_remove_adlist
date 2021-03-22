# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import time
import sys
import pretty_errors
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

pretty_errors.replace_stderr()

#Global vars
TIMEOUT = 10 #sec
TIMEOUT_ELE = 15 #sec
TIMEOUT_DONT_ALLOW = 3 #sec
PATH = os.path.sep + os.path.dirname(os.path.realpath(__file__)) + os.path.sep
SETUP = False
FAILURE_LIMIT = 5
# Login info
LOGIN_CONFIG = False
TIMEOUT_LOGIN = 3 #sec

#Config
chromeProfile_dir = '--user-data-dir=' + os.path.dirname(os.path.realpath(__file__)) \
                    + os.path.sep +'/ChromeProfile'
FB_URL = 'https://www.facebook.com/'

# ============================
# Locators
sponsored_post_menu_win =  '//a/span/span[count(./span) > 25]/../../../../../../../..//div[@aria-haspopup]'
sponsored_post_menu_linux =  '//a/span/b[count(./b) > 25]/../../../../../../../..//div[@aria-haspopup]'
sponsored_post_menu = sponsored_post_menu_linux + '|' + sponsored_post_menu_win
hide_ad_btn = (By.XPATH, '//span[text()="Hide ad"]')
irre_btn = (By.XPATH, '//span[text()="Irrelevant"]')
done_btn = (By.XPATH, '//div[@aria-label="Done"]')
hide_all_ads_from_btn = (By.XPATH, '//span[contains(text(), "Hide all ads from")]')

class RemoveAdlist:
    def __init__(self, url, setup=False):
        self.url = url
        self.setup = setup
        self.driver = init_chrome()
        self.failure = 0
        self.ads_hidden = 0

    def get_element_visible(self, elem_loc, ordinal=0, timeout = TIMEOUT_ELE):
        elem = WebDriverWait(self.driver, timeout).until(\
            EC.visibility_of_all_elements_located(elem_loc))
        if ordinal == 'list':
            return elem
        else:
            return elem[ordinal]

    def wait_clickable(self, elem_loc):
        return WebDriverWait(self.driver, TIMEOUT_ELE).until(\
            EC.element_to_be_clickable(elem_loc))

    def go_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_to_view(self, elem):
        self.driver.execute_script("arguments[0].scrollIntoView();", elem)

    def _hide_ad(self):
        self.wait_clickable(hide_ad_btn).click()
        self.wait_clickable(irre_btn).click()
        self.wait_clickable(done_btn).click()
        self.wait_clickable(hide_all_ads_from_btn).click()
        self.wait_clickable(done_btn).click()
        self.failure = 0 # reset counter
        self.ads_hidden += 1
        print("Hid ad!")

    def load_newsfeed(self):
        self.driver.get(self.url)
        if self.setup:
            time.sleep(300) # wait for 5 mins then do absolutely nothing
            sys.exit()
        self.go_to_bottom()
        time.sleep(1)
        for _ in range(4):    
            try:
                self.get_element_visible((By.XPATH, sponsored_post_menu), timeout = 1)
                break
            except TimeoutException:
                self.go_to_bottom()
                time.sleep(1)
        print("Done loading newsfeed.")

    def refresh(self):
        self.driver.refresh()

    def hide_all_sponsored(self):
        try:
            ad_menu_btn = self.get_element_visible((By.XPATH, sponsored_post_menu), timeout = 1)
        except TimeoutException:
            self.failure += 1
            if self.failure >= FAILURE_LIMIT:
                raise Exception(f"Failed more than {FAILURE_LIMIT} times, maybe no more ads?")
            return
        # self.scroll_to_view(ad_menu_btn)
        time.sleep(0.5)
        ad_menu_btn.click()
        self._hide_ad()
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
    driver.set_window_size(700,900)
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
            fb.load_newsfeed()
            fb.hide_all_sponsored()
            fb.refresh()
        fb.quit()
        log_step(f"Hid total of {fb.ads_hidden}.")
    except Exception as er_log:
        fb.quit()
        error_log(er_log)
        raise Exception(er_log)
