from fastapi import FastAPI
from src.models.baseModel import Device
import uvicorn


app = FastAPI()

@app.get("/")
async def root():
    return{"Message: Hello World"}




if __name__ == '__main__':

    uvicorn.run("endpoints:app", host="localhost", port=8000, reload= True)