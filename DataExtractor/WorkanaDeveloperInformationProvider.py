import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import pandas as pd
import json
import DeveloperInformationProvider

class WorkanaDeveloperInformationProvider(DeveloperInformationProvider.DeveloperInformationProvider):
    def __init__(self):
        self.url = "https://www.workana.com/pt/freelancers?query=%22github.com%2F%22&page="
        self.current_page = 0
        self.max_pages = 14
        self.workana_freelancers_profile_url_file = "developers_pages_url.txt"
        path_to_save_scraped_profiles = "individual_developers_info.json"

    def process(self):
        driver = self.launchBrowser()
        workana_freelancers_url = self.getListWithFreelancersProfileURLs(driver)
        self.writeListToFile(workana_freelancers_url, self.workana_freelancers_profile_url_file)
        freelancers_url_list = self.readListFromFile(self.workana_freelancers_profile_url_file)
        self.get_data_from_freelancers_urls(driver, freelancers_url_list)

    def getCurrentURL(self):
        global current_page
        global url
        current_page += 1

        return url + str(current_page)

    def launchBrowser(self):
        chrome_options = Options()
        path_to_chrome_driver = '/Users/path-to-chromedriver/chromedriver'
        driver = webdriver.Chrome(path_to_chrome_driver, options=chrome_options)
        driver.get(self.getCurrentURL())
        driver.maximize_window()
        return driver

    def getListWithFreelancersProfileURLs(self, driver):
        workana_freelancers_url = []

        for page in range(current_page, self.max_pages):
            time.sleep(3)

            user_names = driver.find_elements("class name", "user-name")
            for user_name in user_names:
                html_representation = user_name.get_attribute("innerHTML")
                soup = BeautifulSoup(html_representation, "html.parser")
                a_tag = soup.select_one("a")
                workana_freelancers_url.append(a_tag.get("href"))

            driver.get(self.getCurrentURL())

        return workana_freelancers_url

    def writeListToFile(self, list, filename):
        with open(filename, "w") as file:
            file_lines = '\n'.join(list)
            file.write(file_lines)

    def readListFromFile(self, filename):
        file = open(filename, "r")
        file_lines = file.read()

        return file_lines.split('\n')

    def removeFeatureWorkersSection(self,driver):
        driver.execute_script("""
        var element = document.querySelector("#featured-workers");
        if (element)
            element.parentNode.removeChild(element);
        """)

    def openSkillsSection(self,driver):
        try:
            skills_collapse_button = driver.find_element("link text", "Ver mais habilidades")
            skills_collapse_button.click()
        except:
            pass

    def openDetailsSections(self,driver):
        try:
            details_collapse_buttons = driver.find_elements("link text", "Ver mais detalhes")

            for collapse_button in details_collapse_buttons:
                collapse_button.click()
        except:
            pass

    def getGitHubLinkFromPage(self, html_page):
        pattern = "(github.com\/[^(\s|\/)]+)"
        match = re.search(pattern, html_page)

        if match:
            match = match.groups()[0]
            return self.replaceListForACharacterInString(["(", ")", "|"], "", match)

        return ""

    def replaceListForACharacterInString(self, list, character, string):
        new_string = string
        for replaced in list:
            new_string = new_string.replace(replaced, character)

        return new_string

    def getSkillsAsArrayFromPage(self, html_page):
        skills_section = BeautifulSoup(html_page)
        table = skills_section.find_all('table')

        return pd.read_html(str(table))[0] if table else ""

    def initProfileInformationJSONFile(self):
        with open(self.path_to_save_scraped_profiles, mode='w', encoding='utf-8') as file:
            json.dump([], file)

    def saveProfileInformationAsJSON(self, profileName, role, workanaURL, githubURL, skills):
        profile_contents = ""
        skills_as_dict = json.loads(skills.to_json())
        parsed_skills_as_dict = self.removeDictKeyElementThatContains("Unnamed", skills_as_dict)
        entry = {"name": profileName, "role": role, "workanaURL": workanaURL, "githubURL": githubURL,
                 "skills": parsed_skills_as_dict}

        with open(self.path_to_save_scraped_profiles) as file:
            profile_contents = json.load(file)

        profile_contents.append(entry)
        with open(self.path_to_save_scraped_profiles, mode='w') as f:
            f.write(json.dumps(profile_contents, indent=2))

    def removeDictKeyElementThatContains(self, string, object_dict):
        for key in list(object_dict.keys()):
            if string in key:
                del object_dict[key]

        return object_dict

    def closePopups(self, driver):
        close_popup_cookies_button = driver.find_element("id", "onetrust-accept-btn-handler")
        driver.execute_script("arguments[0].click();", close_popup_cookies_button)
        close_popup_button = driver.find_element("class name", "close")
        close_popup_button.click()

    def get_data_from_freelancers_urls(self, driver, url_list):
        first_opening = True

        for freelancer_url in url_list:
            driver.get(freelancer_url)

            if first_opening:
                self.closePopups(driver)
                first_opening = False

            self.removeFeatureWorkersSection(driver)
            self.openSkillsSection(driver)
            self.openDetailsSections(driver)

            time.sleep(5)

            profile_name = driver.find_element_by_xpath('//div[@itemprop="name"]//span')
            skills_section = driver.find_element("id", "section-skills")
            skills_html_representation = skills_section.get_attribute("innerHTML")

            profile_role = driver.find_element("class name", "profile-role").find_element("tag name", "span")
            profile_role_as_text = profile_role.text

            github_link = self.getGitHubLinkFromPage(driver.page_source)
            skills = self.getSkillsAsArrayFromPage(skills_html_representation)

            profile_name_as_text = profile_name.text

            self.saveProfileInformationAsJSON(profile_name_as_text, profile_role_as_text, freelancer_url, github_link,
                                         skills)
