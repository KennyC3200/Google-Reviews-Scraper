from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ollama import ChatResponse
from ramsay_debug import *
from ramsay_restaurant import *
import time
import os
import json
import ollama


# Constants
PAGE_WAIT_TIME = int(os.getenv("PAGE_WAIT_TIME", 3))
FIND_ELEMENT_DEFAULT_PARAMS = {
    "timeout": 0,
    "exit_on_fail": False,
    "show_debug": False,
    "by": By.CSS_SELECTOR
}


def ramsay_init_driver() -> WebDriver:
    """Init the web driver.
    Returns a chrome webdriver class
    """
    ramsay_print_debug("Initializing chrome driver")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def ramsay_quit_driver(driver: WebDriver):
    ramsay_print_debug("Quitting the web driver")
    driver.quit()


def ramsay_find_element(driver: WebDriver, tag: str, **params) -> WebElement | None:
    params = {**FIND_ELEMENT_DEFAULT_PARAMS, **params}
    element = None
    try:
        if params["timeout"] == 0:
            element = driver.find_element(params["by"], tag)
        else:
            element = WebDriverWait(driver, params["timeout"]).until(
                expected_conditions.presence_of_element_located((params["by"], tag)))
    except TimeoutException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_element | Locating element timeout: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_element")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_element | Locating element timeout: {tag}")
    except NoSuchElementException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_element | Could not locate element: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_element")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_element | Could not locate element: {tag}")
    return element


def ramsay_find_elements(driver: WebDriver, tag: str, **params) -> list[WebElement]:
    params = {**FIND_ELEMENT_DEFAULT_PARAMS, **params}
    elements: list[WebElement] = []
    try:
        if params["timeout"] == 0:
            elements = driver.find_elements(params["by"], tag)
        else:
            elements = WebDriverWait(driver, params["timeout"]).until(
                expected_conditions.presence_of_all_elements_located((params["by"], tag)))
    except TimeoutException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_elements | Locating elements timeout: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_elements")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_elements | Locating elements timeout: {tag}")
    except NoSuchElementException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_elements | Could not locate elements: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_elements")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_elements | Could not locate elements: {tag}")
    return elements


def ramsay_find_element_by_element(driver: WebDriver, element: WebElement, tag: str, **params) -> WebElement | None:
    params = {**FIND_ELEMENT_DEFAULT_PARAMS, **params}
    _element = None
    try:
        _element = element.find_element(params["by"], tag)
    except NoSuchElementException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_element_by_element | Could not locate element: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_element_by_element")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_elemnet_by_element | Could not locate element: {tag}")
    return _element


def ramsay_find_elements_by_element(driver: WebDriver, element: WebElement, tag: str, **params) -> list[WebElement]:
    params = {**FIND_ELEMENT_DEFAULT_PARAMS, **params}
    elements: list[WebElement] = []
    try:
        elements = element.find_elements(params["by"], tag)
    except NoSuchElementException:
        if params["exit_on_fail"]:
            ramsay_print_error(f"ramsay_find_elements_by_element | Could not locate elements: {tag}")
            ramsay_screenshot_error(driver, "ramsay_find_elements_by_element")
            exit(1)
        if params["show_debug"]:
            ramsay_print_debug(f"ramsay_find_elements_by_element | Could not locate element: {tag}")
    return elements


def ramsay_scrape_restaurant(driver: WebDriver, restaurant: RamsayRestaurant, max_reviews: int=50):
    try:
        ramsay_print_debug(
            "Navigating to restaurant | "
            f"restaurant: {restaurant.name} | "
            f"url: {ramsay_shorten_str(restaurant.url)}")
        driver.get(restaurant.url)

        # Allow the page to load
        time.sleep(PAGE_WAIT_TIME)

        ramsay_print_debug("Locating reviews button")
        reviews_button = ramsay_find_element(
            driver, 
            "button[jsaction*=\"reviewChart\"]",
            **{"exit_on_fail": True})
        ramsay_print_debug("Located reviews button")

        driver.execute_script("arguments[0].click()", reviews_button)
        ramsay_print_debug("Clicked reviews button")

        # Allow reviews to load
        ramsay_print_debug("Waiting for reviews to load")
        time.sleep(PAGE_WAIT_TIME)

        reviews_div = ramsay_find_element(
            driver, 
            "div[class=\"m6QErb DxyBCb kA9KIf dS8AEf XiKgde \"]", 
            **{"exit_on_fail": True})
        ramsay_print_debug("Located reviews div")
        
        # Scrape reviews
        ramsay_print_debug(f"Beginning to collect {max_reviews} reviews")
        prev_height = driver.execute_script("return arguments[0].scrollHeight", reviews_div)

        # Max number of scrolls to reach the bottom
        scrolls = 0
        max_scrolls = 30

        # Scroll all the way to reach the bottom then scrape the reviews
        while len(restaurant.reviews) < max_reviews and scrolls < max_scrolls:
            scrolls += 1
            ramsay_print_debug(f"Scrolled {scrolls} times")

            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviews_div)
            time.sleep(1)

            curr_height = driver.execute_script("return arguments[0].scrollHeight", reviews_div)
            if curr_height == prev_height:
                ramsay_print_debug("Reached bottom of reviews section")
                break
            prev_height = curr_height

        # Scrape the reviews
        ramsay_print_debug("Beginning to scrape the reviews")
        review_elements = ramsay_find_elements(driver, "div[class=\"jftiEf fontBodyMedium \"]")
        for review_element in review_elements:
            more_button = ramsay_find_element(driver, "button[class=\"w8nwRe kyuRq\"]")
            if more_button:
                more_button.click()

            desc_container = ramsay_find_element_by_element(driver, review_element, "div[jslog=\"127691\"]")
            if desc_container:
                # Locate additional fields in the description (e.g Food: 5 and Atmosphere: 2)
                desc_fields = ramsay_find_elements_by_element(driver, desc_container, "div[jslog]")
            desc = ramsay_find_element_by_element(driver, review_element, "span[class=\"wiI7pd\"]")

            # Create the review
            review = RamsayReview()
            if desc:
                review.add_desc(desc.text)
            for desc_field in desc_fields:
                field = ramsay_find_elements_by_element(driver, desc_field, "span[class=\"RfDO5c\"]")
                if field:
                    if len(field) == 1:
                        s = field[0].text.split(": ")
                        title = s[0]
                        rating = int(s[1])
                        review.add_rating(title, rating)
                    elif len(field) == 2:
                        title = field[0].text
                        rating_desc = field[1].text
                        review.add_rating_by_desc(title, rating_desc)
            restaurant.add_review(review)
    except Exception as e:
        ramsay_print_error(f"ramsay_scrape_restaurant | Unexpected error: {str(e)}")
        ramsay_screenshot_error(driver, "ramsay_scrape_restaurant")
    finally:
        ramsay_print_debug(f"Collected {len(restaurant.reviews)} reviews")
    ramsay_print_valid(f"Successfully scraped {str(restaurant)}")


def main():
    driver = ramsay_init_driver()

    restaurant = RamsayRestaurant("Longing Fusion Cuisine", "https://www.google.com/maps?sca_esv=338e44cf9c71f0ac&output=search&q=markham+longing+fusion+cuisine&source=lnms&fbs=ABzOT_CWdhQLP1FcmU5B0fn3xuWpA-dk4wpBWOGsoR7DG5zJBv10Kbgy3ptSBM6mMfaz8zD9rbDafxurA2LWQsFsMg4xyw0wcZEfh0F_bSugtfTXcZDlIRGobOM82WNCfxsPUBtuKvdzDM77ZM5aoZ5QE_xqOGiJ4VbI28fUJGueFoKtUJUuWV5PbN2_6qQaRUynPA3fSAvE8zCWmWqH3jLtfC1UuNmmfQ&entry=mc&ved=1t:200715&ictx=111")

    ramsay_scrape_restaurant(driver, restaurant)

    ramsay_quit_driver(driver)


if __name__ == "__main__":
    main()
