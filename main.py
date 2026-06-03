import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager

app = FastAPI()

# Target API you are relaying to
UPSTREAM_URL = "http://192.168.12.111"

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Connect to your Redis instance
    redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    # Initialize the limiter
    await FastAPILimiter.init(redis_client)
    yield
    # Clean up connections on shutdown
    await redis_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def get_json_relay():
    async with httpx.AsyncClient() as client:
        try:
            # Forward the GET request
            response = await client.get(UPSTREAM_URL)
            
            # Raise exception if upstream API fails
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Upstream error")
                
            # Return the JSON data directly to the client
            return JSONResponse(content=response.json())
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Relay failed: {e}")
