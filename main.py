# Description: Main entry point for the application
import redis
from fastapi import FastAPI, WebSocket, Request, Depends
from fastapi.websockets import WebSocketDisconnect
from models.User import User
from utils.logger import logger
from utils.paths import set_path_for_user, update_traffic_for_user
from utils.connection_manager import manager

app = FastAPI()


@app.on_event("startup")
def startup_event():
    app.state.redis = redis.Redis(host='redis', port=6379, db=0)


@app.on_event("shutdown")
def shutdown_event():
    app.state.redis.close()


@app.get("/")
async def get_root():
    return {"message": "Hello, world!"}


def get_redis(request: Request):
    return request.app.state.redis


@app.post("/set_path")
async def set_path(user: User, r: redis.Redis = Depends(get_redis)):
    try:
        logger.info("Called set_path for %s", user.userid)

        path_coordinates = set_path_for_user(user, r)
        logger.info("Successfully set path for user %s", user.userid)

        return {"path": path_coordinates}
    except Exception as e:
        error = "Error setting path for user %s: %s", user.userid, e
        logger.error(error)
        return {"error": error}


@app.post("/update_traffic")
async def update_traffic(user: User, r: redis.Redis = Depends(get_redis)):
    try:
        logger.info("Called update_traffic for %s", user.userid)

        path_coordinates = await update_traffic_for_user(user, r)
        logger.info("Successfully updated path for user %s", user.userid)

        return {"path": path_coordinates}
    except Exception as e:
        error = "Error updating path for user %s: %s", user.userid, e
        logger.error(error)
        return {"error": error}


@app.websocket("/ws/{client_id}")
async def updates(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Just keep the connection open.
        # update_traffic will push updates on this channel
        await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

