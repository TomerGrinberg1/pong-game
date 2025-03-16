import os
import asyncio
import httpx
from fastapi import FastAPI, BackgroundTasks, Request
import socket
import uvicorn
import json
import time

app = FastAPI()

# Global game state variables
game_state = "stopped"  # Possible states: "running", "paused", "stopped"
pong_time_ms = 1000     # Default delay in milliseconds
global partner_url

def find_available_port():
    """
    Find an available port on the system.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def save_ports_to_json(initiator_port, responder_port):
    ports = {
        "initiator_port": str(initiator_port),
        "responder_port": str(responder_port)
    }
    with open("ports.json", "w") as f:
        json.dump(ports, f)
    print(f"Ports saved to JSON: {ports}")

def load_ports_from_json():
    with open("ports.json", "r") as f:
        ports = json.load(f)
    print(f"Ports loaded from JSON: {ports}")
    return ports

# These are configured per instance (e.g. via environment variables)
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
    retries = 5
    while retries > 0:
        await asyncio.sleep(0.1)  # brief delay to allow state change propagation
        async with httpx.AsyncClient() as client:
            try:
                await client.get(f"{partner_url}/ping")
                print("Initial ping sent successfully")
                return
            except Exception as e:
                print(f"Error sending initial ping: {e}")
                retries -= 1
                await asyncio.sleep(1)  # wait before retrying

def start_server():
    global partner_url
    if not os.path.exists("ports.json"):
        initiator_port = find_available_port()
        responder_port = find_available_port()
        save_ports_to_json(initiator_port, responder_port)

    
    ports = load_ports_from_json()
    partner_url = f"http://localhost:{ports['responder_port']}" if instance_role == "initiator" else f"http://localhost:{ports['initiator_port']}"
    port = int(ports['initiator_port']) if instance_role == "initiator" else int(ports['responder_port'])
 
    
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_server()