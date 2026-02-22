import os

GAME_SERVER_IP = os.environ.get("GAME_SERVER_IP", "127.0.0.1")
ROUTE_PREFIX = os.environ.get("ROUTE_PREFIX", "")
HTTP_PORT = os.environ.get("HTTP_PORT", "9013")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "zewmsm.db")
HOME = os.environ.get("HOME", ".")
