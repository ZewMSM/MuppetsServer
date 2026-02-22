from fastapi import APIRouter, Query

# localmodules:start
from config import GAME_SERVER_IP
# localmodules:end

router = APIRouter()


@router.get("/auth.php")
async def auth(
    u: str | None = Query(None, alias="u"),
    p: str | None = Query(None, alias="p"),
    t: str | None = Query(None, alias="t"),
    bbb_id: str | None = Query(None, alias="bbb_id"),
    lang: str | None = Query(None, alias="lang"),
    client_version: str | None = Query(None, alias="client_version"),
    mac: str | None = Query(None, alias="mac"),
    platform: str | None = Query(None, alias="platform"),
    devid: str | None = Query(None, alias="devid"),
    aid: str | None = Query(None, alias="aid"),
):
    """Stub auth: returns fixed anon credentials and serverIp."""
    anon_name = "anon_stub"
    anon_pass = "stub_pass"
    stub_bbb_id = "1796072285"
    r = {
        "ok": True,
        "login_type": t or "anon",
        "anon_name": anon_name,
        "anon_pass": anon_pass,
        "anon_bbb_id": stub_bbb_id,
        "username": stub_bbb_id,
        "account_id": stub_bbb_id,
        "auto_login": True,
        "serverIp": GAME_SERVER_IP,
    }

    print(r)
    return r


@router.get("/check_user.php")
async def check_user(
    u: str | None = Query(None, alias="u"),
    p: str | None = Query(None, alias="p"),
):
    """Stub: always ok."""
    return {"ok": True}


@router.get("/content/{ver}/files.json")
async def get_updates(ver: str):
    """Stub: empty file list."""
    return []


@router.post("/content/getFile.php")
async def get_file():
    """Stub: empty body."""
    return ""

# Алиас для сборки в один файл (auth_app использует auth_router.router)
auth_router = type("_RouterAlias", (), {})()
auth_router.router = router
