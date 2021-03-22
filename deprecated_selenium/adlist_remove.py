# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#Global vars
TIMEOUT = 10 #sec
TIMEOUT_ELE = 15 #sec
TIMEOUT_DONT_ALLOW = 3 #sec
TIMEOUT_CLICKABLE = 3
PATH = os.path.sep + os.path.dirname(os.path.realpath(__file__)) + os.path.sep
SETUP = False
# Login info
LOGIN_CONFIG = False
TIMEOUT_LOGIN = 3 #sec

#Config
chromeProfile_dir = '--user-data-dir=' + os.path.dirname(os.path.realpath(__file__)) \
                    + os.path.sep +'/ChromeProfile'
FB_URL = 'https://www.facebook.com/adpreferences/ad_settings'

# ============================
# Locators
audience_based_loc = (By.XPATH, '//span[text()="Audience-based advertising"]')
see_all_business_loc = (By.XPATH, '//div[@aria-label="See All Businesses"]')

businesses_loc = (By.XPATH, '//span[contains(text(), "Audience-based")]/../../../..//div[contains(@style,"padding-top: 8px;")]/div/div') # pylint: disable=C0301
list_usage_btn_loc = (By.XPATH, '//span[contains(text(), "You may have")]|//span[contains(text(), "They uploaded")]') # pylint: disable=C0301
dont_allow_btn_loc = (By.XPATH, '//span[contains(text(), "Showing")]/../../../../../../../..//div[contains(@aria-label, "Allow")]|//span[text()="Hide"]|//span[text()="Undo"]') # pylint: disable=C0301
back_btn_loc = (By.XPATH, '//span[contains(text(),"Website, App") or contains(text(),"List ")]/../../../..//div[@aria-label="Back"]') # pylint: disable=C0301
back_tolist_btn_loc = (By.XPATH, '//div[@aria-label="Back"]') # pylint: disable=C0301


class RemoveAdlist:
    def __init__(self, url, setup=False):
        self.url = url
        self.setup = setup
        self.driver = init_chrome()
        self.list_business_elem = None
        self.list_business_name = None
        self.progress = 0

    def get_element_visible(self, elem_loc, ordinal=0):
        elem = WebDriverWait(self.driver, TIMEOUT_ELE).until(\
            EC.visibility_of_all_elements_located(elem_loc))
        if ordinal == 'list':
            return elem
        else:
            return elem[ordinal]

    def wait_clickable(self, elem_loc):
        return WebDriverWait(self.driver, TIMEOUT_CLICKABLE).until(\
            EC.element_to_be_clickable(elem_loc))

    def prepare_adlist(self):
        self.driver.get(self.url)
        if self.setup:
            time.sleep(300) # wait for 5 mins then do absolutely nothing
            sys.exit()
        self.wait_clickable(audience_based_loc).click()
        self.wait_clickable(see_all_business_loc).click()
        WebDriverWait(self.driver, 5).until(\
            EC.invisibility_of_element_located(see_all_business_loc))
        self.list_business_elem = self.get_element_visible(businesses_loc, 'list')
        self.list_business_name = [x.text for x in self.list_business_elem]

    def remove_adlist(self):
        remove_list = []
        for business_elem in self.list_business_elem:
            if self.progress >= len(self.list_business_elem):
                break
            business_name = self.list_business_name[self.progress]
            self.progress += 1
            business_elem: WebElement
            business_elem.location_once_scrolled_into_view # pylint: disable=W0104
            try:
                business_elem.click()
            except: # pylint: disable=W0702
                time.sleep(2)
                business_elem.click()
            self.wait_clickable(list_usage_btn_loc).click()
            button = self.wait_clickable(dont_allow_btn_loc)
            log_step(f"[{self.progress}] {business_name}. Button is '{button.text}'\n")
            if button.text.lower() in ("don't allow", "hide"):
                button.click()
                remove_list.append(business_name)
            self.wait_clickable(back_btn_loc).click()
            self.wait_clickable(back_tolist_btn_loc).click()
        log_step(f"\nRemoved {len(remove_list)}: {remove_list}")

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
    SKIP_ADLIST = 0
    if len(sys.argv) >= 2:
        if sys.argv[1] == "debug":
            SETUP = True
        if sys.argv[1].lower() == "skip":
            SKIP_ADLIST = int(sys.argv[2])
    log_step(chromeProfile_dir)
    fb = RemoveAdlist(FB_URL, SETUP)
    try:
        fb.prepare_adlist()
        fb.progress = SKIP_ADLIST
        fb.remove_adlist()
    except Exception as error:
        error_log(error)
    fb.quit()
