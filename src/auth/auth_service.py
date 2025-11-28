from typing import Dict, Optional
from datetime import datetime
from src.auth.jwt_handler import create_access_token, create_refresh_token
from src.auth.password_utils import hash_password, verify_password

# Mock Database for demonstration since actual DB connection isn't set up
# In production, replace with actual DB calls
MOCK_USERS_DB = {}
MOCK_TOKEN_BLACKLIST = set()

class AuthService:
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        return MOCK_USERS_DB.get(email)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        for user in MOCK_USERS_DB.values():
            if user["id"] == user_id:
                return user
        return None

    async def create_patient(self, user_data: Dict) -> Dict:
        import uuid
        user_id = str(uuid.uuid4())
        user_data["id"] = user_id
        MOCK_USERS_DB[user_data["email"]] = user_data
        return user_data

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def create_access_token(self, user_id: str) -> str:
        return create_access_token(user_id)

    def create_refresh_token(self, user_id: str) -> str:
        return create_refresh_token(user_id)

    async def send_verification_email(self, email: str, user_id: str):
        # Mock email sending
        print(f"Sending verification email to {email} for user {user_id}")

    async def log_login_event(self, user_id: str):
        print(f"User {user_id} logged in")

    async def is_token_blacklisted(self, token: str) -> bool:
        return token in MOCK_TOKEN_BLACKLIST

    async def blacklist_token(self, token: str):
        MOCK_TOKEN_BLACKLIST.add(token)
