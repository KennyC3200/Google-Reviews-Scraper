from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
import ollama
from ollama import ChatResponse


def init_driver():
    """Init the Chromedriver"""

    print("Setting up Chrome driver...")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)


# Scrape reviews, given a url
# Max number of reviews is default to 50
def get_reviews(driver, restaurant_url, num_reviews=50):
    """Scrape reviews

    Keyword arguments:
    driver -- Chromedriver object
    restaurant_url -- url to the restaurant
    num_reviews -- maximum number of reviews (default 50)
    """

    reviews = []
    seen_reviews = set()

    try:
        print(f"Navigating to restaurant page: {restaurant_url}")
        driver.get(restaurant_url)

        # Wait for page to load
        time.sleep(3)

        print("DEBUG: Looking for reviews button")
        try:
            reviews_button = None
            try:
                reviews_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[jsaction*="reviewChart"]')))
            except:
                print("ERROR: Could not locate reviews button")
                driver.save_screenshot("debug_screenshot.png")
                return reviews

            if reviews_button:
                print("DEBUG: Clicking reviews button")
                driver.execute_script("arguments[0].click();", reviews_button)

        except TimeoutException:
            print("ERROR: Couldn't find the reviews button. Taking screenshot for debugging")
            driver.save_screenshot("debug_screenshot.png")
            return reviews

        # Wait for reviews to load
        print("DEBUG: Waiting for reviews to load")
        time.sleep(3)

        try:
            reviews_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]')))
            print("DEBUG: Reviews section found!")
        except TimeoutException:
            print("ERROR: Couldn't find the reviews section. Taking screenshot")
            driver.save_screenshot("debug_screenshot2.png")
            return reviews

        print(f"DEBUG: Starting to collect {num_reviews} reviews")
        last_height = driver.execute_script("return arguments[0].scrollHeight", reviews_div)

        # Maximum number of scrolls to reach the bottom
        scroll_attempts = 0
        max_scroll_attempts = 30

        while len(reviews) < num_reviews and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            print(f"Scroll attempt {scroll_attempts}, collected {len(reviews)} reviews so far")

            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', reviews_div)
            time.sleep(1)

            review_elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="jftiEf fontBodyMedium "]')

            for review_element in review_elements:
                if review_element not in seen_reviews:
                    seen_reviews.add(review_element)
                else:
                    continue

                # Click the more button
                try:
                    more_button = review_element.find_element(By.CSS_SELECTOR, 'button[class="w8nwRe kyuRq"]')

                    more_button.click()

                    description_container = review_element.find_element(By.CSS_SELECTOR, 'div[jslog="127691"]')
                    # description_container = review.find_element(By.CSS_SELECTOR, 'div > div') # This one works too

                    more_descriptions = description_container.find_elements(By.CSS_SELECTOR, 'div[jslog]')
                except:
                    pass

                # Primary description
                try:
                    description = review_element.find_element(By.CSS_SELECTOR, 'span[class="wiI7pd"]')
                except:
                    print("DEBUG: No description found!")

                # Append the descriptions
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

            new_height = driver.execute_script("return arguments[0].scrollHeight", reviews_div)
            if new_height == last_height:
                print("DEBUG: Reached the bottom of reviews section or no new reviews loading")
                break
            last_height = new_height

    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        driver.save_screenshot("error_screenshot.png")

    finally:
        print(f"DEBUG: Successfully scraped {restaurant_url}")

    print(f"DEBUG: Successfully collected {len(reviews)} reviews!")
    return reviews[:num_reviews]


def print_reviews(reviews, directory, filename):
    """Print out the reviews into a JSON file

    Keyword arguments:
    reviews -- reviews passed in as an array
    directory -- directory to store the reviews in
    filename -- filename to store the reviews in
    """

    os.makedirs(directory, exist_ok=True) # Ensure the directory exists
    with open(f'{directory}/{filename}.json', 'w') as fd:
        json.dump(reviews, fd, indent=4)
        print(f'Reviews have been written to {directory}/{filename}')

    with open(f'{directory}/{directory}.txt', 'a') as fd:
        fd.write(f'{filename}: {len(reviews)}\n')


def scrape_locations(driver, city, locations):
    """Scrape the locations

    Keyword arguments:
    driver -- Chromedriver object
    city -- city that the restaurants are in
    locations -- locations, passed in as an array
    """

    for location in locations:
        reviews = get_reviews(driver, location["url"], 200)
        print_reviews(reviews, city, location["filename"])


def main():
    driver = init_driver()

    richmond_hill = [
        {"filename": "11000_yonge_st", "url": "https://www.google.com/maps/place/Harvey's/@43.8955846,-79.443642,17z/data=!3m1!4b1!4m6!3m5!1s0x882b2a6bed191d91:0x4560094eb1e60b57!8m2!3d43.8955846!4d-79.443642!16s%2Fg%2F11b6gf67sk?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "13008_yonge_st", "url": "https://www.google.com/maps/place/Harvey's/@43.9447601,-79.4552696,17z/data=!3m1!4b1!4m6!3m5!1s0x882ad5cc19421439:0x90b5bd8165817a71!8m2!3d43.9447601!4d-79.4552696!16s%2Fg%2F1tfpvx66?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "8865_yonge_st", "url": "https://www.google.com/maps/place/Harvey's/@43.8435329,-79.4293226,17z/data=!3m1!4b1!4m6!3m5!1s0x882b2b782fb984c3:0xc4b3700a72067dbe!8m2!3d43.8435329!4d-79.4293226!16s%2Fg%2F1hc349nk3?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"}
    ]
    markham = [
        {"filename": "5000_highway_7", "url": "https://www.google.com/maps/place/Harvey's/@43.870206,-79.2868826,17z/data=!3m1!4b1!4m6!3m5!1s0x405736d499f6d47f:0xe34d1d5701533cc!8m2!3d43.870206!4d-79.2868826!16s%2Fg%2F1pp2w_39b?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "725_markland_st", "url": "https://www.google.com/maps/place/Harvey's/@43.88563,-79.3732155,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d549c367d60f:0x6381385cc8608f7a!8m2!3d43.88563!4d-79.3732155!16s%2Fg%2F12xp_qnqj?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "7750_markham rd", "url": "https://www.google.com/maps/place/Harvey's/@43.8545928,-79.25854,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d6f80f59df57:0xa5961d3d5d49ca8a!8m2!3d43.854589!4d-79.2559597!16s%2Fg%2F1q2wfqn73?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "9275_highway_48", "url": "https://www.google.com/maps/place/Harvey's/@43.8939913,-79.2640625,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4d620bc8a20b1:0xad1730b07aac8467!8m2!3d43.8939913!4d-79.2640625!16s%2Fg%2F11b5wl549q?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"}
    ]
    toronto = [
        {"filename": "2150_bloor_st_west", "url": "https://www.google.com/maps/place/Harvey's/@43.6518815,-79.4735839,17z/data=!3m1!4b1!4m6!3m5!1s0x882b3740f50d4f33:0x1904fd45494b5911!8m2!3d43.6518815!4d-79.4735839!16s%2Fg%2F11vlvrjp6j?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "1641_queens_st", "url": "https://www.google.com/maps/place/Harvey's/@43.6665177,-79.3150659,17z/data=!3m1!4b1!4m6!3m5!1s0x89d4cb8b7d4b935f:0xb9d6089226abfe2!8m2!3d43.6665177!4d-79.3150659!16s%2Fg%2F1tgddd8f?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"},
        {"filename": "1_york_gate_blvd", "url": "https://www.google.com/maps/place/Harvey's/@43.7578548,-79.5202195,17z/data=!3m1!4b1!4m6!3m5!1s0x882b31d1355e11e1:0x26730b1a474ee3b7!8m2!3d43.7578548!4d-79.5202195!16s%2Fg%2F11qnl0x57s?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"}
    ]

    scrape_locations(driver, "richmond_hill", richmond_hill)
    scrape_locations(driver, "markham", markham)
    scrape_locations(driver, "toronto", toronto)

    # driver.quit()

    # Print out AI response for a restaurant
    # print("The AI is thinking...")
    # response: ChatResponse = ollama.chat(model='deepseek-r1:1.5b', messages=[
    #     {
    #         'role': 'user',
    #         'content': "Given the JSON for the Google reviews of a Harvey's restaurant, provide feedback on what is good about the restaurant and areas for improvement:\n" + open("toronto/1_york_gate_blvd.json", "r").read(),
    #     },
    # ])
    # print(response.message.content)


if __name__ == "__main__":
    main()
