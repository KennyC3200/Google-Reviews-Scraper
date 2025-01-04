from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json


"""Setup Chrome driver with necessary options"""
def setup_driver():
    print("Setting up Chrome driver...")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Temporarily disable headless mode for debugging
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')  # Set a larger window size
    return webdriver.Chrome(options=options)


"""Scrape reviews from a Google Maps restaurant page"""
def get_reviews(restaurant_url, num_reviews=50):
    driver = setup_driver()
    reviews = []
    seen_reviews = set()
    
    try:
        print(f"Navigating to restaurant page: {restaurant_url}")
        driver.get(restaurant_url)
        
        # Wait longer for initial page load
        time.sleep(3)
        
        print("Looking for reviews button...")
        try:
            reviews_button = None
            try:
                reviews_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[jsaction*="reviewChart"]'))
                )
            except:
                print("ERROR: Could not locate reviews button")
                driver.save_screenshot("debug_screenshot.png")
                return reviews
            
            if reviews_button:
                print("Clicking reviews button")
                driver.execute_script("arguments[0].click();", reviews_button)
                
        except TimeoutException:
            print("ERROR: Couldn't find the reviews button. Taking screenshot for debugging")
            driver.save_screenshot("debug_screenshot.png")
            return reviews
        
        # Wait for reviews to load
        print("Waiting for reviews to load")
        time.sleep(3)
        
        try:
            reviews_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]'))
            )
            print("Reviews section found!")
        except TimeoutException:
            print("ERROR: Couldn't find the reviews section. Taking screenshot")
            driver.save_screenshot("debug_screenshot2.png")
            return reviews
        
        print(f"Starting to collect {num_reviews} reviews")
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
                    print('No "more" button!')

                # Primary description
                description = review_element.find_element(By.CSS_SELECTOR, 'span[class="wiI7pd"]')

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
                print("Reached the bottom of reviews section or no new reviews loading")
                break
            last_height = new_height
            
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        driver.save_screenshot("error_screenshot.png")
    
    finally:
        print("Closing Chromedriver")
        driver.quit()
    
    print(f"Successfully collected {len(reviews)} reviews!")
    return reviews[:num_reviews]


def print_reviews(reviews):
    with open('reviews.json', 'w') as fd:
        json.dump(reviews, fd, indent=4)
        print("Reviews have been written to reviews.json")


def main():
    restaurant_url = "https://www.google.com/maps/place/Harvey's/@43.8435329,-79.4318975,17z/data=!3m1!4b1!4m6!3m5!1s0x882b2b782fb984c3:0xc4b3700a72067dbe!8m2!3d43.8435329!4d-79.4293226!16s%2Fg%2F1hc349nk3?entry=ttu&g_ep=EgoyMDI0MTIxMS4wIKXMDSoASAFQAw%3D%3D"
    num_reviews = 20
    
    reviews = get_reviews(restaurant_url, num_reviews)
    print_reviews(reviews)


if __name__ == "__main__":
    main()