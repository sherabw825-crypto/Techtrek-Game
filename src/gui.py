import math
import threading
from pathlib import Path
import arcade
from arcade.types import Color

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
SCREEN_TITLE = "False Face"

BASE_PATH = Path(__file__).resolve().parent.parent / "assets"
BACKGROUND_PATH = BASE_PATH / "images" / "GUI.jpg"
GLOW_PATH = BASE_PATH / "images" / "glow.png"
MUSIC_PATH = BASE_PATH / "sound" / "BC1.mp3"
LOGO_PATH = BASE_PATH / "images" / "mask.jpg"


class GameStartView(arcade.View):
    """View shown after selecting a save slot, featuring a single START GAME button."""
    def __init__(self, slot_number: int) -> None:
        super().__init__()
        self.slot_number = slot_number
        self.camera = arcade.Camera2D()
        self.camera.projection = arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

        self.center_x = SCREEN_WIDTH / 2
        self.btn_w, self.btn_h = 280, 60
        self.btn_y = SCREEN_HEIGHT / 2 - 20
        self.btn_hovered = False

        self.title_text = arcade.Text(
            f"VESSEL {self.slot_number} PREPARED",
            x=self.center_x, y=SCREEN_HEIGHT / 2 + 100,
            color=Color(210, 215, 220), font_size=26, font_name="Trajan Pro", bold=True,
            anchor_x="center", anchor_y="center"
        )
        self.start_text_norm = arcade.Text(
            "START GAME", x=self.center_x, y=self.btn_y,
            color=Color(160, 165, 180), font_size=20, font_name="Trajan Pro", bold=True,
            anchor_x="center", anchor_y="center"
        )
        self.start_text_hover = arcade.Text(
            "START GAME", x=self.center_x, y=self.btn_y,
            color=arcade.color.WHITE, font_size=20, font_name="Trajan Pro", bold=True,
            anchor_x="center", anchor_y="center"
        )

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.btn_hovered = (
            self.center_x - self.btn_w / 2 <= x <= self.center_x + self.btn_w / 2 and
            self.btn_y - self.btn_h / 2 <= y <= self.btn_y + self.btn_h / 2
        )

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.btn_hovered:
            print(f"Launching gameplay for Save Slot {self.slot_number}...")

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(Color(12, 14, 18))
        self.camera.use()

        self.title_text.draw()

        btn_bg = Color(40, 45, 55) if self.btn_hovered else Color(20, 22, 28)
        btn_border = Color(230, 160, 50) if self.btn_hovered else Color(80, 85, 100)

        arcade.draw_rect_filled(arcade.XYWH(self.center_x, self.btn_y, self.btn_w, self.btn_h), btn_bg)
        arcade.draw_rect_outline(arcade.XYWH(self.center_x, self.btn_y, self.btn_w, self.btn_h), btn_border, border_width=2)

        (self.start_text_hover if self.btn_hovered else self.start_text_norm).draw()


class SaveSlotView(arcade.View):
    """Save & Load Slot Selection View."""
    def __init__(self) -> None:
        super().__init__()
        self.camera = arcade.Camera2D()
        self.camera.projection = arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

        self.hovered_slot = -1
        self.create_btn_hovered = self.back_hovered = False

        self.center_x = SCREEN_WIDTH / 2
        self.slot_w, self.slot_h, self.start_y, self.spacing = 520, 80, 440, 95

        self.save_slots = [
            {"active": True, "title": "[ SLOT 1 ]", "sub": "Cham: Mahakala | Paro Dzong - Day 1", "time": "Playtime: 00:45:12"},
            {"active": False, "title": "[ EMPTY NICHE ]", "sub": "Awaiting the Dance...", "time": ""},
            {"active": False, "title": "[ EMPTY NICHE ]", "sub": "Awaiting the Dance...", "time": ""},
            {"active": False, "title": "[ EMPTY NICHE ]", "sub": "Awaiting the Dance...", "time": ""}
        ]

        self.back_norm = arcade.Text("BACK", x=self.center_x, y=40, color=Color(105, 108, 128), font_size=22, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")
        self.back_hover = arcade.Text("BACK", x=self.center_x, y=40, color=arcade.color.WHITE, font_size=22, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.create_btn_hovered = (self.center_x - 130 <= x <= self.center_x + 130 and 500 <= y <= 535)
        self.back_hovered = (self.center_x - 50 <= x <= self.center_x + 50 and 25 <= y <= 55)

        self.hovered_slot = -1
        for i in range(4):
            sy = self.start_y - (i * self.spacing)
            if (self.center_x - self.slot_w / 2 <= x <= self.center_x + self.slot_w / 2) and (sy - self.slot_h / 2 <= y <= sy + self.slot_h / 2):
                self.hovered_slot = i
                break

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.create_btn_hovered:
            for i, slot in enumerate(self.save_slots):
                if not slot["active"]:
                    slot.update({"active": True, "title": f"[ SLOT {i + 1} ]", "sub": "Cham: Uncarved Mask | Monastery Gate", "time": "Playtime: 00:00:00"})
                    break
        elif self.hovered_slot != -1:
            slot = self.save_slots[self.hovered_slot]
            if not slot["active"]:
                slot.update({"active": True, "title": f"[ SLOT {self.hovered_slot + 1} ]", "sub": "Cham: Uncarved Mask | Monastery Gate", "time": "Playtime: 00:00:00"})
            
            # Transition to single START GAME button menu
            self.window.show_view(GameStartView(self.hovered_slot + 1))

        elif self.back_hovered:
            # Return to main window view mode
            self.window.show_view(MainMenuView())

    def on_draw(self) -> None:
        self.clear()
        arcade.set_background_color(Color(12, 14, 18))
        self.camera.use()

        arcade.draw_text("VESSEL SELECTION", self.center_x, 565, Color(210, 215, 220), font_size=24, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")

        # Create Button
        c_bg = Color(40, 45, 55) if self.create_btn_hovered else Color(20, 22, 28)
        c_border = Color(230, 160, 50) if self.create_btn_hovered else Color(80, 85, 100)
        c_text = arcade.color.WHITE if self.create_btn_hovered else Color(160, 165, 180)

        arcade.draw_rect_filled(arcade.XYWH(self.center_x, 517, 260, 32), c_bg)
        arcade.draw_rect_outline(arcade.XYWH(self.center_x, 517, 260, 32), c_border, border_width=1)
        arcade.draw_text("+ CREATE NEW SAVE", self.center_x, 517, c_text, font_size=13, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")

        # Save Slots
        for i, slot in enumerate(self.save_slots):
            sy = self.start_y - (i * self.spacing)
            hover = (self.hovered_slot == i)

            arcade.draw_rect_filled(arcade.XYWH(self.center_x, sy, self.slot_w, self.slot_h), Color(24, 26, 32) if hover else Color(18, 20, 24))
            arcade.draw_rect_outline(arcade.XYWH(self.center_x, sy, self.slot_w, self.slot_h), Color(230, 160, 50, 220) if hover else Color(50, 55, 65, 180), border_width=2)

            arcade.draw_text(slot["title"], self.center_x, sy + 16, arcade.color.WHITE if hover else Color(160, 165, 180), font_size=16, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")
            arcade.draw_text(slot["sub"], self.center_x, sy - 8, Color(110, 115, 130), font_size=12, font_name="Trajan Pro", anchor_x="center", anchor_y="center")
            if slot["active"]:
                arcade.draw_text(slot["time"], self.center_x, sy - 25, Color(180, 140, 60), font_size=10, font_name="Trajan Pro", anchor_x="center", anchor_y="center")

        (self.back_hover if self.back_hovered else self.back_norm).draw()


class MainMenuView(arcade.View):
    """Main Application View."""
    def __init__(self) -> None:
        super().__init__()
        self.background = arcade.load_texture(str(BACKGROUND_PATH)) if BACKGROUND_PATH.exists() else None
        self.glow_texture = arcade.load_texture(str(GLOW_PATH)) if GLOW_PATH.exists() else None
        self.logo_texture = arcade.load_texture(str(LOGO_PATH)) if LOGO_PATH.exists() else None

        self.mouse_x = self.mouse_y = 0
        self.current_state = "MAIN_MENU"
        self.hovered_index = self.glow_current_index = -1
        self.glow_alpha, self.glow_time = 0.0, 0.0

        self.menus = {
            "MAIN_MENU": {"options": ["NEW GAME", "OPTIONS", "JOURNAL", "CREDITS", "QUIT"], "layout": {"w": 300, "h": 50, "left": 173, "start_y": 473, "spacing": 70, "size": 30.5}},
            "OPTIONS": {"options": ["GAME", "AUDIO", "VIDEO", "KEYBOARD", "BACK"], "layout": {"w": 350, "h": 45, "left": SCREEN_WIDTH / 2 + 105, "start_y": 550, "spacing": 70, "size": 28}},
            "AUDIO_MENU": {"options": ["VOLUME UP", "VOLUME DOWN", "MUTE: OFF", "BACK"], "layout": {"w": 350, "h": 45, "left": SCREEN_WIDTH / 2 + 105, "start_y": 460, "spacing": 70, "size": 26}}
        }

        self.text_groups = {}
        for state, cfg in self.menus.items():
            lay = cfg["layout"]
            self.text_groups[state] = []
            for i, opt in enumerate(cfg["options"]):
                x, y = lay["left"] + (lay["w"] / 2), (lay["start_y"] - (i * lay["spacing"])) + (lay["h"] / 2)
                self.text_groups[state].append({
                    "normal": arcade.Text(opt, x=x, y=y, color=(105, 108, 128), font_size=lay["size"], font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center"),
                    "hovered": arcade.Text(opt, x=x, y=y, color=arcade.color.WHITE, font_size=lay["size"], font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center"),
                    "bounds": (lay["left"], lay["left"] + lay["w"], lay["start_y"] - (i * lay["spacing"]), lay["start_y"] - (i * lay["spacing"]) + lay["h"]),
                    "w": len(opt) * (lay["size"] * 0.65), "h": lay["size"]
                })

        self.options_title = arcade.Text("OPTIONS", x=SCREEN_WIDTH / 2 + 280, y=650, color=arcade.color.WHITE, font_size=38, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")
        self.audio_title = arcade.Text("AUDIO SETTINGS", x=SCREEN_WIDTH / 2 + 280, y=650, color=arcade.color.WHITE, font_size=34, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x, self.mouse_y = x, y

    def on_update(self, delta_time: float) -> None:
        self.glow_time += delta_time
        active_items = self.text_groups[self.current_state]

        self.hovered_index = -1
        for i, item in enumerate(active_items):
            l, r, b, t = item["bounds"]
            if l <= self.mouse_x <= r and b <= self.mouse_y <= t:
                self.hovered_index = i
                break

        target_alpha = 38.25 if self.hovered_index != -1 else 0
        if self.glow_current_index != self.hovered_index and self.hovered_index != -1:
            self.glow_current_index, self.glow_alpha = self.hovered_index, 0.0

        step = (38.25 / 0.5) * delta_time
        self.glow_alpha = min(target_alpha, self.glow_alpha + step) if self.glow_alpha < target_alpha else max(target_alpha, self.glow_alpha - step)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.hovered_index == -1:
            return

        opt = self.menus[self.current_state]["options"][self.hovered_index]
        if self.current_state == "MAIN_MENU":
            if opt == "NEW GAME":
                # Explicit View Transition
                self.window.show_view(SaveSlotView())
            elif opt == "OPTIONS":
                self.current_state = "OPTIONS"
            elif opt == "QUIT":
                arcade.exit()
        elif self.current_state == "OPTIONS":
            if opt == "AUDIO":
                self.current_state = "AUDIO_MENU"
            elif opt == "BACK":
                self.current_state = "MAIN_MENU"
        elif self.current_state == "AUDIO_MENU":
            if opt == "BACK":
                self.current_state = "OPTIONS"

    def on_draw(self) -> None:
        self.clear()
        if self.current_state == "MAIN_MENU" and self.background:
            arcade.draw_texture_rect(self.background, arcade.XYWH(self.window.width / 2, self.window.height / 2, self.window.width, self.window.height))

        active_items = self.text_groups[self.current_state]

        if self.glow_texture and self.glow_alpha > 0 and self.glow_current_index != -1:
            target = active_items[self.glow_current_index]
            pulse = math.sin(self.glow_time * 4.0) * 7.0
            arcade.draw_texture_rect(self.glow_texture, arcade.XYWH(target["hovered"].x, target["hovered"].y, target["w"] + 120 + pulse, target["h"] + 133 + (pulse * 0.5)), color=Color(255, 255, 255, max(0, min(48, int(self.glow_alpha)))))

        if self.logo_texture and self.hovered_index != -1:
            target = active_items[self.hovered_index]
            arcade.draw_texture_rect(self.logo_texture, arcade.XYWH(target["hovered"].x - (target["w"] / 2) - 65, target["hovered"].y, 80, 80))

        if self.current_state == "OPTIONS":
            self.options_title.draw()
        elif self.current_state == "AUDIO_MENU":
            self.audio_title.draw()

        if self.current_state != "MAIN_MENU":
            arcade.draw_line(SCREEN_WIDTH / 2 + 100, 630, SCREEN_WIDTH / 2 + 460, 630, Color(160, 165, 185, 150), 2)

        for i, item in enumerate(active_items):
            (item["hovered"] if i == self.hovered_index else item["normal"]).draw()


def main() -> None:
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
    window.show_view(MainMenuView())
    arcade.run()


if __name__ == "__main__":
    main()