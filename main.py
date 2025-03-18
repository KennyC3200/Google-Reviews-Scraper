from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
from guara.transaction import AbstractTransaction, Application  # Corrected import

# Constants
REVIEWS_SECTION_CSS = 'div[class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]'
REVIEW_ELEMENT_CSS = 'div[class="jftiEf fontBodyMedium "]'
MORE_BUTTON_CSS = 'button[class="w8nwRe kyuRq"]'
DESCRIPTION_CSS = 'span[class="wiI7pd"]'
MORE_DESCRIPTION_CSS = 'div[jslog="127691"]'


# Define Transactions
class InitDriver:
    def do(self, **kwargs):
        print("Setting up Chrome driver...")
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)


class NavigateToRestaurant(AbstractTransaction):
    def do(self, url, **kwargs):
        print(f"Navigating to restaurant page: {url}")
        self._driver.get(url)
        time.sleep(3)


class ClickReviewsButton(AbstractTransaction):
    def do(self, **kwargs):
        print("DEBUG: Looking for reviews button")
        try:
            reviews_button = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[jsaction*="reviewChart"]'))
            )
            if reviews_button:
                print("DEBUG: Clicking reviews button")
                self._driver.execute_script("arguments[0].click();", reviews_button)
                time.sleep(3)
        except TimeoutException:
            print("ERROR: Couldn't find the reviews button. Taking screenshot for debugging")
            self._driver.save_screenshot("debug_screenshot.png")
            return False
        return True


class WaitForReviewsSection(AbstractTransaction):
    def do(self, **kwargs):
        print("DEBUG: Waiting for reviews to load")
        try:
            reviews_div = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, REVIEWS_SECTION_CSS))
            )
            print("DEBUG: Reviews section found!")
            return reviews_div
        except TimeoutException:
            print("ERROR: Couldn't find the reviews section. Taking screenshot")
            self._driver.save_screenshot("debug_screenshot2.png")
            return None


class ScrollAndCollectReviews(AbstractTransaction):
    def do(self, reviews_div, num_reviews, **kwargs):
        reviews = []
        seen_reviews = set()
        last_height = self._driver.execute_script("return arguments[0].scrollHeight", reviews_div)
        scroll_attempts = 0
        max_scroll_attempts = 30

        while len(reviews) < num_reviews and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            print(f"Scroll attempt {scroll_attempts}, collected {len(reviews)} reviews so far")

            self._driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", reviews_div
            )
            time.sleep(1)

            review_elements = self._driver.find_elements(By.CSS_SELECTOR, REVIEW_ELEMENT_CSS)
            more_descriptions = []
            for review_element in review_elements:
                if review_element not in seen_reviews:
                    seen_reviews.add(review_element)
                else:
                    continue

                try:
                    more_button = review_element.find_element(By.CSS_SELECTOR, MORE_BUTTON_CSS)
                    more_button.click()
                    description_container = review_element.find_element(
                        By.CSS_SELECTOR, MORE_DESCRIPTION_CSS
                    )
                    more_descriptions = description_container.find_elements(
                        By.CSS_SELECTOR, "div[jslog]"
                    )
                except:
                    pass

                try:
                    description = review_element.find_element(By.CSS_SELECTOR, DESCRIPTION_CSS)
                except:
                    print("DEBUG: No description found!")

                review = {}
                review["description"] = description.text

                for more_description in more_descriptions:
                    field = more_description.find_elements(By.CSS_SELECTOR, 'span[class="RfDO5c"]')
                    if len(field) == 1:
                        s = field[0].text.split(": ")
                        review[s[0]] = s[1]
                    elif len(field) == 2:
                        review[field[0].text] = field[1].text

                if review not in reviews:
                    reviews.append(review)

            new_height = self._driver.execute_script(
                "return arguments[0].scrollHeight", reviews_div
            )
            if new_height == last_height:
                print("DEBUG: Reached the bottom of reviews section or no new reviews loading")
                break
            last_height = new_height

        return reviews[:num_reviews]


class SaveReviews(AbstractTransaction):
    def do(self, reviews, directory, filename, **kwargs):
        os.makedirs(directory, exist_ok=True)
        with open(f"{directory}/{filename}.json", "w") as fd:
            json.dump(reviews, fd, indent=4)
            print(f"Reviews have been written to {directory}/{filename}")

        with open(f"{directory}/{directory}.txt", "a") as fd:
            fd.write(f"{filename}: {len(reviews)}\n")


class CloseDriver(AbstractTransaction):
    def do(self, **kwargs):
        print("Closing Chrome driver...")
        self._driver.quit()


# Main Script
if __name__ == "__main__":
    # Initialize Application
    app = Application(InitDriver().do())

    # Define locations
    richmond_hill = [
        {
            "filename": "11000_yonge_st",
            "url": "https://www.google.com/maps/place/Harvey's/@43.8955846,-79.443642,17z/data=!3m1!4b1!4m6!3m5!1s0x882b2a6bed191d91:0x4560094eb1e60b57!8m2!3d43.8955846!4d-79.443642!16s%2Fg%2F11b6gf67sk?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "13008_yonge_st",
            "url": "https://www.google.com/maps/place/Harvey's/@43.9447601,-79.4552696,17z/data=!3m1!4b1!4m6!3m5!1s0x882ad5cc19421439:0x90b5bd8165817a71!8m2!3d43.9447601!4d-79.4552696!16s%2Fg%2F1tfpvx66?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "8865_yonge_st",
            "url": "https://www.google.com/maps/place/Harvey's/@43.8435329,-79.4293226,17z/data=!3m1!4b1!4m6!3m5!1s0x882b2b782fb984c3:0xc4b3700a72067dbe!8m2!3d43.8435329!4d-79.4293226!16s%2Fg%2F1hc349nk3?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D",
        },
    ]
    markham = [
        {
            "filename": "5000_highway_7",
            "url": "https://www.google.com/maps/place/Harvey's/@43.870206,-79.2868826,17z/data=!3m1!4b1!4m6!3m5!1s0x405736d499f6d47f:0xe34d1d5701533cc!8m2!3d43.870206!4d-79.2868826!16s%2Fg%2F1pp2w_39b?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "725_markland_st",
            "url": "https://www.google.com/maps/place/Harvey's/@43.88563,-79.3732155,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d549c367d60f:0x6381385cc8608f7a!8m2!3d43.88563!4d-79.3732155!16s%2Fg%2F12xp_qnqj?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "7750_markham rd",
            "url": "https://www.google.com/maps/place/Harvey's/@43.8545928,-79.25854,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d6f80f59df57:0xa5961d3d5d49ca8a!8m2!3d43.854589!4d-79.2559597!16s%2Fg%2F1q2wfqn73?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "9275_highway_48",
            "url": "https://www.google.com/maps/place/Harvey's/@43.8939913,-79.2640625,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d620bc8a20b1:0xad1730b07aac8467!8m2!3d43.8939913!4d-79.2640625!16s%2Fg%2F11b5wl549q?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
    ]
    toronto = [
        {
            "filename": "2150_bloor_st_west",
            "url": "https://www.google.com/maps/place/Harvey's/@43.6518815,-79.4735839,17z/data=!3m1!4b1!4m6!3m5!1s0x882b3740f50d4f33:0x1904fd45494b5911!8m2!3d43.6518815!4d-79.4735839!16s%2Fg%2F11vlvrjp6j?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "1641_queens_st",
            "url": "https://www.google.com/maps/place/Harvey's/@43.6665177,-79.3150659,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4cb8b7d4b935f:0xb9d6089226abfe2!8m2!3d43.6665177!4d-79.3150659!16s%2Fg%2F1tgddd8f?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
        {
            "filename": "1_york_gate_blvd",
            "url": "https://www.google.com/maps/place/Harvey's/@43.7578548,-79.5202195,17z/data=!3m1!4b1!4m6!3m5!1s0x882b31d1355e11e1:0x26730b1a474ee3b7!8m2!3d43.7578548!4d-79.5202195!16s%2Fg%2F11qnl0x57s?entry=ttu&g_ep=EgoyMDI0MTIxMS.0IKXMDSoASAFQAw%3D%3D",
        },
    ]

    # Scrape reviews for each location
    for location in richmond_hill + markham + toronto:
        app.at(NavigateToRestaurant, url=location["url"])
        if app.at(ClickReviewsButton).result:
            reviews_div = app.at(WaitForReviewsSection).result
            if reviews_div:
                reviews = app.at(
                    ScrollAndCollectReviews, reviews_div=reviews_div, num_reviews=200
                ).result
                app.at(
                    SaveReviews, reviews=reviews, directory="reviews", filename=location["filename"]
                )

    # Close the driver
    app.at(CloseDriver)
