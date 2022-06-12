import pandas as pd
import re
import shlex
import subprocess as sp
import io
from pandas import read_csv
import os
import json

class SourceCodeAnalyzer():
    def __init__(self):
        self.local_temp_repo_files = "temp_repo_files/"

    def collect_raw_statistics(self, repo_path, current_username, user_statistics_dataframe, is_email_try):
        os.chdir(repo_path)
        cmd = "git log --no-renames --numstat --author=" + current_username + " --pretty=format:'%x09%x09%x09%h'"
        p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE)
        stdout, _ = p.communicate()
        os.chdir("../../..")
        table = read_csv(io.StringIO(stdout.decode('utf-8')), sep='\t',
                         names=['additions', 'deletions', 'path', 'commit'],
                         parse_dates=True).fillna(method='ffill').dropna()
        temp = pd.DataFrame(table)
        temp = temp.drop_duplicates(['path', 'commit'], keep='first')

        if temp.empty:
            if is_email_try:
                return user_statistics_dataframe
            creator_email = self.get_main_branch_creator_email(repo_path)

            if creator_email:
                return self.collect_raw_statistics(repo_path, creator_email, user_statistics_dataframe, True)
            else:
                return user_statistics_dataframe

        return pd.concat([user_statistics_dataframe, temp])

    def get_main_branch_creator_email(self,repo_path):
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

    def insert_loc_in_dataframe(self, user_statistics_dataframe):
        user_statistics_dataframe = user_statistics_dataframe.replace({'-': 0})

        user_statistics_dataframe['deletions'] = user_statistics_dataframe['deletions'].astype(float)
        user_statistics_dataframe['additions'] = user_statistics_dataframe['additions'].astype(float)

        user_statistics_dataframe['deletions'] = user_statistics_dataframe['deletions'].astype(int)
        user_statistics_dataframe['additions'] = user_statistics_dataframe['additions'].astype(int)

        user_statistics_dataframe['loc'] = user_statistics_dataframe.apply(lambda x: x['additions'] + x['deletions'],
                                                                           axis=1)
        return user_statistics_dataframe

    def aggregate_by_commits_count(self, user_statistics_dataframe, partial_dataframe_with_file_extensions):
        user_statistics_dataframe['commits_count'] = 0
        commits_count_dataframe = partial_dataframe_with_file_extensions.drop_duplicates(['path', 'commit'],
                                                                                         keep='first')
        commits_count_dataframe = commits_count_dataframe['path'].value_counts()
        for language in user_statistics_dataframe['path']:
            user_statistics_dataframe.loc[user_statistics_dataframe['path'] == language, 'commits_count'] = \
            commits_count_dataframe[language]

        return user_statistics_dataframe

    def aggregate_by_loc(self, user_statistics_dataframe):
        user_statistics_dataframe = user_statistics_dataframe.groupby(['path'])['loc'].agg('sum')

        user_statistics_dataframe = user_statistics_dataframe.reset_index()
        user_statistics_dataframe.head()
        return user_statistics_dataframe

