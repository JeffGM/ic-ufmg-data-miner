import DatabaseInterface
import json
import csv

class AnalyticsReaderAndUploader():
    def __init__(self):
        self.databaseInterface = DatabaseInterface.MysqlDatabaseInterface()
        self.profile_stats = []
        self.profiles = []
        self.languages_and_extensions = dict()
        self.error_github_usernames = []
        self.languages_and_ids = dict()

    def find_github_profile(self, user):
        global error_github_usernames
        for profile in profiles:
            if user in profile["githubURL"]:
                return profile

        error_github_usernames.append(user)
        return None


    def get_data_from_files(self):
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

    def process(self):
        self.get_data_from_files()

        for username, info in profile_stats.items():
            profile = self.find_github_profile(username)

            if profile is None:
                continue

            if self.databaseInterface.is_developer_already_added(username):
                continue

            developer_id = self.databaseInterface.insert_developer(profile, info["reposCount"])
            developer_reported_habilities = profile["skills"]["Habilidades"].values()

            for file_extension in info["statistics"]["loc"].keys():
                loc = info["statistics"]["loc"][file_extension]
                commits_count = info["statistics"]["commits_count"][file_extension]

                if file_extension not in languages_and_extensions:
                    continue

                ability = languages_and_extensions[file_extension]

                if ability not in developer_reported_habilities:
                    continue

                language_id = self.databaseInterface.get_language(ability, self.languages_and_ids)

                if not language_id:
                    language_id = self.databaseInterface.insert_language(ability)

                if loc > 0:
                    self.databaseInterface.insert_developer_language_association(developer_id, language_id, loc, commits_count)