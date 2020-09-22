# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
import time
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
chromeProfile_dir = '--user-data-dir=' + os.path.dirname(os.path.realpath(__file__)) + os.path.sep +'/ChromeProfile'
FB_URL = 'https://www.facebook.com/ds/preferences/'

# ============================
# Locators
iframe = (By.XPATH, '//iframe')
ad_and_business_loc = (By.XPATH, '//div[text()="Advertisers and businesses"]')
your_interests_loc = (By.XPATH, '//div[text()="Your interests"]')
see_more_loc = (By.XPATH, '//div[text()="See more"]')
view_control_btn = (By.XPATH, '//div[text()="View controls"]')
dont_allow_loc = (By.XPATH, '//div[text()="Showing ads to you using a list"]/../../button/div/div')
business_name_loc = (By.XPATH, '//div[contains(text(),"List controls")]')
done_btn_loc = (By.XPATH, '//div[text()="Done"]')



class RemoveAdlist:
    def __init__(self, url, setup=False):
        self.url = url
        self.setup = setup
        self.driver = init_chrome()
        self.list = None

    def get_element_visible(self, elem_loc, ordinal=0):
        elem = WebDriverWait(self.driver, TIMEOUT_ELE).until(\
            EC.visibility_of_all_elements_located(elem_loc))
        if ordinal == 'list':
            return elem
        else:
            return elem[ordinal]

    def is_displayed(self, elem_loc):
        pass
    def prepare_adlist(self):
        self.driver.get(self.url)
        if self.setup:
            time.sleep(300) # wait for 5 mins then do absolutely nothing
            sys.exit()
        self.driver.switch_to.frame(self.get_element_visible(iframe))
        interest = self.get_element_visible(your_interests_loc)
        interest.click()
        ad_bus_row = self.get_element_visible(ad_and_business_loc)
        ad_bus_row.click()
        more = self.get_element_visible(see_more_loc)
        try:
            while more.is_displayed():
                more.click()
        except:
            log_step("Loaded all.")
        self.list = self.get_element_visible(view_control_btn, 'list')

    def remove_adlist(self):
        counter = 0
        remove_list = []
        for elem in self.list:
            WebDriverWait(self.driver, TIMEOUT_DONT_ALLOW).until(\
                EC.element_to_be_clickable(view_control_btn))
            elem.location_once_scrolled_into_view
            try:
                elem.click()
            except:
                time.sleep(1)
                elem.click()
            business = self.get_element_visible(business_name_loc).text
            business = re.sub (r'List controls for ', '', business)
            button = self.get_element_visible(dont_allow_loc)
            log_step(f"[{counter}] {business}. Button is '{button.text}'\n")
            if button.text == "Don't Allow":
                button.click()
                remove_list.append(business)
            self.get_element_visible(done_btn_loc).click()
            counter += 1
        log_step(f"\nRemoved {len(remove_list)}: {remove_list}")
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
    # chrome_options.add_argument('--window-size=1440, 1080')
    prefs = {"profile.managed_default_content_settings.images": 2,}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
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
    if len(sys.argv) >= 2:
        if sys.argv[1] == "debug":
            SETUP = True
    log_step(chromeProfile_dir)
    fb = RemoveAdlist(FB_URL, SETUP)
    fb.prepare_adlist()
    fb.remove_adlist()
