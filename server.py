import os
import asyncio
import httpx
from fastapi import FastAPI, BackgroundTasks, Request

app = FastAPI()

# Global game state variables
game_state = "stopped"  # Possible states: "running", "paused", "stopped"
pong_time_ms = 1000     # Default delay in milliseconds

# These are configured per instance (e.g. via environment variables)
partner_url = os.environ.get("PARTNER_URL", "http://localhost:8001")
instance_role = os.environ.get("INSTANCE_ROLE", "initiator")  # "initiator" for instance1, "responder" for instance2

@app.get("/ping")
async def ping(background_tasks: BackgroundTasks):
    """
    When a ping request is received, reply with 'pong' and (if running) schedule the next ping.
    """
    response = {"message": "pong"}
    if game_state == "running":
        # Schedule the next ping after the delay
        background_tasks.add_task(schedule_next_ping)
    return response

async def schedule_next_ping():
    """
    Wait for the specified delay and then send a ping to the partner server.
    """
    global game_state, pong_time_ms
    await asyncio.sleep(pong_time_ms / 1000.0)
    if game_state == "running":
        async with httpx.AsyncClient() as client:
            try:
                await client.get(f"{partner_url}/ping")
            except Exception as e:
                print(f"Error sending ping: {e}")

@app.post("/control")
async def control(request: Request):
    """
    Control endpoint to start, pause, resume, or stop the game.
    """
    global game_state, pong_time_ms
    data = await request.json()
    command = data.get("command")
    
    if command == "start":
        pong_time_ms = data.get("pong_time_ms", pong_time_ms)
        game_state = "running"
        # If this is the initiator, trigger the first ping.
        if instance_role == "initiator":
            asyncio.create_task(send_initial_ping())
    elif command == "pause":
        if game_state == "running":
            game_state = "paused"
    elif command == "resume":
        if game_state == "paused":
            game_state = "running"
            # For the initiator, resume by sending a ping to restart the cycle.
            if instance_role == "initiator":
                asyncio.create_task(send_initial_ping())
    elif command == "stop":
        game_state = "stopped"
    else:
        return {"error": "Invalid command"}
    
    return {"status": "ok", "state": game_state}

async def send_initial_ping():
    """
    For starting/resuming the game, the initiator sends the first ping.
    """
    await asyncio.sleep(0.1)  # brief delay to allow state change propagation
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{partner_url}/ping")
        except Exception as e:
            print(f"Error sending initial ping: {e}")
