from datetime import date, datetime

from clients.sqlite_client import SQLiteClient


class UserActioner:
    _CREATE_USER = """INSERT INTO users (user_id, username, firstname, balance, last_date_shell, shell_count) VALUES (?, ?, ?, ?, ?, ?)"""

    _GET_USER = """SELECT * FROM users WHERE user_id = ?"""

    _GET_USER_BY_USNAME = """SELECT * FROM users WHERE username = ?"""

    _UPDATE_BALANCE = """UPDATE users SET balance = ? WHERE user_id = ?"""

    _GET_USERS_ORDER_BY_BALANCE = """SELECT firstname, balance FROM users ORDER BY balance DESC"""

    _UPDATE_LAST_DATE_SHELL = """UPDATE users SET last_date_shell = ? WHERE user_id = ?"""

    _UPDATE_SHELL_COUNT = """UPDATE users SET shell_count = ? WHERE user_id = ?"""

    def __init__(self, database_client: SQLiteClient):
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def shutdown(self):
        self.database_client.close_conn()

    def get_user(self, user_id: int):
        try:
            user = self.database_client.execute_select_command(self._GET_USER, (user_id,))
            return user[0] if user else user
        except ConnectionError:
            raise Exception('You need to setup!')

    def get_user_by_username(self, username: str):
        try:
            user = self.database_client.execute_select_command(self._GET_USER_BY_USNAME, (username,))
            return user[0] if user else user
        except ConnectionError:
            raise Exception('You need to setup!')

    def create_user(self, user_id: int, username: str, firstname: str, balance: int, last_shell_update: date,
                    shell_count: int):
        try:
            self.database_client.execute_command(self._CREATE_USER, (
            user_id, username, firstname, balance, last_shell_update, shell_count))
        except ConnectionError:
            raise Exception('You need to setup!')

    def user_exists(self, user_id: int):
        try:
            user = self.database_client.execute_select_command(self._GET_USER, (user_id,))
            return True if user else False
        except ConnectionError:
            raise Exception('You need to setup!')

    def get_balance(self, user_id: int):
        try:
            user = self.get_user(user_id)
            return user[3] if user else None
        except ConnectionError:
            raise Exception('You need to setup!')

    def update_balance(self, user_id: int, new_balance: int):
        try:
            self.database_client.execute_command(self._UPDATE_BALANCE, (new_balance, user_id))
        except ConnectionError:
            raise Exception('You need to setup!')

    def get_top_users(self):
        try:
            user = self.database_client.execute_select_command(self._GET_USERS_ORDER_BY_BALANCE)
            return user
        except ConnectionError:
            raise Exception('You need to setup!')

    def update_shell_date(self, user_id: int, updated_date: date):
        try:
            self.database_client.execute_command(self._UPDATE_LAST_DATE_SHELL, (updated_date, user_id))
        except ConnectionError:
            raise Exception('You need to setup!')

    def get_shell_date(self, user_id: int):
        try:
            user = self.get_user(user_id)
            return datetime.strptime(user[4], '%Y-%m-%d').date() if user else None
        except ConnectionError:
            raise Exception('You need to setup!')

    def update_shell_count(self, user_id: int, updated_count: date):
        try:
            self.database_client.execute_command(self._UPDATE_SHELL_COUNT, (updated_count, user_id))
        except ConnectionError:
            raise Exception('You need to setup!')

    def get_shell_count(self, user_id):
        try:
            user = self.get_user(user_id)
            return user[5] if user else None
        except ConnectionError:
            raise Exception('You need to setup!')


if __name__ == '__main__':
    user_actioner = UserActioner(SQLiteClient('../db/users.db'))
    user_actioner.setup()
    # print(user_actioner.get_shell_date(484127122))
    print(user_actioner.get_shell_count(484127122))
    user_actioner.shutdown()
