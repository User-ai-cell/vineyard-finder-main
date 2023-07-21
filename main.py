import overpass
import csv
import sys
import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

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

def check_bound_box(sBound, wBound, nBound, eBound):
    if not (-90 <= float(sBound) <= 90) & (-90 <= float(nBound) <= 90):
        raise InvalidCoordinateError("Longitude angle must be in [-90;90] range")
    if not (-180 <= float(wBound) <= 180) & (-180 <= float(eBound) <= 180):
        raise InvalidCoordinateError("Latitude angle must be in [-180;180] range")
    if not (float(nBound) >= float(sBound)) & (float(eBound) >= float(wBound)):
        raise InvalidBoundBoxError("Bound Box cannot be formed")

def check_coordinate_arguments(args):
    for arg in args[1:]:
        try:
            isinstance(float(arg), float)
        except ValueError:
            raise WrongArgTypeError("Coordinates must be either decimal or integer values")


def get_vineyard_coordinates(sBound, wBound, nBound, eBound):
    # create overpass API object
    api = overpass.API()
    # check query file presence
    if not (os.path.exists("query.overpass")):
        raise MissingFileError("query.overpass file is missing")

    # read query from file
    script_file = open("query.overpass", mode='r')
    # format bounds into query string
    query = script_file.read().format(sBound, wBound, nBound, eBound)

    script_file.close()
    # get response as csv object (a list of [lat,lon] rows with header row)
    print("Executing Overpass Query...")
    response = api.get(query, responseformat="csv(::lat,::lon)")
    # remove "empty" rows from the end of list
    while response[-1] == ['', '']:
        response.remove(['', ''])
    print(f"Response received, {len(response) - 1} vineyards found.")

    csv_file = open("vineyards_coordinates.csv", mode='w', newline='')
    # write list into csv file
    csv.writer(csv_file).writerows(response)
    csv_file.close()

    # delete header row from list
    response.pop(0)
    # return coordinate list
    return response

def install_webdriver(browser):
    if browser == 'Firefox':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    elif browser == 'Chrome':
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    else:
        raise UnknownBrowserError(f"Unknown browser: {browser}. Failed to install webdriver.")
    return driver

def get_vineyard_images(coordinatesList, browser):
    sleep_time = 1
    zoom_level = 18.0

    print("Launching webdriver...")
    # create driver object
    driver = install_webdriver(browser)

    print("Webdriver is working.")
    print("DO NOT CLOSE THE WINDOW. DO NOT MINIMISE THE WINDOW.")

    for item in coordinatesList:
        maps_url = f"https://www.bing.com/maps/?cp={item[0]}~{item[1]}&lvl={zoom_level}&style=a"
        driver.get(maps_url)

        # wait until map container is loaded
        mapContainer = WebDriverWait(driver, sleep_time).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "#overlayContainer"))
        )

        # collapse the annoying container
        driver.find_element(By.XPATH, "//*[@class='geochainActionButton geochainCollapse']").click()
        # take screenshot of map container
        mapContainer.screenshot(f"screenshots/{item[0]} {item[1]}.png")

        time.sleep(sleep_time)

    print("Webdriver shutting down...")
    driver.close()

def main(arguments):
    print("Vineyard finder script is running")
    sBound, wBound, nBound, eBound = arguments
    try:
        check_coordinate_arguments(arguments[0:4])
        check_bound_box(sBound, wBound, nBound, eBound)
    except Exception as exc:
        print('Error: ')
        print(str(exc))
        return -1
    print("Getting a list of vineyard coordinates.")
    coordinates_list = get_vineyard_coordinates(sBound, wBound, nBound, eBound)
    print("Getting satellite images of vineyards.")
    get_vineyard_images(coordinates_list, 'Firefox')
    return 0


if __name__ == '__main__':
    main(sys.argv[1:])
