from pydantic import BaseModel
from typing import List, Optional
from models.TrafficPoint import TrafficPoint


class User(BaseModel):
    userid: str
    latitude: float
    longitude: float
    end_latitude: float
    end_longitude: float
    traffic_data: Optional[List[TrafficPoint]] = None
