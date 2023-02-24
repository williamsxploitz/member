class Config:
    ADMIN_EMAIL = "test@member.com"
    SECRET_KEY = "4749FNJDBjbndb3"

class Liveconfig(Config):
    ADMIN_EMAIL="admin@memba.com"
    SERVER_ADDRESS="https://server.member.com"

class TestConfig(Config):
    SERVER_ADDRESS="https://127.0.0.1:5000"