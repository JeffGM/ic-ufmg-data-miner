import mysql.connector

class MysqlDatabaseInterface:
    def __init(self):
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abacate1",
            database="ic_ufmg",
            autocommit=True
        )
        self.mycursor = self.mydb.cursor()

    def remove_invalid_chars(self, string):
        return string.replace('"', '')

    def is_developer_already_added(self, user):
        sql_query = 'SELECT * FROM ic_ufmg.developer WHERE githubUrl like "%' + self.remove_invalid_chars(user) + '%"'
        self.mycursor.execute(sql_query)
        result = self.mycursor.fetchone()

        return result is not None

    def insert_developer(self, profile, reposCount):
        sql_query = 'INSERT INTO ic_ufmg.developer(name, searchedReposCount, githubUrl, workanaUrl, role) VALUES ("' + self.remove_invalid_chars(
            profile["name"]) + '","' + str(reposCount) + '","' + self.remove_invalid_chars(
            profile["githubURL"]) + '", "' + self.remove_invalid_chars(
            profile["workanaURL"]) + '", "' + self.remove_invalid_chars(profile["role"]) + '")'
        self.mycursor.execute(sql_query)

        return self.mycursor.lastrowid

    def insert_developer_language_association(self, developer_id, language_id, loc, commitsCount):
        sql_query = 'INSERT INTO ic_ufmg.developer_has_languages(developerId, languageId, loc, commitsCount) VALUES (' + str(
            developer_id) + ', ' + str(language_id) + ', ' + str(loc) + ', ' + str(commitsCount) + ')'
        self.mycursor.execute(sql_query)

        return self.mycursor.lastrowid

    def insert_language(self, name):
        sql_query = 'INSERT INTO ic_ufmg.language(name) VALUES ("' + self.remove_invalid_chars(name) + '")'
        self.mycursor.execute(sql_query)

        return self.mycursor.lastrowid

    def get_language(self, name, cached_languages_and_ids):
        if name in cached_languages_and_ids:
            return cached_languages_and_ids[name]

        sql_query = 'SELECT * FROM ic_ufmg.language WHERE name = "' + self.remove_invalid_chars(name) + '"'
        self.mycursor.execute(sql_query)
        result = self.mycursor.fetchone()

        if result is not None:
            cached_languages_and_ids[name] = result[0]
            return result[0]
        else:
            return False
