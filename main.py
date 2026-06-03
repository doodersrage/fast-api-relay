import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
import redis
import json

app = FastAPI()

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)


# Target API you are relaying to
UPSTREAM_URL = "http://192.168.12.111"

# Configuration: Allows 2 requests every 5 seconds
route_limit = Limiter(Rate(2, Duration.SECOND * 5))

@app.get("/", dependencies=[Depends(RateLimiter(limiter=route_limit))])
async def get_json_relay():
    cached_item = redis_client.get(UPSTREAM_URL)

    if cached_item:
        cached_item = json.loads(cached_item)

        # Return cached response if available
        return JSONResponse(content=cached_item)
    
    else:
        async with httpx.AsyncClient() as client:
            try:
                # Forward the GET request
                response = await client.get(UPSTREAM_URL)
                
                # Raise exception if upstream API fails
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Upstream error")
                    
                # Cache the response in Redis for future requests
                redis_client.setex(UPSTREAM_URL, 1300, json.dumps(response.json()))
                # Return the JSON data directly to the client
                return JSONResponse(content=response.json())
                
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Relay failed: {e}")

