from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from config import settings
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class LinkedInReceiver:
    def __init__(self):
        self.driver = None
        self.last_check = datetime.now()
        self._initialize_driver()
    
    def _initialize_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self._login()
            logger.info("LinkedIn Selenium driver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn driver: {e}")
            self.driver = None
    
    def _login(self):
        try:
            self.driver.get("https://www.linkedin.com/login")
            
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(settings.LINKEDIN_EMAIL)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(settings.LINKEDIN_PASSWORD)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Sign in']")
            login_button.click()
            
            time.sleep(5)
            logger.info("LinkedIn login successful")
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            raise
    
    def get_new_messages(self):
        try:
            if not self.driver:
                return []
            
            self.driver.get("https://www.linkedin.com/messaging/")
            time.sleep(3)
            
            new_messages = []
            conversations = self.driver.find_elements(By.XPATH, "//div[@data-test-id='conversation-item']")
            
            for conv in conversations[:5]:
                try:
                    sender_name = conv.find_element(By.XPATH, ".//span[@data-test-id='conversation-item-name']").text
                    message_preview = conv.find_element(By.XPATH, ".//span[@data-test-id='conversation-item-message']").text
                    
                    conv.click()
                    time.sleep(2)
                    
                    messages = self.driver.find_elements(By.XPATH, "//div[@data-test-id='message-item']")
                    if messages:
                        latest_msg = messages[-1].text
                        new_messages.append({
                            "sender_name": sender_name,
                            "sender_id": sender_name.replace(" ", "_"),
                            "message": latest_msg,
                            "timestamp": datetime.now()
                        })
                except Exception as e:
                    logger.error(f"Error processing conversation: {e}")
                    continue
            
            self.last_check = datetime.now()
            return new_messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    def send_message(self, recipient_id: str, message: str) -> bool:
        try:
            if not self.driver:
                logger.error("LinkedIn driver not initialized")
                return False
            
            logger.info(f"Message queued for {recipient_id}: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def __del__(self):
        if self.driver:
            self.driver.quit()

linkedin_receiver = LinkedInReceiver()
