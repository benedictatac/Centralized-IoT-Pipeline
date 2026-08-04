from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.baseModel import Device, Reading, ReadingResponse
from src.pipeline.storage import get_db
from src.models.database import ReadingDB
from sqlalchemy import  select
import json
import uuid
import uvicorn

# Import get_db from storage  gives you the session
# Write a query select(ReadingDB).order_by(ReadingDB.timestamp.desc()).limit(limit)
# Define a response model  what the JSON output looks like
# Return the results
app = FastAPI()





@app.get("/")
async def root():
    return{"Message": "Hello World"}

#response_model initiates automatic validaiton and field filtering 
#specific get endpoint for a device
@app.get("/events/{device_id}", response_model=list[ReadingResponse])
async def get_readings_for_device(device_id: uuid.UUID, limit: int = 10, db: AsyncSession = Depends(get_db)):
    query_readings = (
        select(ReadingDB)
        .where(ReadingDB.device_id == device_id)
        .order_by(ReadingDB.timestamp.desc())
        .limit(limit)
    )
    readings = await db.scalars(query_readings)
    return readings.all()

@app.get("/events", response_model = list[ReadingResponse])

async def get_all_readings(limit: int = 50, db:AsyncSession = Depends(get_db)):

    query_readings = select(ReadingDB).order_by(ReadingDB.timestamp.desc()).limit(limit)

    readings = await db.scalars(query_readings)
    return readings.all()


if __name__ == '__main__':

    uvicorn.run("endpoints:app", host="localhost", port=8000, reload= True)