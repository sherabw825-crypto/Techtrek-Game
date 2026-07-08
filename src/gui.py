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


class SaveSlotView(arcade.View):
    """A clean, dark view dedicated to rendering save and load slots."""
    def __init__(self) -> None:
        super().__init__()
        # Lock camera to match the design grid
        self.camera = arcade.Camera2D()
        self.camera.projection = arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

    def on_draw(self) -> None:
        self.clear()
        
        # Hollow Knight-style deep dark background canvas
        arcade.set_background_color(Color(12, 12, 15))
        
        self.camera.use()
        
        # Placeholder text layer where you can start rendering your save slots
        arcade.draw_text(
            "[ Save / Load Slot Screen Active ]", 
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 
            Color(60, 64, 84), 
            font_size=18, 
            font_name="Trajan Pro", 
            anchor_x="center", anchor_y="center"
        )


class TechtrekWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        self.background_color = arcade.color.BLACK
        
        # Load textures once with hitboxes disabled
        self.background = arcade.load_texture(str(BACKGROUND_PATH), hit_box_algorithm=None) if BACKGROUND_PATH.exists() else None
        self.glow_texture = arcade.load_texture(str(GLOW_PATH), hit_box_algorithm=None) if GLOW_PATH.exists() else None
        self.logo_texture = arcade.load_texture(str(LOGO_PATH), hit_box_algorithm=None) if LOGO_PATH.exists() else None
        
        if not self.logo_texture:
            print(f"\n[WARNING] Logo image not found at: {LOGO_PATH}\n")

        # Background Audio Threading Setup
        self.audio_muted, self.volume = False, 0.5  
        self.bg_music = None
        self.music_player = None
        self.music_ready = False
        self.music_started = False
        
        threading.Thread(target=self._load_audio_async, daemon=True).start()
        
        self.mouse_x = self.mouse_y = 0
        self.runtime_width, self.runtime_height = SCREEN_WIDTH, SCREEN_HEIGHT
        self.current_state = "MAIN_MENU"  
        self.hovered_index = self.glow_current_index = -1
        self.glow_alpha, self.glow_time, self.fade_speed = 0.0, 0.0, 38.25 / 0.5  

        # UI Layout Map
        self.menus = {
            "MAIN_MENU": {
                "options": ["NEW GAME", "OPTIONS", "JOURNAL", "CREDITS", "QUIT"],
                "layout": {"width": 300, "height": 50, "left": 173, "start_y": 473, "spacing": 70, "size": 30.5}
            },
            "OPTIONS": {
                "options": ["GAME", "AUDIO", "VIDEO", "KEYBOARD", "BACK"],
                "layout": {"width": 350, "height": 45, "left": (SCREEN_WIDTH / 2) + 105, "start_y": 550, "spacing": 70, "size": 28}
            },
            "AUDIO_MENU": {
                "options": ["VOLUME UP", "VOLUME DOWN", "MUTE: OFF", "BACK"],
                "layout": {"width": 350, "height": 45, "left": (SCREEN_WIDTH / 2) + 105, "start_y": 460, "spacing": 70, "size": 26}
            }
        }

        # PERFORMANCE FIX: Pre-generate separate text objects for Normal and Hover states.
        self.text_groups = {}
        for state, config in self.menus.items():
            lay = config["layout"]
            self.text_groups[state] = []
            for index, option_text in enumerate(config["options"]):
                x_pos = lay["left"] + (lay["width"] / 2)
                y_pos = (lay["start_y"] - (index * lay["spacing"])) + (lay["height"] / 2)
                
                normal_text = arcade.Text(
                    option_text, x=x_pos, y=y_pos,
                    color=(105, 108, 128), font_size=lay["size"], font_name="Trajan Pro", bold=True,
                    anchor_x="center", anchor_y="center"
                )
                hovered_text = arcade.Text(
                    option_text, x=x_pos, y=y_pos,
                    color=arcade.color.WHITE, font_size=lay["size"], font_name="Trajan Pro", bold=True,
                    anchor_x="center", anchor_y="center"
                )
                
                approx_width = len(option_text) * (lay["size"] * 0.65)
                approx_height = lay["size"]

                self.text_groups[state].append({
                    "normal": normal_text,
                    "hovered": hovered_text,
                    "width": approx_width,
                    "height": approx_height
                })

        # Static text headers
        self.options_title = arcade.Text("OPTIONS", x=(SCREEN_WIDTH / 2) + 280, y=650, color=arcade.color.WHITE, font_size=38, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")
        self.audio_title = arcade.Text("AUDIO SETTINGS", x=(SCREEN_WIDTH / 2) + 280, y=650, color=arcade.color.WHITE, font_size=34, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")
        self.volume_display = arcade.Text(f"CURRENT VOLUME: {int(self.volume * 100)}%", x=(SCREEN_WIDTH / 2) + 280, y=560, color=arcade.color.WHITE, font_size=20, font_name="Trajan Pro", bold=True, anchor_x="center", anchor_y="center")

    def _load_audio_async(self) -> None:
        try:
            if MUSIC_PATH.exists():
                loaded_sound = arcade.load_sound(str(MUSIC_PATH))
                self.bg_music = loaded_sound
                self.music_ready = True
        except Exception:
            self.bg_music = None

    def on_resize(self, width: float, height: float) -> None:
        self.runtime_width, self.runtime_height = width, height

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x, self.mouse_y = x, y

    def on_update(self, delta_time: float) -> None:
        if self.music_ready and not self.music_started:
            self.music_started = True
            if self.bg_music:
                try:
                    self.music_player = arcade.play_sound(self.bg_music, volume=self.volume, loop=True)
                except Exception:
                    self.music_player = None

        self.glow_time += delta_time
        config = self.menus[self.current_state]
        lay = config["layout"]
        
        current_hover = -1
        for index in range(len(config["options"])):
            btn_bottom = lay["start_y"] - (index * lay["spacing"])
            if (lay["left"] <= self.mouse_x <= (lay["left"] + lay["width"]) and btn_bottom <= self.mouse_y <= (btn_bottom + lay["height"])):
                current_hover = index
                break
        
        self.hovered_index = current_hover

        if self.hovered_index != -1:
            if self.glow_current_index != self.hovered_index:
                self.glow_current_index, self.glow_alpha = self.hovered_index, 0.0
            target_alpha = 38.25
        else:
            target_alpha = 0    

        if self.glow_alpha < target_alpha:
            self.glow_alpha = min(target_alpha, self.glow_alpha + self.fade_speed * delta_time)
        elif self.glow_alpha > target_alpha:
            self.glow_alpha = max(target_alpha, self.glow_alpha - self.fade_speed * delta_time)
            if self.glow_alpha == 0:
                self.glow_current_index = -1

    def change_state(self, new_state: str) -> None:
        self.current_state, self.hovered_index, self.glow_current_index, self.glow_alpha = new_state, -1, -1, 0.0

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        config = self.menus[self.current_state]
        lay = config["layout"]
        
        for index, option_text in enumerate(config["options"]):
            btn_bottom = lay["start_y"] - (index * lay["spacing"])
            if (lay["left"] <= x <= (lay["left"] + lay["width"]) and btn_bottom <= y <= (btn_bottom + lay["height"])):
                if self.current_state == "MAIN_MENU":
                    if option_text == "NEW GAME":
                        # Triggers the dark layout view framework directly
                        self.show_view(SaveSlotView())
                    elif option_text == "OPTIONS": 
                        self.change_state("OPTIONS")
                    elif option_text == "QUIT": 
                        arcade.exit()
                elif self.current_state == "OPTIONS":
                    if option_text == "AUDIO": 
                        self.change_state("AUDIO_MENU")
                    elif option_text == "BACK": 
                        self.change_state("MAIN_MENU")
                elif self.current_state == "AUDIO_MENU":
                    if index == 0: self.volume = min(1.0, self.volume + 0.1)
                    elif index == 1: self.volume = max(0.0, self.volume - 0.1)
                    elif index == 2:
                        self.audio_muted = not self.audio_muted
                        new_text = "MUTE: ON" if self.audio_muted else "MUTE: OFF"
                        self.text_groups["AUDIO_MENU"][2]["normal"].text = new_text
                        self.text_groups["AUDIO_MENU"][2]["hovered"].text = new_text
                    elif option_text == "BACK": 
                        self.change_state("OPTIONS")
                    
                    if self.music_player: 
                        self.music_player.volume = 0.0 if self.audio_muted else self.volume
                    self.volume_display.text = f"CURRENT VOLUME: {int(self.volume * 100)}%"

    def on_draw(self) -> None:
        self.clear()
        
        # 1. Background Frame Setup
        if self.current_state == "MAIN_MENU" and self.background:
            arcade.draw_texture_rect(self.background, arcade.XYWH(self.runtime_width / 2, self.runtime_height / 2, self.runtime_width, self.runtime_height))

        active_text_list = self.text_groups[self.current_state]

        # 2. Draw Glow Effect
        if self.glow_texture and self.glow_alpha > 0 and self.glow_current_index != -1:
            target_data = active_text_list[self.glow_current_index]
            target_text = target_data["hovered"]
            pulse = math.sin(self.glow_time * 4.0) * 7.0    
            final_alpha = max(0, min(48, int(self.glow_alpha + math.sin(self.glow_time * 5.5) * 4.0)))
            arcade.draw_texture_rect(self.glow_texture, arcade.XYWH(target_text.x, target_text.y, target_data["width"] + 120 + pulse, target_data["height"] + 133 + (pulse * 0.5)), color=Color(255, 255, 255, final_alpha))

        # 3. Draw Mask Logo Anchor
        if self.logo_texture and self.hovered_index != -1:
            target_data = active_text_list[self.hovered_index]
            target_text = target_data["hovered"]
            arcade.draw_texture_rect(self.logo_texture, arcade.XYWH(target_text.x - (target_data["width"] / 2) - 65, target_text.y, 80, 80))
            
        # 4. Draw Header Decorations
        if self.current_state == "OPTIONS": self.options_title.draw()
        elif self.current_state == "AUDIO_MENU": self.audio_title.draw(); self.volume_display.draw()
        
        if self.current_state != "MAIN_MENU":
            arcade.draw_line(((SCREEN_WIDTH / 2) + 280) - 180, 630, ((SCREEN_WIDTH / 2) + 280) + 180, 630, Color(160, 165, 185, 150), 2)

        # 5. Draw Interactive Options Text
        for index, text_data in enumerate(active_text_list):
            if index == self.hovered_index:
                text_data["hovered"].draw()
            else:
                text_data["normal"].draw()


def main() -> None:
    TechtrekWindow()
    arcade.run()


if __name__ == "__main__":
    main()