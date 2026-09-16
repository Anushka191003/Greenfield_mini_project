from urllib.parse import parse_qs, unquote, urlsplit

import pymysql

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self, uri):
        if self.connection is None or not self.connection.open:
            try:
                parsed = urlsplit(uri)
                query = parse_qs(parsed.query)
                connect_args = {
                    "host": parsed.hostname,
                    "port": parsed.port or 3306,
                    "user": unquote(parsed.username or ""),
                    "password": unquote(parsed.password or ""),
                    "database": parsed.path.lstrip("/"),
                    "cursorclass": pymysql.cursors.DictCursor,
                }
                if query.get("ssl-mode", [""])[0].upper() == "REQUIRED":
                    connect_args["ssl"] = {"check_hostname": False}
                self.connection = pymysql.connect(
                    **connect_args
                )
            except Exception as e:
                print(f"Error connecting to MySQL: {e}")
                raise e
        return self.connection

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None