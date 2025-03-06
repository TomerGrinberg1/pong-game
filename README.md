# Pong Game using FastAPI and CLI Tool

## Overview
This project implements a simple ping-pong game between two FastAPI servers. The servers communicate via HTTP requests to simulate a pong game. One server (the "initiator") starts by sending a ping, while the other (the "responder") replies with a pong. After each ping, the server waits for a specified delay (in milliseconds) before sending the next ping back to its partner. A CLI tool is provided to control the game with commands to start, pause, resume, and stop the ping-pong cycle.

## Project Structure
- **server.py**: FastAPI server code that handles the ping-pong logic and control commands.
- **pong_cli.py**: CLI tool to send control commands to both server instances.
- **README.md**: This file.

## Requirements
- Python 3.7+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/) (for running the server)
- [httpx](https://www.python-httpx.org/) (for asynchronous HTTP requests)
- [Requests](https://docs.python-requests.org/) (for the CLI tool)

Install the required packages using pip:

```bash
pip install -r requirements.txt
```


## Setup and Running the Project
### Running the Servers
You need to run two instances of the server with different roles and partner URLs. Open two terminal windows or tabs:

Instance 1 (Initiator):
```bash
INSTANCE_ROLE=initiator PARTNER_URL=http://localhost:8001 uvicorn server:app --host 0.0.0.0 --port 8000
```
Instance 2 (Responder):
```bash
INSTANCE_ROLE=responder PARTNER_URL=http://localhost:8000 uvicorn server:app --host 0.0.0.0 --port 8001
```

### Using the CLI Tool
The CLI tool (pong_cli.py) controls the game by sending HTTP POST requests to both server instances.

#### Commands
- Start the Game:

```bash
python pong_cli.py start 1000
```
This starts the game with a 1-second (1000 ms) interval between pings.

- Pause the Game:

```bash
python pong_cli.py pause
```
- Resume the Game:
```bash
python pong_cli.py resume
```
- Stop the Game:
```bash
python pong_cli.py stop
```
## How It Works
- Ping-Pong Cycle:
When the game starts, the initiator server sends a ping to the responder's /ping endpoint. Upon receiving the ping, the responder replies with "pong" and schedules the next ping after the defined delay. This back-and-forth continues as long as the game is in the "running" state.

- Game Control:
The /control endpoint on each server accepts commands to start, pause, resume, or stop the game. When paused or stopped, the servers halt scheduling new pings. Resuming restarts the ping cycle.

- Delayed Tasks:
Asynchronous tasks (using asyncio) manage the delay between pings, ensuring the game operates on the specified pong_time_ms interval.

