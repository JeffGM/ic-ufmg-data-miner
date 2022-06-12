import requests
import json
import os
from git import Repo, GitCommandError
from pathlib import Path
from datetime import datetime, timezone
from time import sleep
import GitRepositoryProvider
import re

class GitHubSourceCodeProvider(GitRepositoryProvider.GitRepositoryProvider):
    def __init__(self):
        self.url_user_profile = lambda username: "https://github.com/" + username
        self.local_temp_repo_files = "temp_repo_files/"
        self.path_to_save_github_stats = "github_info.json"
        self.url_github_api = "https://api.github.com"

        self.usernames_list = self.get_usernames_list()
        self.fetched_counter = 0
        self.already_fetched_users = []

        self.url_github_get_repositories_list = lambda username: self.url_github_api + "/users/" + username + "/repos"
        self.url_github_get_repository_download_link = lambda username, repo_name: \
            self.url_github_api + "/repos/" + username + "/" + repo_name + "/zipball"
        self.user_local_path = lambda username: self.local_temp_repo_files + username
        self.repository_local_path = lambda username, repo_name: self.user_local_path(username) + "/" + repo_name
        self.csv_report_local_path = lambda username: self.user_local_path(username) + "/" + username + ".csv"

    def process(self):
        self.initGithubInformationJSONFile()

        with open(self.path_to_save_github_stats) as file:
            profile_contents = json.loads(file.read())
            if len(profile_contents) > 0:
                already_fetched_users = profile_contents.keys()

        for current_username in self.usernames_list:
            if current_username in already_fetched_users:
                continue

            parsed_repos_list = self.get_repos_list(current_username)

            for repo in parsed_repos_list:
                self.get_git_repository(repo, current_username)


    def get_usernames_list(self):
        profiles_list = json.loads(open("individual_developers_info.json", 'r').read())
        username_list = []
        for profile in profiles_list:
            partially_parsed_profile = profile['githubURL'].replace("github.com/", '')
            username_list.append(re.sub("[^0-9a-zA-Z]", '', partially_parsed_profile))

        return username_list

    def get_repos_list(self, current_username):
        repos_list = requests.get(self.url_github_get_repositories_list(current_username), headers={'User-Agent': 'request'})

        if repos_list.status_code != 200:
            self.wait_until_rate_limit_returns()
            return self.get_repos_list(current_username)

        return json.loads(repos_list.text)


    def wait_until_rate_limit_returns(self):
        rate_limit_request = requests.get(self.url_github_api + "/rate_limit", headers={'User-Agent': 'request'})
        rate_limit = json.loads(rate_limit_request.text)

        if rate_limit["resources"]["core"]["remaining"] == 0:
            print("Rate limit exceeded")
            timestamp = int(rate_limit["resources"]["core"]["reset"])
            print("The process will halt until " + datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') + " and try again.")
            self.wait_until_timestamp(timestamp)
        else:
            raise Exception("Unknown error in requesting repos list")

    def wait_until_timestamp(self,timestamp):
        time_now = datetime.now().timestamp()

        while timestamp > time_now:
            sleep(60)
            time_now = datetime.now().timestamp()

        return

    def get_git_repository(self,repo, current_username):
        local_repository_path = self.repository_local_path(current_username, repo['name'])

        Path(local_repository_path).mkdir(parents=True, exist_ok=True)

        if len(os.listdir(local_repository_path)) == 0:
            try:
                Repo.clone_from(repo['clone_url'], local_repository_path)
            except GitCommandError:
                print("Guessing that git repo " + repo['name'] + " is probably already cloned, proceding...")

        return local_repository_path

    def initGithubInformationJSONFile(self):
        if not os.path.exists(self.path_to_save_github_stats):
            with open(self.path_to_save_github_stats, mode='w', encoding='utf-8') as file:
                json.dump([], file)

