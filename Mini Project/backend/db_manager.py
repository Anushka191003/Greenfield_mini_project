# backend/db_manager.py
import pymysql

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self, host, user, password, database):
        if self.connection is None or not self.connection.open:
            try:
                self.connection = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    cursorclass=pymysql.cursors.DictCursor
                )
            except Exception as e:
                print(f"Error connecting to MySQL: {e}")
                raise e
        return self.connection

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None