import psycopg2
import psycopg2.extras
import sys


class DbHandler(object):

    def __init__(self, db_name):
        super(DbHandler, self).__init__()
        self.db_name = db_name
        self.db = psycopg2.connect(self.db_name)
        cur = self.db.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS "users" (id SERIAL PRIMARY KEY, name VARCHAR(100), telegram_id INTEGER);')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS "files" (id SERIAL PRIMARY KEY, name VARCHAR(300), mime VARCHAR(100), size REAL, telegram_id INTEGER, directory_id INTEGER, user_id INTEGER);')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS "directories" (id SERIAL PRIMARY KEY, name VARCHAR(300), parent_directory_id INTEGER, user_id INTEGER);')
        cur.execute(
            'CREATE TABLE IF NOT EXISTS "shares" (id SERIAL PRIMARY KEY, directory_id INTEGER, parent_directory_id INTEGER, user_id INTEGER);')

    def __db_connect__(self):
        self.cursor = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __db_disconnect__(self):
        pass

    def insert(self, table, values, updater=None):
        if (not updater):
            updater = values

        try:
            updater_str = ', '.join([(k + (" is " if updater[k] == "NULL" else "=") + (
                "NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'"))) for k in updater.keys()])
            values_str = ', '.join([("NULL" if values[k] == "NULL" else (
                "'" + str(values[k]) + "'")) for k in values.keys()])
            columns_str = ', '.join([str(k) for k in values.keys()])
            where_str = ' AND '.join([(k + (" is " if updater[k] == "NULL" else "=") + (
                "NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'"))) for k in updater.keys()])
        except Exception as e:
            print("--values1")
            print(values)
            print("--updater2")
            print(updater)
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return 0

        exists = len(self.select(table, where_str))

        try:
            self.__db_connect__()
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            self.__db_disconnect__()
            return 0

        if (exists):
            try:
                values_str = ', '.join(
                    [(k + "=" + ("NULL" if values[k] == "NULL" else ("'" + str(values[k]) + "'"))) for k in values.keys()])
            except Exception as e:
                print("--values3")
                print(values)
                print("Line: " + str(sys.exc_info()[-1].tb_lineno))
                print(e)

            sql = "UPDATE " + table + " SET " + values_str + " WHERE " + where_str

            try:
                self.cursor.execute(sql)
                self.db.commit()
                self.__db_disconnect__()
                return 2
            except Exception as e:
                print("Line: " + str(sys.exc_info()[-1].tb_lineno))
                print(e)
                return 0

        sql = "INSERT INTO " + table + "(" + columns_str + ") VALUES (" + values_str + ")"

        try:
            self.cursor.execute(sql)
            self.db.commit()
            self.__db_disconnect__()
            return 1
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return 0

    def select(self, table, where=None):
        if (where):
            sql = "SELECT '" + table + "' as type, * FROM " + table + " WHERE (" + where + ")"
            return self._selectRaw(sql)
        else:
            sql = "SELECT '" + table + "' as type, * FROM " + table
            return self.cursor.execute(sql)

    def _selectRaw(self, sql):
        try:
            self.__db_connect__()
            self.cursor.execute(sql)
            data = self.cursor.fetchall()
            self.__db_disconnect__()
            return data
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            self.__db_disconnect__()
            return False

    def delete(self, table, where=None):
        try:
            self.__db_connect__()
            if (where):
                sql = "DELETE FROM " + table + " WHERE (" + where + ")"
                self.cursor.execute(sql)
            else:
                sql = "DELETE FROM " + table
                self.cursor.execute(sql)
            self.db.commit()
            self.__db_disconnect__()
            return True
        except Exception as e:
            print(sql)
            self.__db_disconnect__()
            return False
