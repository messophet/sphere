from pydantic import BaseModel


class TrafficPoint(BaseModel):
    latitude: float
    longitude: float
    delay: int  # delay in minutes