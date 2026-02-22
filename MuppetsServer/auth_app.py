from fastapi import FastAPI

# localmodules:start
from MuppetsServer.routers import auth as auth_router
from config import ROUTE_PREFIX
# localmodules:end

app = FastAPI()
_route_prefix = f"/{ROUTE_PREFIX}" if ROUTE_PREFIX else ""
app.include_router(auth_router.router, prefix=_route_prefix)

# Алиас для сборки в один файл (main использует auth_app)
auth_app = app
