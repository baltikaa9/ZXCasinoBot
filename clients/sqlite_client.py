import sqlite3

CREATE_TABLE = '''create table if not exists users (
    user_id int primary key,
    username text,
    firstname text,
    balance int,
    last_date_shell date, 
    shell_count int    
    );'''

CREATE_USER = """INSERT INTO users (user_id, username, firstname, balance) VALUES (?, ?, ?, ?)"""

GET_USER = """SELECT * FROM users WHERE user_id = %s;"""


class SQLiteClient:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.conn = None

    def create_conn(self):
        self.conn = sqlite3.connect(self.filepath, check_same_thread=False)

    def close_conn(self):
        self.conn.close()

    def execute_command(self, command: str, params: tuple):
        if self.conn is not None:
            self.conn.execute(command, params)
            self.conn.commit()
        else:
            raise ConnectionError('You need to create connection to database!')

    def execute_select_command(self, command: str, params: tuple = None):
        if self.conn is not None:
            cur = self.conn.cursor()
            if params is None:
                cur.execute(command)
            else:
                cur.execute(command, params)
            return cur.fetchall()
        else:
            raise ConnectionError('You need to create connection to database!')


if __name__ == '__main__':
    conn = sqlite3.connect('./users.db')
    conn.execute(CREATE_TABLE)
    conn.commit()

    # sqlite_client = SQLiteClient('users.db')
    # sqlite_client.create_conn()
    # # sqlite_client.execute_command('''insert into users (user_id, username, firstname, balance) values (?, ?, ?, ?)''', (2, 'sosibibu', 'ser', 10000))
    # print(sqlite_client.execute_select_command(GET_USER % 1))
    # sqlite_client.close_conn()