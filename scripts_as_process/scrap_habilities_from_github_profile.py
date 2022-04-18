import requests
import json
import os
from git import Repo, GitCommandError
from pathlib import Path
import shlex
import subprocess as sp
import io
import pandas as pd
from pandas import read_csv
import re
import shutil
from datetime import datetime, timezone
from time import sleep


url_user_profile = lambda username: "https://github.com/" + username
local_temp_repo_files = "temp_repo_files/"
path_to_save_github_stats = "scripts_as_process/github_info.json"
url_github_api = "https://api.github.com"

url_github_get_repositories_list = lambda username: url_github_api + "/users/" + username + "/repos"
url_github_get_repository_download_link = lambda username, repo_name: \
    url_github_api + "/repos/" + username + "/" + repo_name + "/zipball"
user_local_path = lambda username: local_temp_repo_files + username
repository_local_path = lambda username, repo_name: user_local_path(username) + "/" + repo_name
csv_report_local_path = lambda username: user_local_path(username) + "/" + username + ".csv"

def get_repos_list(current_username):
    repos_list = requests.get(url_github_get_repositories_list(current_username), headers={'User-Agent': 'request'})

    if repos_list.status_code != 200:
        wait_until_rate_limit_returns()
        return get_repos_list(current_username)

    return json.loads(repos_list.text)


def wait_until_rate_limit_returns():
    rate_limit_request = requests.get(url_github_api + "/rate_limit", headers={'User-Agent': 'request'})
    rate_limit = json.loads(rate_limit_request.text)

    if rate_limit["resources"]["core"]["remaining"] == 0:
        print("Rate limit exceeded")
        timestamp = int(rate_limit["resources"]["core"]["reset"])
        print("The process will halt until " + datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') + " and try again.")
        wait_until_timestamp(timestamp)
    else:
        raise Exception("Unknown error in requesting repos list")

def wait_until_timestamp(timestamp):
    time_now = datetime.now().timestamp()

    while timestamp > time_now:
        sleep(60)
        time_now = datetime.now().timestamp()

    return

def process_dataframe_to_final_format(user_raw_statistics_dataframe):
    partial_dataframe_with_file_extensions = filter_filenames_to_file_extensions(user_raw_statistics_dataframe)
    partial_dataframe = insert_loc_in_dataframe(partial_dataframe_with_file_extensions)
    partial_dataframe = aggregate_by_loc(partial_dataframe)
    partial_dataframe = sort_values_by_loc(partial_dataframe)
    partial_dataframe = filter_invalid_filetypes(partial_dataframe)
    partial_dataframe = filter_null_rows(partial_dataframe)
    partial_dataframe = aggregate_by_commits_count(partial_dataframe, partial_dataframe_with_file_extensions)

    return partial_dataframe


def filter_invalid_filetypes(user_statistics_dataframe):
    invalid_filetypes_list = ["txt", "sqlite3", "pdf", "LICENSE", "csv", "txt", "jpg", "png", "md", "gitignore", "htaccess", "/", "woff", "svg", "zip", "json", "gif"]
    for invalid_type in invalid_filetypes_list:
        user_statistics_dataframe = user_statistics_dataframe[
            ~user_statistics_dataframe.path.str.contains(invalid_type)]

    return user_statistics_dataframe

def filter_null_rows(user_statistics_dataframe):
    return user_statistics_dataframe[~(user_statistics_dataframe["loc"] == 0)]

def sort_values_by_loc(user_statistics_dataframe):
    user_statistics_dataframe.sort_values(by=['loc'], ascending=False).head()
    return user_statistics_dataframe


def aggregate_by_loc(user_statistics_dataframe):
    user_statistics_dataframe = user_statistics_dataframe.groupby(['path'])['loc'].agg('sum')

    user_statistics_dataframe = user_statistics_dataframe.reset_index()
    user_statistics_dataframe.head()
    return user_statistics_dataframe

def aggregate_by_commits_count(user_statistics_dataframe, partial_dataframe_with_file_extensions):
    user_statistics_dataframe['commits_count'] = 0
    commits_count_dataframe = partial_dataframe_with_file_extensions.drop_duplicates(['path', 'commit'], keep='first')
    commits_count_dataframe = commits_count_dataframe['path'].value_counts()
    for language in user_statistics_dataframe['path']:
        user_statistics_dataframe.loc[user_statistics_dataframe['path'] == language, 'commits_count'] = commits_count_dataframe[language]

    return user_statistics_dataframe


def insert_loc_in_dataframe(user_statistics_dataframe):
    user_statistics_dataframe = user_statistics_dataframe.replace({'-': 0})

    user_statistics_dataframe['deletions'] = user_statistics_dataframe['deletions'].astype(float)
    user_statistics_dataframe['additions'] = user_statistics_dataframe['additions'].astype(float)

    user_statistics_dataframe['deletions'] = user_statistics_dataframe['deletions'].astype(int)
    user_statistics_dataframe['additions'] = user_statistics_dataframe['additions'].astype(int)

    user_statistics_dataframe['loc'] = user_statistics_dataframe.apply(lambda x: x['additions'] + x['deletions'],
                                                                       axis=1)
    return user_statistics_dataframe


def filter_filenames_to_file_extensions(user_statistics_dataframe):
    user_statistics_dataframe.filter(items=['path'])
    user_statistics_dataframe['path'] = user_statistics_dataframe.path.str.rsplit('.', 1).str[-1]
    user_statistics_dataframe.head()

    return user_statistics_dataframe

def get_main_branch_creator_email(repo_path):
    try:
        os.chdir(repo_path)
        cmd = "git for-each-ref --format='%(authoremail) %09 %(refname)'"
        p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE)
        stdout, _ = p.communicate()
        os.chdir("../../..")
        table = read_csv(io.StringIO(stdout.decode('utf-8')), sep='\t', names=['email', 'branch'],
                         parse_dates=False).fillna(method='ffill').dropna()
        table.set_index('branch', inplace=True)
        raw_main_branch_creator_table = table.to_dict()["email"]

        possible_branch_names = [" refs/remotes/origin/master", "refs/remotes/origin/main"]

        for possible_branch_name in possible_branch_names:
            if possible_branch_name in raw_main_branch_creator_table:
                return raw_main_branch_creator_table[possible_branch_name].replace("<", '').replace(">", '')

        raise Exception()
    except:
        return ""

def collect_raw_statistics(repo_path, current_username, user_statistics_dataframe, is_email_try):
    os.chdir(repo_path)
    cmd = "git log --no-renames --numstat --author=" + current_username + " --pretty=format:'%x09%x09%x09%h'"
    p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE)
    stdout, _ = p.communicate()
    os.chdir("../../..")
    table = read_csv(io.StringIO(stdout.decode('utf-8')), sep='\t', names=['additions', 'deletions', 'path', 'commit'],
                     parse_dates=True).fillna(method='ffill').dropna()
    temp = pd.DataFrame(table)
    temp = temp.drop_duplicates(['path', 'commit'], keep='first')

    if temp.empty:
        if is_email_try:
            return user_statistics_dataframe
        creator_email = get_main_branch_creator_email(repo_path)

        if creator_email:
            return collect_raw_statistics(repo_path, creator_email, user_statistics_dataframe, True)
        else:
            return user_statistics_dataframe

    return pd.concat([user_statistics_dataframe, temp])


def get_git_repository(repo, current_username):
    local_repository_path = repository_local_path(current_username, repo['name'])

    Path(local_repository_path).mkdir(parents=True, exist_ok=True)

    if len(os.listdir(local_repository_path)) == 0:
        try:
            Repo.clone_from(repo['clone_url'], local_repository_path)
        except GitCommandError:
            print("Guessing that git repo " + repo['name'] + " is probably already cloned, proceding...")

    return local_repository_path

def get_usernames_list():
    profiles_list = json.loads(open("scripts_as_process/individual_developers_info.json", 'r').read())
    username_list = []
    for profile in profiles_list:
        partially_parsed_profile = profile['githubURL'].replace("github.com/", '')
        username_list.append(re.sub("[^0-9a-zA-Z]", '', partially_parsed_profile))

    return username_list

def initGithubInformationJSONFile():
    global path_to_save_github_stats

    if not os.path.exists(path_to_save_github_stats):
        with open(path_to_save_github_stats, mode='w', encoding='utf-8') as file:
            json.dump([], file)


def saveGithubInformationAsJSON(user_statistics, username, repos_count):
    global path_to_save_github_stats
    user_statistics.set_index('path', inplace=True)

    with open(path_to_save_github_stats) as file:
        profile_contents = json.loads(file.read())

    if len(profile_contents) == 0:
        profile_contents = dict()

    profile_contents[username] = dict()
    profile_contents[username]["reposCount"] = repos_count
    profile_contents[username]["statistics"] = user_statistics.to_dict('dict')
    with open(path_to_save_github_stats, mode='w') as f:
        f.write(json.dumps(profile_contents, indent=2))


def deleteSavedGithubRepos(user_repos_path):
    shutil.rmtree(user_repos_path)


def main():
    initGithubInformationJSONFile()
    usernames_list = get_usernames_list()
    fetched_counter = 0

    already_fetched_users = []
    with open(path_to_save_github_stats) as file:
        profile_contents = json.loads(file.read())
        if len(profile_contents) > 0:
            already_fetched_users = profile_contents.keys()

    for current_username in usernames_list:
        if current_username in already_fetched_users:
            continue

        try:
            user_raw_statistics_dataframe = pd.DataFrame()
            parsed_repos_list = get_repos_list(current_username)

            for repo in parsed_repos_list:
                local_repo_path = get_git_repository(repo, current_username)
                user_raw_statistics_dataframe = collect_raw_statistics(local_repo_path, current_username,
                                                                       user_raw_statistics_dataframe, False)

            if user_raw_statistics_dataframe.empty:
                raise Exception("Could not identify any commits in the repos that correspont to the gihtub user account. Skipping...")

            user_statistics = process_dataframe_to_final_format(user_raw_statistics_dataframe)
            saveGithubInformationAsJSON(user_statistics, current_username, len(parsed_repos_list))
            deleteSavedGithubRepos(user_local_path(current_username))
        except Exception as e:
            print(str(e))
            print("Failed somewhere in the process of getting statistics of the user " + current_username + ". Skipping...")
        print()
        print("Done with user " + current_username + ". Now going to the next...")
        print()

    print("All finished.")

main()
