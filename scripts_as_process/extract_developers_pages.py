import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

url = "https://www.workana.com/pt/freelancers?query=%22github.com%2F%22&page="
current_page = 0
max_pages = 14
workana_freelancers_profile_url_file = "developers_pages_url.txt"

def getCurrentURL():
    global current_page
    global url
    current_page += 1

    return url + str(current_page)


def launchBrowser():
    chrome_options = Options()
    path_to_chrome_driver = '/Users/jefferson.lopes/chromedriver'
    driver = webdriver.Chrome(path_to_chrome_driver, options=chrome_options)
    driver.get(getCurrentURL())
    driver.maximize_window()
    return driver


def getListWithFreelancersProfileURLs(driver):
    workana_freelancers_url = []

    for page in range(current_page, max_pages):
        time.sleep(3)

        user_names = driver.find_elements("class name", "user-name")
        for user_name in user_names:
            html_representation = user_name.get_attribute("innerHTML")
            soup = BeautifulSoup(html_representation, "html.parser")
            a_tag = soup.select_one("a")
            workana_freelancers_url.append(a_tag.get("href"))

        driver.get(getCurrentURL())

    return workana_freelancers_url


def writeListToFile(list, filename):
    with open(filename, "w") as file:
        file_lines = '\n'.join(list)
        file.write(file_lines)


def main():
    driver = launchBrowser()

    workana_freelancers_url = getListWithFreelancersProfileURLs(driver)
    writeListToFile(workana_freelancers_url, workana_freelancers_profile_url_file)


if __name__ == "__main__":
    main()
