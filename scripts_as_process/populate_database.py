import json
import mysql.connector
import csv

profile_stats = []
profiles = []
languages_and_extensions = dict()
error_github_usernames = []

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="abacate1",
  database="ic_ufmg",
  autocommit=True
)

mycursor = mydb.cursor()
languages_and_ids = dict()

def find_github_profile(user):
    global error_github_usernames
    for profile in profiles:
        if user in profile["githubURL"]:
            return profile

    error_github_usernames.append(user)
    return None

def is_developer_already_added(user):
    sql_query = 'SELECT * FROM ic_ufmg.developer WHERE githubUrl like "%' + remove_invalid_chars(user) + '%"'
    mycursor.execute(sql_query)
    result = mycursor.fetchone()

    return result is not None

def insert_developer(profile, reposCount):
    sql_query = 'INSERT INTO ic_ufmg.developer(name, searchedReposCount, githubUrl, workanaUrl, role) VALUES ("' + remove_invalid_chars(profile["name"]) + '","' + str(reposCount) + '","' + remove_invalid_chars(profile["githubURL"]) + '", "' + remove_invalid_chars(profile["workanaURL"]) + '", "' + remove_invalid_chars(profile["role"]) + '")'
    mycursor.execute(sql_query)

    return mycursor.lastrowid

def insert_language(name):
    sql_query = 'INSERT INTO ic_ufmg.language(name) VALUES ("' + remove_invalid_chars(name) + '")'
    mycursor.execute(sql_query)

    return mycursor.lastrowid

def get_language(name):
    global languages_and_ids

    if name in languages_and_ids:
        return languages_and_ids[name]

    sql_query = 'SELECT * FROM ic_ufmg.language WHERE name = "' + remove_invalid_chars(name) + '"'
    mycursor.execute(sql_query)
    result = mycursor.fetchone()

    if result is not None:
        languages_and_ids[name] = result[0]
        return result[0]
    else:
        return False

def insert_developer_language_association(developer_id, language_id, loc, commitsCount):
    sql_query = 'INSERT INTO ic_ufmg.developer_has_languages(developerId, languageId, loc, commitsCount) VALUES (' + str(developer_id) + ', ' + str(language_id) + ', ' + str(loc) + ', ' + str(commitsCount) + ')'
    mycursor.execute(sql_query)

    return mycursor.lastrowid

def remove_invalid_chars(string):
    return string.replace('"', '')


def get_data_from_files():
    global profile_stats
    global profiles
    global languages_and_extensions

    profile_stats_path = 'github_info.json'
    profiles_path = 'individual_developers_info.json'
    languages_and_extensions_path = "habilities_and_extensions_relationship.csv"

    profile_stats = json.load(open(profile_stats_path))
    profiles = json.load(open(profiles_path))
    reader = csv.reader(open(languages_and_extensions_path))

    for row in reader:
        k, v = row
        languages_and_extensions[v] = k


get_data_from_files()


for username, info in profile_stats.items():
    profile = find_github_profile(username)

    if profile is None:
        continue

    if is_developer_already_added(username):
        continue

    developer_id = insert_developer(profile, info["reposCount"])
    developer_reported_habilities = profile["skills"]["Habilidades"].values()

    for file_extension in info["statistics"]["loc"].keys():
        loc = info["statistics"]["loc"][file_extension]
        commits_count = info["statistics"]["commits_count"][file_extension]

        if file_extension not in languages_and_extensions:
            continue

        ability = languages_and_extensions[file_extension]

        if ability not in developer_reported_habilities:
            continue

        language_id = get_language(ability)

        if not language_id:
            language_id = insert_language(ability)

        if loc > 0:
            insert_developer_language_association(developer_id, language_id, loc, commits_count)

print(error_github_usernames)
