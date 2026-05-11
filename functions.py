import time, sys, pandas as pd
import base64
import logging
from contextlib import contextmanager
from styles import license, Config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException,
    NoAlertPresentException,
)

# Configure logging with file and console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BROWSER = "".join(license)

# Initialize Chrome WebDriver
def create_driver():
    logging.info("Initializing Chrome WebDriver")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

# Log in to tinchi.neu.edu.vn system
def login(driver, MSV, MK):
    logging.info(f"Attempting login with MSV: {MSV}")
    try:
        driver.get("https://tinchi.neu.edu.vn/Login/index")
        logging.info("Navigated to login page")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(MSV)
        driver.find_element(By.ID, "password").send_keys(MK)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Đăng nhập']").click()

        WebDriverWait(driver, 5).until(
            EC.any_of(
                EC.url_contains("tinchi.neu.edu.vn"),
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        )

        page_source = driver.page_source
        if "Lỗi hệ thống mạng" in page_source:
            logging.error("Login failed: Network error or incorrect credentials")
            return False, driver

        if "tinchi.neu.edu.vn" in driver.current_url:
            logging.info("Login successful")
            return True, driver
        logging.warning("Login failed: Unknown reason")
        return False, driver
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return False, driver

# Generate ID for MLHP
def generateID(MLHP):
    logging.info(f"Generating ID for MLHP: {MLHP}")
    subject, group = MLHP.split("_", 1)
    generated_id = f"{subject}_{group}$0.0${subject}$$0"
    logging.info(f"Generated ID: {generated_id}")
    return generated_id

# Refresh the page
def refresh_page(driver):
    logging.info("Refreshing page")
    try:
        driver.refresh()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logging.info("Page refreshed successfully")
    except Exception as e:
        logging.error(f"Refresh page error: {str(e)}")

# Find subject by MHP
def findSubject(driver, MHP, MLHP, max_retries, stop_event=None):
    if stop_event and stop_event.is_set():
        logging.info("Stop event detected, exiting findSubject")
        return False
    logging.info(f"Finding subject: {MHP}")
    try:
        xpath = f"//a[contains(@href, '{MHP}')]"
        register_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", register_button)
        register_button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "cnDanhSachLHP")))
        cnDanhSachLHP = driver.find_element(By.ID, "cnDanhSachLHP").text
        if "Đang tải dữ liệu" in cnDanhSachLHP or "lỗi" in cnDanhSachLHP.lower():
            logging.warning(f"Subject {MHP} loading issue")
            return False

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'GetClassStudyUnit')]"))
        )
        return findClass(driver, MHP, MLHP, max_retries, stop_event=stop_event)
    except TimeoutException:
        logging.error(f"Timeout while finding subject {MHP}")
        return False
    except Exception as e:
        logging.error(f"Error finding subject {MHP}: {str(e)}")
        return False

# Find class by MLHP, with retry limit
def findClass(driver, MHP, MLHP, max_retries, stop_event=None, timeout=1):
    if stop_event and stop_event.is_set():
        logging.info("Stop event detected, exiting findClass")
        return False
    logging.info(f"Finding class: {MLHP} (Retries left: {max_retries})")

    if max_retries <= 0:
        findBack(driver)
        logging.info(f"Exceeded max retries for class {MLHP}")
        return False

    try:
        xpath = f"//input[@type='radio' and contains(@onclick, '{MLHP}')]"
        radio_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", radio_button)

        if radio_button.is_enabled():
            radio_button.click()
            logging.info(f"Selected class: {MLHP}")
            return findSubmit(driver)
    except (TimeoutException, ElementNotInteractableException):
        logging.warning(f"Timeout or interaction issue with class {MLHP}, navigating back")
        if findBack(driver):
            return findSubject(driver, MHP, MLHP, max_retries - 1, stop_event)
        return False
    except Exception as e:
        logging.error(f"Error finding class {MLHP}: {str(e)}")
        return False

# Find and click the Register button
def findSubmit(driver, timeout=3):
    try:
        xpath = "//div[@class='pull-right']//input[@type='button' and @value='Đăng ký' and contains(@class, 'btn-cus1')]"
        button = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
        button.click()
        logging.info("Clicked Register button")
        return True
    except Exception as e:
        logging.error(f"Error finding submit button: {str(e)}")
        return False

# Find and click the Back button
def findBack(driver, timeout=10):
    try:
        xpath = "//div[@class='pull-right']//input[@type='button' and @value='Quay về' and contains(@class, 'btn-cus1')]"
        button = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", button)
        button.click()
        return True
    except Exception as e:
        logging.error(f"Error finding back button: {str(e)}")
        return False

# Check and dismiss alert
def check_and_dismiss_alert(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        logging.info(f"Alert dismissed: {alert_text}")
        return alert_text
    except Exception as e:
        logging.info(f"No alert present or error: {str(e)}")
        return None

# Cache for MSV list
class MSVCache:
    _msv_list = None

    @classmethod
    def load_list(cls):
        if cls._msv_list is None:
            try:
                googlesheets = "https://docs.google.com/spreadsheets/d/e/"
                df = pd.read_csv(googlesheets + base64.b64decode(BROWSER).decode() + "/pub?output=csv")
                cls._msv_list = set(df.iloc[:, 0].astype(str))
                logging.info("Successfully loaded MSV list")
            except Exception as e:
                logging.error(f"Error loading MSV list: {str(e)}")
        return cls._msv_list

# Check if MSV is in the valid list
def checkMSV(MSV):
    try:
        result = MSV in MSVCache.load_list()
        logging.info(f"MSV check result for {MSV}: {result}")
        return result
    except Exception as e:
        logging.error(f"Error checking MSV: {str(e)}")
        return False

# Execute course registration with maximum retries
def execute(driver, MHP, MLHP, max_retries=3, stop_event=None):
    logging.info(f"Executing registration for MHP: {MHP}, MLHP: {MLHP} with {max_retries} retries")
    if stop_event and stop_event.is_set():
        logging.info("Stop event detected, exiting execute")
        return
    try:
        findSubject(driver, MHP, MLHP, max_retries, stop_event)
        alert_text = check_and_dismiss_alert(driver)
        logging.info(f"{MLHP}. Alert: {alert_text}")
    except Exception as e:
        logging.error(f"ERROR (execute): {str(e)}")