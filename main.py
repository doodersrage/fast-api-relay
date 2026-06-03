import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Target API you are relaying to
UPSTREAM_URL = "http://192.168.12.111"

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
