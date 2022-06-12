import SourceCodeAnalyzer
import SourceCodeStatisticsFilter
import json
import shutil

class DeveloperInformationAndAnalyticsJoiner():
    def __init__(self):
        self.sourceCodeStatisticsFilter = SourceCodeStatisticsFilter.SourceCodeStatisticsFilter()
        self.sourceCodeAnalyzer = SourceCodeAnalyzer.SourceCodeAnalyzer()
        self.partial_path = "partial.json"
        local_temp_repo_files = "temp_repo_files/"
        self.path_to_save_github_stats = "scripts_as_process/github_info.json"
        self.user_local_path = lambda username: local_temp_repo_files + username

    def read_partial(self):
        return json.loads(self.partial_path)

    def process(self):
        try:
            partial_info = self.read_partial()
            user_raw_statistics_dataframe = dict()
            previous_username = ""

            for local_repo_path, current_username in partial_info:
                user_raw_statistics_dataframe = self.sourceCodeAnalyzer.collect_raw_statistics(local_repo_path, current_username,
                                                                       user_raw_statistics_dataframe, False)


                if user_raw_statistics_dataframe.empty:
                    raise Exception(
                        "Could not identify any commits in the repos that correspont to the gihtub user account. Skipping...")

                if previous_username != current_username and previous_username != "":
                    user_statistics = self.process_dataframe_to_final_format(user_raw_statistics_dataframe)
                    self.saveGithubInformationAsJSON(user_statistics, current_username, len(partial_info["parsed_repos_list"]))
                    self.deleteSavedGithubRepos(self.user_local_path(current_username))

                    previous_username = current_username
                elif previous_username != current_username:
                    previous_username = current_username

            self.process_dataframe_to_final_format(user_raw_statistics_dataframe)
        except:
            print("An error ocurred while processing the git repositories")


    def process_dataframe_to_final_format(self, user_raw_statistics_dataframe):
        partial_dataframe_with_file_extensions = self.sourceCodeStatisticsFilter.filter_filenames_to_file_extensions(user_raw_statistics_dataframe)
        partial_dataframe = self.sourceCodeAnalyzer.insert_loc_in_dataframe(partial_dataframe_with_file_extensions)
        partial_dataframe = self.sourceCodeAnalyzer.aggregate_by_loc(partial_dataframe)
        partial_dataframe = self.sourceCodeStatisticsFilter.sort_values_by_loc(partial_dataframe)
        partial_dataframe = self.sourceCodeStatisticsFilter.filter_invalid_filetypes(partial_dataframe)
        partial_dataframe = self.sourceCodeStatisticsFilter.filter_null_rows(partial_dataframe)
        partial_dataframe = self.sourceCodeAnalyzer.aggregate_by_commits_count(partial_dataframe, partial_dataframe_with_file_extensions)

        return partial_dataframe

    def saveGithubInformationAsJSON(self,user_statistics, username, repos_count):
        user_statistics.set_index('path', inplace=True)

        with open(self.path_to_save_github_stats) as file:
            profile_contents = json.loads(file.read())

        if len(profile_contents) == 0:
            profile_contents = dict()

        profile_contents[username] = dict()
        profile_contents[username]["reposCount"] = repos_count
        profile_contents[username]["statistics"] = user_statistics.to_dict('dict')
        with open(self.path_to_save_github_stats, mode='w') as f:
            f.write(json.dumps(profile_contents, indent=2))

    def deleteSavedGithubRepos(self,user_repos_path):
        shutil.rmtree(user_repos_path)