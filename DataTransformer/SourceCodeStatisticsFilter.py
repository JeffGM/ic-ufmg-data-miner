def SourceCodeStatisticsFilter():
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

    def filter_filenames_to_file_extensions(user_statistics_dataframe):
        user_statistics_dataframe.filter(items=['path'])
        user_statistics_dataframe['path'] = user_statistics_dataframe.path.str.rsplit('.', 1).str[-1]
        user_statistics_dataframe.head()

        return user_statistics_dataframe