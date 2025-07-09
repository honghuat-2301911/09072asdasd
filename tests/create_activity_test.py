import os
import sys
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class CreateActivityPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--ignore-certificate-errors")  # <-- key line
        options.add_argument("--allow-insecure-localhost")  # optional, but useful
        options.add_argument("--headless")  # for CI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        cls.driver.implicitly_wait(10)
        cls.base_url = "https://localhost"

        # Use the seeded email and password created to test create activity
        cls.seeded_email = "2301875@sit.singaporetech.edu.sg"
        cls.seeded_password = "123123123"

    def fill_login_form(self, email, password):
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CLASS_NAME, "login-btn").click()
        time.sleep(2)

    def test_create_activity_success(self):
        try:
            # Assert that the login with the seeded email and password is successful
            # After login, the user should be redirected to the bulletin board page
            self.fill_login_form(email=self.seeded_email, password=self.seeded_password)
            self.assertIn("Bulletin Board", self.driver.page_source)

            # Open the host activity modal
            host_button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Host Activity')]"
            )
            host_button.click()
            time.sleep(1)  # Wait for modal animation

            # Fill in the activity form
            self.driver.find_element(By.ID, "activityNameInput").send_keys(
                "Selenium Test Activity"
            )
            self.driver.find_element(By.ID, "activityTypeInput").send_keys("Sports")
            self.driver.find_element(By.ID, "skillsReqInput").send_keys("None")

            date_input = self.driver.find_element(By.ID, "dateInput")
            self.driver.execute_script(
                "arguments[0].value = arguments[1]", date_input, "2025-07-08T15:30"
            )

            self.driver.find_element(By.ID, "locationInput").send_keys("Test Field")
            self.driver.find_element(By.ID, "maxPaxInput").clear()
            self.driver.find_element(By.ID, "maxPaxInput").send_keys("10")

            # Submit the form
            self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Host')]"
            ).click()
            time.sleep(2)

            # Assert that the activity was created successfully
            self.assertIn("Selenium Test Activity", self.driver.page_source)
            # activity_card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'card')]//h3[text()='Selenium Test Activity']")
            # self.assertTrue(activity_card.is_displayed())

        except Exception as e:
            os.makedirs("artifacts", exist_ok=True)
            self.driver.save_screenshot("artifacts/create_activity_success.png")
            with open("artifacts/debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise  # Re-raise so the test still fails

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()


if __name__ == "__main__":
    unittest.main()
