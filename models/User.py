from pydantic import BaseModel
from typing import List
from models.TrafficPoint import TrafficPoint


class User(BaseModel):
    userid: str
    latitude: float
    longitude: float
    end_latitude: float
    end_longitude: float
    traffic_data: List[TrafficPoint] = None
