from fastapi import FastAPI

from MuppetsServer.routers import auth as auth_router

app = FastAPI()
app.include_router(auth_router.router)
