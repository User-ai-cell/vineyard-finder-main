import overpass
import csv
import sys
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class InvalidBoundBoxError(Exception):
    pass


class InvalidCoordinateError(Exception):
    pass


class WrongArgTypeError(Exception):
    pass


class MissingFileError(Exception):
    pass


class UnknownBrowserError(Exception):
    pass


# check if the coordinates are correct
# and bound box can be formed
def check_bound_box(s_bound, w_bound, n_bound, e_bound):
    if not (-90 <= float(s_bound) <= 90) & (-90 <= float(n_bound) <= 90):
        raise InvalidCoordinateError("Longitude angle must be in [-90;90] range")
    if not (-180 <= float(w_bound) <= 180) & (-180 <= float(e_bound) <= 180):
        raise InvalidCoordinateError("Latitude angle must be in [-180;180] range")
    if not (float(n_bound) >= float(s_bound)) & (float(e_bound) >= float(w_bound)):
        raise InvalidBoundBoxError("Bound Box cannot be formed")


def check_coordinate_arguments(args):
    for arg in args[1:]:
        try:
            isinstance(float(arg), float)
        except ValueError:
            raise WrongArgTypeError("Coordinates must be either decimal or integer values")


def get_vineyard_coordinates(s_bound, w_bound, n_bound, e_bound):
    # create overpass API object
    api = overpass.API()
    # check query file presence
    if not (os.path.exists("query.overpass")):
        raise MissingFileError("query.overpass file is missing")

    # read query from file
    with open("query.overpass", mode='r') as script_file:
        # format bounds into query string
        query = script_file.read().format(s_bound, w_bound, n_bound, e_bound)

    script_file.close()
    # get response as .csv object
    # (a list of [lat,lon] rows with header row)
    print("Executing Overpass Query...")
    response = api.get(query, responseformat="csv(::lat,::lon)")
    # remove "empty" rows from the end of list
    while response[-1] == ['', '']:
        response.remove(['', ''])
    print(f"Response received, {len(response) - 1} vineyards found.")

    with open("vineyards_coordinates.csv", mode='w', newline='') \
    as csv_file:
        # write list into .csv file
        csv.writer(csv_file).writerows(response)

    # delete the header row from list
    response.pop(0)
    # return response as coordinate list
    return response


def install_webdriver(browser):
    if browser == 'Firefox':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    elif browser == 'Chrome':
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    else:
        raise UnknownBrowserError(f"Unknown browser: {browser}. Failed to install webdriver.")
    return driver


def get_vineyard_images(coordinates_list, browser):
    SLEEP_TIME = 5  # sec
    ZOOM_LEVEL = 18.0

    print("Launching webdriver...")
    # create driver object
    driver = install_webdriver(browser)

    print("Webdriver is working.")
    print("DO NOT CLOSE THE WINDOW. DO NOT MINIMISE THE WINDOW.")
    try:
        for item in coordinates_list:
            maps_url = f"https://www.bing.com/maps/?cp={item[0]}~{item[1]}&lvl={ZOOM_LEVEL}&style=a"
            driver.get(maps_url)

            # wait until map container is loaded
            map_container = WebDriverWait(driver, SLEEP_TIME).until(
                expected_conditions.presence_of_element_located\
                    ((By.CSS_SELECTOR, "#overlayContainer"))
            )

            # take screenshot of map container
            map_container.screenshot(f"screenshots/{item[0]} {item[1]}.png")

            # slight delay after each screenshot taken
            # (purely for visual satisfaction)
            driver.implicitly_wait(2)

    finally:
        print("Webdriver shutting down...")
        driver.close()


def main(args):
    print("Vineyard finder script is running")
    s_bound, w_bound, n_bound, e_bound = args[0:4]
    browser = args[4]
    try:
        check_coordinate_arguments(args[0:4])
        check_bound_box(s_bound, w_bound, n_bound, e_bound)
    except Exception as exc:
        print('Error: ' + str(exc))
        return -1
    print("Getting a list of vineyard coordinates.")
    coordinates_list = get_vineyard_coordinates(s_bound, w_bound, n_bound, e_bound)
    if len(coordinates_list) > 0:
        print("Getting satellite images of vineyards.")
        get_vineyard_images(coordinates_list, browser)
    return 0


if __name__ == '__main__':
    # pass the command line arguments (except the first one,
    # which is script name)
    main(sys.argv[1:])
