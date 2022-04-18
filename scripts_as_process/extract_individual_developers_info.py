import pandas as pd
import time
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

path_to_save_scraped_profiles = "individual_developers_info.json"
workana_freelancers_profile_url_file = "developers_pages_url.txt"

def launchBrowser():
    chrome_options = Options()
    path_to_chrome_driver = '/Users/jefferson.lopes/chromedriver'
    driver = webdriver.Chrome(path_to_chrome_driver, options=chrome_options)
    driver.maximize_window()
    return driver


def readListFromFile(filename):
    file = open(filename, "r")
    file_lines = file.read()

    return file_lines.split('\n')


def removeFeatureWorkersSection(driver):
    driver.execute_script("""
    var element = document.querySelector("#featured-workers");
    if (element)
        element.parentNode.removeChild(element);
    """)


def openSkillsSection(driver):
    try:
        skills_collapse_button = driver.find_element("link text", "Ver mais habilidades")
        skills_collapse_button.click()
    except:
        pass


def openDetailsSections(driver):
    try:
        details_collapse_buttons = driver.find_elements("link text", "Ver mais detalhes")

        for collapse_button in details_collapse_buttons:
            collapse_button.click()
    except:
        pass


def getGitHubLinkFromPage(html_page):
    pattern = "(github.com\/[^(\s|\/)]+)"
    match = re.search(pattern, html_page)

    if match:
        match = match.groups()[0]
        return replaceListForACharacterInString(["(", ")", "|"], "", match)

    return ""


def replaceListForACharacterInString(list, character, string):
    new_string = string
    for replaced in list:
        new_string = new_string.replace(replaced, character)

    return new_string


def getSkillsAsArrayFromPage(html_page):
    skills_section = BeautifulSoup(html_page)
    table = skills_section.find_all('table')

    return pd.read_html(str(table))[0] if table else ""


def initProfileInformationJSONFile():
    global path_to_save_scraped_profiles

    with open(path_to_save_scraped_profiles, mode='w', encoding='utf-8') as file:
        json.dump([], file)


def saveProfileInformationAsJSON(profileName, role, workanaURL, githubURL, skills):
    global path_to_save_scraped_profiles

    profile_contents = ""
    skills_as_dict = json.loads(skills.to_json())
    parsed_skills_as_dict = removeDictKeyElementThatContains("Unnamed", skills_as_dict)
    entry = {"name": profileName, "role": role, "workanaURL": workanaURL, "githubURL": githubURL, "skills": parsed_skills_as_dict}

    with open(path_to_save_scraped_profiles) as file:
        profile_contents = json.load(file)

    profile_contents.append(entry)
    with open(path_to_save_scraped_profiles, mode='w') as f:
        f.write(json.dumps(profile_contents, indent=2))


def removeDictKeyElementThatContains(string, object_dict):
    for key in list(object_dict.keys()):
        if string in key:
            del object_dict[key]

    return object_dict

def closePopups(driver):
    close_popup_cookies_button = driver.find_element("id", "onetrust-accept-btn-handler")
    driver.execute_script("arguments[0].click();", close_popup_cookies_button)
    close_popup_button = driver.find_element("class name", "close")
    close_popup_button.click()

def get_data_from_freelancers_urls(driver, url_list):
    first_opening = True

    for freelancer_url in url_list:
        driver.get(freelancer_url)

        if first_opening:
            closePopups(driver)
            first_opening = False

        removeFeatureWorkersSection(driver)
        openSkillsSection(driver)
        openDetailsSections(driver)

        time.sleep(5)

        profile_name = driver.find_element_by_xpath('//div[@itemprop="name"]//span')
        skills_section = driver.find_element("id", "section-skills")
        skills_html_representation = skills_section.get_attribute("innerHTML")

        profile_role = driver.find_element("class name", "profile-role").find_element("tag name", "span")
        profile_role_as_text = profile_role.text

        github_link = getGitHubLinkFromPage(driver.page_source)
        skills = getSkillsAsArrayFromPage(skills_html_representation)

        profile_name_as_text = profile_name.text

        saveProfileInformationAsJSON(profile_name_as_text, profile_role_as_text, freelancer_url, github_link, skills)


def main():
    #initProfileInformationJSONFile()
    driver = launchBrowser()
    freelancers_url_list = readListFromFile(workana_freelancers_profile_url_file)
    get_data_from_freelancers_urls(driver, freelancers_url_list)


if __name__ == "__main__":
    main()
