import argparse
import requests

# List the control endpoints for both server instances
SERVER_CONTROL_URLS = [
    "http://localhost:8000/control",
    "http://localhost:8001/control"
]

def send_command(url, command, pong_time_ms=None):
    data = {"command": command}
    if pong_time_ms is not None:
        data["pong_time_ms"] = pong_time_ms
    try:
        response = requests.post(url, json=data)
        print(f"Response from {url}: {response.json()}")
    except Exception as e:
        print(f"Error contacting {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Control the ping-pong game.")
    parser.add_argument("command", choices=["start", "pause", "resume", "stop"], help="Game command")
    parser.add_argument("pong_time_ms", nargs="?", type=int, help="Delay between pings in milliseconds (only for start)")
    args = parser.parse_args()
    
    for url in SERVER_CONTROL_URLS:
        if args.command == "start" and args.pong_time_ms is not None:
            send_command(url, args.command, args.pong_time_ms)
        else:
            send_command(url, args.command)

if __name__ == "__main__":
    main()
