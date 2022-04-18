import csv
import os
import pandas as pd

local_repository_path = "temp_repo_files/"

downloaded_repos = os.listdir(local_repository_path)

report_path = "final_report.csv"


def append_csv_file(file_to_read):
    second = pd.read_csv(file_to_read)
    try:
        first = pd.read_csv(report_path)
    except:
        second.to_csv(report_path, index=False)
        return


    merged = pd.concat([first, second])
    merged.to_csv(report_path, index=False)



for repo in downloaded_repos:
    try:
        files_list = os.listdir(local_repository_path + repo)
        for file in files_list:
            if "csv" in file:
                append_csv_file(local_repository_path + repo + "/" + file)
    except:
        pass


