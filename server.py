import os
import asyncio
import httpx
from fastapi import FastAPI, BackgroundTasks, Request
import json
app = FastAPI()

# Global game state variables
game_state = "stopped"  # Possible states: "running", "paused", "stopped"
pong_time_ms = 1000     # Default delay in milliseconds

STATE_FILE = "game_state.json"
MAX_RETRIES = 3  # Number of retry attempts before stopping
# These are configured per instance (e.g. via environment variables)
partner_url = os.environ.get("PARTNER_URL", "http://localhost:8001")
instance_role = os.environ.get("INSTANCE_ROLE", "initiator")  # "initiator" for instance1, "responder" for instance2

def load_game_state():
    global game_state, pong_time_ms
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            game_state = data.get("state", "stopped")
            pong_time_ms = data.get("pong_time_ms", 1000)

# Load state on startup
load_game_state()
def save_game_state():
    """Save the game state to a JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump({"state": game_state, "pong_time_ms": pong_time_ms}, f)

async def schedule_next_ping():
    """
    Wait for the specified delay and then send a ping to the partner server.
    Implements a retry mechanism if the request fails.
    """
    global game_state

    await asyncio.sleep(pong_time_ms / 1000.0)  # Wait before sending next ping

    if game_state == "running":
        retries = 0
        while retries < MAX_RETRIES:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{partner_url}/ping")
                    if response.status_code == 200:
                        return  # Ping was successful, exit function
                except Exception as e:
                    print(f"Error sending ping (Attempt {retries+1}/{MAX_RETRIES}): {e}")

            retries += 1
            await asyncio.sleep(1)  # Small delay before retrying

        # If all retries fail, stop the game
        print("Max retries reached. Stopping game.")
        game_state = "stopped"
        save_game_state()  # ✅ Update the JSON file when stopping


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




@app.post("/control")
async def control(request: Request):
    global game_state, pong_time_ms
    data = await request.json()
    command = data.get("command")

    if command == "start":
        pong_time_ms = data.get("pong_time_ms", pong_time_ms)
        game_state = "running"
        save_game_state()  # Save state
        if instance_role == "initiator":
            asyncio.create_task(send_initial_ping())

    elif command == "pause":
        if game_state == "running":
            game_state = "paused"
            save_game_state()

    elif command == "resume":
        if game_state == "paused":
            game_state = "running"
            save_game_state()
            if instance_role == "initiator":
                asyncio.create_task(send_initial_ping())

    elif command == "stop":
        game_state = "stopped"
        save_game_state()

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
