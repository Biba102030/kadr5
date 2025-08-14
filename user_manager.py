import json
import logging
import os

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.users = {}
        self.load_users()

    def load_users(self):
        try:
            if os.path.exists("users.json"):
                with open("users.json", "r", encoding="utf-8") as f:
                    self.users = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Ошибка загрузки пользователей: {e}")
            self.users = {}

    def save_users(self):
        try:
            with open("users.json", "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения пользователей: {e}")

    def add_user(self, user_id, name, phone):
        self.users[str(user_id)] = {"name": name, "phone": phone}
        self.save_users()

    def get_user(self, user_id):
        return self.users.get(str(user_id))