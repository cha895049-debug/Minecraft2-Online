import asyncio
import json
import random
import websockets

HOST = "0.0.0.0"
PORT = 8765
MAX_PLAYERS = 10

players = {}
clients = set()
world = {}

for x in range(30):
    for y in range(30):
        roll = random.random()
        if roll < 0.035:
            world[f"{x},{y}"] = "tree"
        elif roll < 0.05:
            world[f"{x},{y}"] = "stone"


def make_state():
    return {"type": "state", "players": players, "world": world}


async def broadcast():
    if clients:
        message = json.dumps(make_state())
        await asyncio.gather(
            *(client.send(message) for client in list(clients)),
            return_exceptions=True,
        )


async def game_server(ws, path=None):
    if len(clients) >= MAX_PLAYERS:
        await ws.send(json.dumps({"type": "full", "message": "World is full."}))
        await ws.close()
        return

    player_id = str(id(ws))
    players[player_id] = {
        "name": f"Player {len(players) + 1}",
        "x": random.randint(2, 27),
        "y": random.randint(2, 27),
        "facing": "down",
    }
    clients.add(ws)

    try:
        await ws.send(json.dumps({"type": "welcome", "id": player_id}))
        await broadcast()

        async for message in ws:
            try:
                data = json.loads(message)
            except (json.JSONDecodeError, TypeError):
                continue

            if not isinstance(data, dict):
                continue

            player = players.get(player_id)
            if player is None:
                continue

            action = data.get("action")
            if action == "move":
                direction = data.get("direction")
                moves = {
                    "up": (0, -1), "down": (0, 1),
                    "left": (-1, 0), "right": (1, 0),
                }
                if direction in moves:
                    dx, dy = moves[direction]
                    player["x"] = max(0, min(29, player["x"] + dx))
                    player["y"] = max(0, min(29, player["y"] + dy))
                    player["facing"] = direction

            elif action in ("place", "break"):
                directions = {
                    "up": (0, -1), "down": (0, 1),
                    "left": (-1, 0), "right": (1, 0),
                }
                dx, dy = directions.get(player.get("facing", "down"), (0, 1))
                bx, by = player["x"] + dx, player["y"] + dy
                key = f"{bx},{by}"
                if 0 <= bx < 30 and 0 <= by < 30:
                    if action == "place":
                        occupied = any(
                            p["x"] == bx and p["y"] == by
                            for p in players.values()
                        )
                        if not occupied:
                            world[key] = "dirt"
                    else:
                        world.pop(key, None)

            await broadcast()

    finally:
        clients.discard(ws)
        players.pop(player_id, None)
        await broadcast()


async def main():
    print(f"MINECRAFT 2.0 server listening on {HOST}:{PORT}")
    print(f"Maximum players: {MAX_PLAYERS}")
    async with websockets.serve(game_server, HOST, PORT, max_size=100000):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
