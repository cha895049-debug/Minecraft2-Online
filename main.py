import json
import threading
from pathlib import Path

import websocket
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.video import Video

# Replace with your reachable server address.
# Same Wi-Fi example: ws://192.168.1.100:8765
# Internet hosting should use a secure wss:// address.
SERVER_URL = "ws://192.168.1.100:8765"

PROJECT_DIR = Path(__file__).resolve().parent
BACKGROUND_VIDEO = PROJECT_DIR / "background.mp4"


class WorldView(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.35, 0.65, 0.25, 1)
            Rectangle(pos=self.pos, size=self.size)

            state = self.game.state
            if not state:
                return

            blocks = state.get("world", {})
            players = state.get("players", {})
            my_id = self.game.player_id
            me = players.get(my_id, {"x": 15, "y": 15})

            tile = min(self.width / 12, self.height / 10)
            if tile <= 0:
                return

            cols = int(self.width / tile) + 2
            rows = int(self.height / tile) + 2
            start_x = me["x"] - cols // 2
            start_y = me["y"] - rows // 2

            for key, block in blocks.items():
                try:
                    bx, by = map(int, key.split(","))
                except (ValueError, AttributeError):
                    continue

                sx = self.x + (bx - start_x) * tile
                sy = self.y + self.height - (by - start_y + 1) * tile

                if block == "tree":
                    Color(0.05, 0.35, 0.08, 1)
                elif block == "stone":
                    Color(0.5, 0.5, 0.5, 1)
                else:
                    Color(0.55, 0.35, 0.15, 1)
                Rectangle(pos=(sx, sy), size=(tile, tile))

            for pid, player in players.items():
                sx = self.x + (player["x"] - start_x) * tile
                sy = self.y + self.height - (player["y"] - start_y + 1) * tile
                if pid == my_id:
                    Color(0.1, 0.3, 1, 1)
                else:
                    Color(1, 0.2, 0.2, 1)
                Rectangle(
                    pos=(sx + tile * 0.12, sy + tile * 0.12),
                    size=(tile * 0.76, tile * 0.76),
                )


class Minecraft2App(App):
    def build(self):
        self.player_id = None
        self.state = {}
        self.socket = None
        self.send_lock = threading.Lock()
        self.root = FloatLayout()
        self.show_title_screen()
        return self.root

    def add_video_background(self, screen):
        # The video file must sit beside main.py and be named background.mp4.
        if BACKGROUND_VIDEO.is_file():
            try:
                video = Video(
                    source=str(BACKGROUND_VIDEO),
                    state="play",
                    options={"eos": "loop"},
                    volume=0,
                    allow_stretch=True,
                    keep_ratio=False,
                    size_hint=(1, 1),
                    pos_hint={"x": 0, "y": 0},
                )
                screen.add_widget(video, index=len(screen.children))
                self.background_video = video
            except Exception as error:
                print("Video could not start:", error)
                self.add_fallback_background(screen)
        else:
            self.add_fallback_background(screen)

        # Dark translucent layer helps the title and buttons remain readable.
        with screen.canvas.after:
            Color(0, 0, 0, 0.38)
            overlay = Rectangle(pos=screen.pos, size=screen.size)

        screen.bind(
            pos=lambda obj, value: setattr(overlay, "pos", value),
            size=lambda obj, value: setattr(overlay, "size", value),
        )

    def add_fallback_background(self, screen):
        with screen.canvas.before:
            Color(0.08, 0.16, 0.10, 1)
            bg = Rectangle(pos=screen.pos, size=screen.size)
        screen.bind(
            pos=lambda obj, value: setattr(bg, "pos", value),
            size=lambda obj, value: setattr(bg, "size", value),
        )

    def show_title_screen(self, *args):
        # Close an existing game connection when returning to the title screen.
        old_socket = self.socket
        self.socket = None
        if old_socket is not None:
            try:
                old_socket.close()
            except Exception as error:
                print("Socket close warning:", error)

        self.root.clear_widgets()
        self.add_video_background(self.root)

        content = BoxLayout(
            orientation="vertical",
            padding=24,
            spacing=12,
            size_hint=(0.9, 0.72),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        )

        content.add_widget(Widget())

        title = Label(
            text="[b]MINECRAFT 2.0[/b]",
            markup=True,
            font_size="38sp",
            color=(0.65, 1, 0.42, 1),
            size_hint_y=0.20,
        )
        content.add_widget(title)

        creator = Label(
            text="Created by Chandru",
            font_size="22sp",
            color=(1, 1, 1, 1),
            size_hint_y=0.12,
        )
        content.add_widget(creator)

        subtitle = Label(
            text="ONLINE BLOCK SURVIVAL",
            font_size="17sp",
            color=(0.9, 0.95, 0.85, 1),
            size_hint_y=0.12,
        )
        content.add_widget(subtitle)

        start = Button(
            text="PLAY ONLINE",
            font_size="22sp",
            size_hint=(0.8, 0.16),
            pos_hint={"center_x": 0.5},
            background_normal="",
            background_color=(0.12, 0.52, 0.18, 1),
        )
        start.bind(on_press=self.start_game)
        content.add_widget(start)

        content.add_widget(Widget())
        self.root.add_widget(content)

    def start_game(self, instance):
        self.state = {}
        self.player_id = None
        self.socket = None
        self.root.clear_widgets()
        self.add_video_background(self.root)

        layout = BoxLayout(
            orientation="vertical",
            spacing=5,
            padding=5,
        )

        self.status = Label(
            text="Connecting to Minecraft 2.0 server...",
            size_hint_y=0.09,
        )
        layout.add_widget(self.status)

        self.world_view = WorldView(self)
        layout.add_widget(self.world_view)

        controls = BoxLayout(
            orientation="vertical",
            size_hint_y=0.32,
            spacing=4,
        )

        row1 = BoxLayout(spacing=4)
        row1.add_widget(Widget())
        self.add_button(row1, "UP", lambda: self.move("up"))
        row1.add_widget(Widget())
        controls.add_widget(row1)

        row2 = BoxLayout(spacing=4)
        self.add_button(row2, "LEFT", lambda: self.move("left"))
        self.add_button(row2, "DOWN", lambda: self.move("down"))
        self.add_button(row2, "RIGHT", lambda: self.move("right"))
        controls.add_widget(row2)

        row3 = BoxLayout(spacing=4)
        self.add_button(row3, "BREAK", lambda: self.send_action("break"))
        self.add_button(row3, "PLACE", lambda: self.send_action("place"))
        self.add_button(row3, "MENU", self.show_title_screen)
        controls.add_widget(row3)

        layout.add_widget(controls)
        self.root.add_widget(layout)

        Clock.schedule_interval(self.world_view.redraw, 0.2)
        threading.Thread(target=self.connect_server, daemon=True).start()

    def add_button(self, layout, text, callback):
        button = Button(text=text)
        button.bind(on_press=lambda instance: callback())
        layout.add_widget(button)

    def connect_server(self):
        try:
            self.socket = websocket.WebSocketApp(
                SERVER_URL,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            self.socket.run_forever()
        except Exception as error:
            message = f"Connection error: {error}"
            Clock.schedule_once(
                lambda dt, msg=message: self.set_status(msg)
            )

    def on_open(self, ws):
        Clock.schedule_once(lambda dt: self.set_status("Connected! Waiting for world..."))

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if not isinstance(data, dict):
                return
            if data.get("type") == "welcome":
                self.player_id = data.get("id")
            elif data.get("type") == "full":
                Clock.schedule_once(lambda dt: self.set_status("Server is full!"))
            elif data.get("type") == "state":
                self.state = data
                count = len(data.get("players", {}))
                Clock.schedule_once(
                    lambda dt: self.set_status(f"Players online: {count}/10")
                )
        except (ValueError, TypeError, AttributeError) as error:
            print("Message error:", error)

    def on_error(self, ws, error):
        Clock.schedule_once(lambda dt: self.set_status(f"Network error: {error}"))

    def on_close(self, ws, code, message):
        Clock.schedule_once(lambda dt: self.set_status("Disconnected"))

    def set_status(self, message):
        if hasattr(self, "status"):
            self.status.text = message

    def send_action(self, action):
        self.send_message({"action": action})

    def send_message(self, data):
        sock = self.socket
        if not sock or not sock.sock or not sock.sock.connected:
            self.set_status("Not connected to server")
            return
        try:
            with self.send_lock:
                sock.send(json.dumps(data))
        except Exception as error:
            self.set_status(f"Send failed: {error}")

    def move(self, direction):
        self.send_message({"action": "move", "direction": direction})


if __name__ == "__main__":
    Minecraft2App().run()
