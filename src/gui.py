import math
from pathlib import Path
import arcade
from arcade.types import Color

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "False Face"

# File paths for assets
BACKGROUND_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "GUI.jpg"
)
GLOW_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "glow.png"
)
MUSIC_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "sound" / "BC1.mp3"
)
LOGO_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "Selection_button_upscaled_upscaled.jpg"
)


class TechtrekWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color(arcade.color.BLACK)
        
        # Safely load background
        try:
            self.background = arcade.load_texture(str(BACKGROUND_PATH))
        except Exception:
            self.background = None

        # Safely load glow background
        try:
            self.glow_texture = arcade.load_texture(str(GLOW_PATH))
        except Exception:
            self.glow_texture = None

        # Safely load logo texture - handles missing asset cleanly
        if LOGO_PATH.exists():
            self.logo_texture = arcade.load_texture(str(LOGO_PATH))
        else:
            print(f"\n[WARNING] Logo image not found at: {LOGO_PATH}")
            print("Please check the file name or file extension (.jpg vs .png)!\n")
            self.logo_texture = None
            
        # Initialize background music tracking
        self.audio_muted = False
        self.volume = 0.5  
        try:
            self.bg_music = arcade.load_sound(str(MUSIC_PATH))
            self.music_player = arcade.play_sound(self.bg_music, volume=self.volume, loop=True)
        except Exception as e:
            print(f"Could not load music track: {e}")
            self.music_player = None
        
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.runtime_width = SCREEN_WIDTH
        self.runtime_height = SCREEN_HEIGHT
        
        self.current_state = "MAIN_MENU"  
        
        self.menu_options = ["NEW GAME", "OPTIONS", "JOURNAL", "CREDITS", "QUIT"]
        self.option_options = ["GAME", "AUDIO", "VIDEO", "KEYBOARD", "BACK"]
        self.audio_options = ["VOLUME UP", "VOLUME DOWN", "MUTE: OFF", "BACK"]
        
        # Main Menu layout configuration 
        self.main_btn_width = 300          
        self.main_btn_height = 50          
        self.main_btn_left = 173           
        self.main_start_y = 473   
        self.main_y_spacing = 70           

        # Options layout tracking coordinates
        self.opt_btn_width = 350
        self.opt_btn_height = 45
        self.opt_btn_left = ((SCREEN_WIDTH / 2) - (self.opt_btn_width / 2)) + 280
        self.opt_start_y = 550
        self.opt_y_spacing = 70

        # Sub-Audio Layout Coordinates
        self.audio_start_y = 460

        self.hovered_index = -1

        # Opacity Fade & Mask Aura Animation Variables
        self.glow_alpha = 0.0
        self.glow_current_index = -1
        self.fade_speed = 38.25 / 0.5  
        self.glow_time = 0.0         

        # Pre-create Main Menu Text Objects
        self.text_objects = []
        for index, option_text in enumerate(self.menu_options):
            center_x = self.main_btn_left + (self.main_btn_width / 2)
            current_btn_bottom = self.main_start_y - (index * self.main_y_spacing)
            center_y = current_btn_bottom + (self.main_btn_height / 2)
            
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  
                font_size=30.5, 
                font_name="Trajan Pro",
                bold=True,
                anchor_x="center",
                anchor_y="center",
            )
            self.text_objects.append(text_obj)

        # Options title logo text
        self.options_title_text = arcade.Text(
            "OPTIONS",
            x=(SCREEN_WIDTH / 2) + 280,
            y=650,
            color=arcade.color.WHITE,
            font_size=38,
            font_name="Trajan Pro",
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

        # Pre-create Options Menu Text Objects
        self.options_text_objects = []
        for index, option_text in enumerate(self.option_options):
            center_x = self.opt_btn_left + (self.opt_btn_width / 2)
            current_btn_bottom = self.opt_start_y - (index * self.opt_y_spacing)
            center_y = current_btn_bottom + (self.opt_btn_height / 2)
            
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  
                font_size=28, 
                font_name="Trajan Pro",
                bold=True,
                anchor_x="center",
                anchor_y="center",
            )
            self.options_text_objects.append(text_obj)

        # Pre-create Audio Menu Title Text
        self.audio_title_text = arcade.Text(
            "AUDIO SETTINGS",
            x=(SCREEN_WIDTH / 2) + 280,
            y=650,
            color=arcade.color.WHITE,
            font_size=34,
            font_name="Trajan Pro",
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

        # Dynamic live volume percentage readout indicator text
        self.volume_display_text = arcade.Text(
            f"CURRENT VOLUME: {int(self.volume * 100)}%",
            x=(SCREEN_WIDTH / 2) + 280,
            y=560,
            color=arcade.color.WHITE,
            font_size=20,
            font_name="Trajan Pro",
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

        # Pre-create Audio Menu Sub-state Text Objects
        self.audio_text_objects = []
        for index, option_text in enumerate(self.audio_options):
            center_x = self.opt_btn_left + (self.opt_btn_width / 2)
            current_btn_bottom = self.audio_start_y - (index * self.opt_y_spacing)
            center_y = current_btn_bottom + (self.opt_btn_height / 2)
            
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  
                font_size=26, 
                font_name="Trajan Pro",
                bold=True,
                anchor_x="center",
                anchor_y="center",
            )
            self.audio_text_objects.append(text_obj)

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        self.runtime_width = width
        self.runtime_height = height

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_update(self, delta_time: float) -> None:
        self.glow_time += delta_time

        if self.current_state == "MAIN_MENU":
            active_list = self.menu_options
            btn_left = self.main_btn_left
            btn_width = self.main_btn_width
            start_y = self.main_start_y
            y_spacing = self.main_y_spacing
            btn_height = self.main_btn_height
        elif self.current_state == "OPTIONS":
            active_list = self.option_options
            btn_left = self.opt_btn_left
            btn_width = self.opt_btn_width
            start_y = self.opt_start_y
            y_spacing = self.opt_y_spacing
            btn_height = self.opt_btn_height
        else:  
            active_list = self.audio_options
            btn_left = self.opt_btn_left
            btn_width = self.opt_btn_width
            start_y = self.audio_start_y
            y_spacing = self.opt_y_spacing
            btn_height = self.opt_btn_height
        
        current_hover = -1
        for index in range(len(active_list)):
            current_btn_bottom = start_y - (index * y_spacing)
            
            if (btn_left <= self.mouse_x <= (btn_left + btn_width) and
                current_btn_bottom <= self.mouse_y <= (current_btn_bottom + btn_height)):
                current_hover = index
                break
        
        self.hovered_index = current_hover

        if self.hovered_index != -1:
            if self.glow_current_index != self.hovered_index:
                self.glow_current_index = self.hovered_index
                self.glow_alpha = 0.0  
            target_alpha = 38.25  
        else:
            target_alpha = 0    

        if self.glow_alpha < target_alpha:
            self.glow_alpha = min(target_alpha, self.glow_alpha + self.fade_speed * delta_time)
        elif self.glow_alpha > target_alpha:
            self.glow_alpha = max(target_alpha, self.glow_alpha - self.fade_speed * delta_time)
            if self.glow_alpha == 0:
                self.glow_current_index = -1

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.current_state == "MAIN_MENU":
            for index, option_text in enumerate(self.menu_options):
                current_btn_bottom = self.main_start_y - (index * self.main_y_spacing)
                
                if (self.main_btn_left <= x <= (self.main_btn_left + self.main_btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.main_btn_height)):
                    
                    if option_text == "OPTIONS":
                        self.current_state = "OPTIONS"
                        self.hovered_index = -1
                        self.glow_current_index = -1
                        self.glow_alpha = 0.0
                    elif option_text == "QUIT":
                        arcade.exit()  
                        
        elif self.current_state == "OPTIONS":
            for index, option_text in enumerate(self.option_options):
                current_btn_bottom = self.opt_start_y - (index * self.opt_y_spacing)
                
                if (self.opt_btn_left <= x <= (self.opt_btn_left + self.opt_btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.opt_btn_height)):
                    
                    if option_text == "AUDIO":
                        self.current_state = "AUDIO_MENU"
                        self.hovered_index = -1
                        self.glow_current_index = -1
                        self.glow_alpha = 0.0
                    elif option_text == "BACK":
                        self.current_state = "MAIN_MENU"
                        self.hovered_index = -1
                        self.glow_current_index = -1
                        self.glow_alpha = 0.0

        elif self.current_state == "AUDIO_MENU":
            for index, option_text in enumerate(self.audio_options):
                current_btn_bottom = self.audio_start_y - (index * self.opt_y_spacing)
                
                if (self.opt_btn_left <= x <= (self.opt_btn_left + self.opt_btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.opt_btn_height)):
                    
                    if index == 0:  # VOLUME UP
                        self.volume = min(1.0, self.volume + 0.1)
                        if self.music_player and not self.audio_muted:
                            self.music_player.volume = self.volume
                    elif index == 1:  # VOLUME DOWN
                        self.volume = max(0.0, self.volume - 0.1)
                        if self.music_player and not self.audio_muted:
                            self.music_player.volume = self.volume
                    elif index == 2:  # TOGGLE MUTE
                        self.audio_muted = not self.audio_muted
                        self.audio_text_objects[2].text = "MUTE: ON" if self.audio_muted else "MUTE: OFF"
                        if self.music_player:
                            self.music_player.volume = 0.0 if self.audio_muted else self.volume
                    elif option_text == "BACK":
                        self.current_state = "OPTIONS"
                        self.hovered_index = -1
                        self.glow_current_index = -1
                        self.glow_alpha = 0.0
                    
                    self.volume_display_text.text = f"CURRENT VOLUME: {int(self.volume * 100)}%"

    def on_draw(self) -> None:
        self.clear()
        
        # 1. Background Layer
        if self.current_state == "MAIN_MENU" and self.background:
            arcade.draw_texture_rect(
                texture=self.background,
                rect=arcade.XYWH(self.runtime_width / 2, self.runtime_height / 2, self.runtime_width, self.runtime_height)
            )

        # 2. Soft-Pointed Oval Image Blend Layer (Glow background)
        if self.glow_texture and self.glow_alpha > 0 and self.glow_current_index != -1:
            pulse_size = math.sin(self.glow_time * 4.0) * 7.0    
            pulse_shimmer = math.sin(self.glow_time * 5.5) * 4.0 

            if self.current_state == "MAIN_MENU":
                target_text = self.text_objects[self.glow_current_index]
            elif self.current_state == "OPTIONS":
                target_text = self.options_text_objects[self.glow_current_index]
            else:
                target_text = self.audio_text_objects[self.glow_current_index]

            glow_x = target_text.x
            glow_y = target_text.y
            glow_w = target_text.content_width + 120 + pulse_size       
            glow_h = target_text.content_height + 133 + (pulse_size * 0.5) 

            final_alpha = max(0, min(48, int(self.glow_alpha + pulse_shimmer)))

            arcade.draw_texture_rect(
                texture=self.glow_texture,
                rect=arcade.XYWH(glow_x, glow_y, glow_w, glow_h),
                color=Color(255, 255, 255, final_alpha)
            )

        # 3. Selection Logo Layer – Perfectly matches the glow aura's scaling, alpha values, and time values
        if self.logo_texture and self.glow_alpha > 0 and self.glow_current_index != -1:
            pulse_size = math.sin(self.glow_time * 4.0) * 7.0    
            pulse_shimmer = math.sin(self.glow_time * 5.5) * 4.0 

            if self.current_state == "MAIN_MENU":
                target_text = self.text_objects[self.glow_current_index]
            elif self.current_state == "OPTIONS":
                target_text = self.options_text_objects[self.glow_current_index]
            else:
                target_text = self.audio_text_objects[self.glow_current_index]

            # Matching size logic exactly, but clamped to a standard button-logo aspect ratio format
            logo_w = 40 + (pulse_size * 0.2)
            logo_h = 40 + (pulse_size * 0.2)
            
            # Anchor positioning cleanly to the left side bounds of the targeted button
            logo_x = target_text.x - (target_text.content_width / 2) - 45
            logo_y = target_text.y

            # Pulls the exact fade-in calculation and dynamic shimmer used above
            final_alpha = max(0, min(255, int((self.glow_alpha / 38.25) * 255 + pulse_shimmer)))

            arcade.draw_texture_rect(
                texture=self.logo_texture,
                rect=arcade.XYWH(logo_x, logo_y, logo_w, logo_h),
                color=Color(255, 255, 255, final_alpha)
            )
            
        # 4. Interactive Text Elements (Top Layer)
        if self.current_state == "MAIN_MENU":
            for index, text_obj in enumerate(self.text_objects):
                if index == self.hovered_index:
                    text_obj.color = arcade.color.WHITE
                else:
                    text_obj.color = (105, 108, 128)
                text_obj.draw()
                
        elif self.current_state == "OPTIONS":
            self.options_title_text.draw()
            
            arcade.draw_line(
                start_x=((SCREEN_WIDTH / 2) + 280) - 180,
                start_y=630,
                end_x=((SCREEN_WIDTH / 2) + 280) + 180,
                end_y=630,
                color=Color(160, 165, 185, 150),
                line_width=2
            )
            
            for index, text_obj in enumerate(self.options_text_objects):
                if index == self.hovered_index:
                    text_obj.color = arcade.color.WHITE
                else:
                    text_obj.color = (105, 108, 128)
                text_obj.draw()

        elif self.current_state == "AUDIO_MENU":
            self.audio_title_text.draw()
            self.volume_display_text.draw()
            
            arcade.draw_line(
                start_x=((SCREEN_WIDTH / 2) + 280) - 180,
                start_y=630,
                end_x=((SCREEN_WIDTH / 2) + 280) + 180,
                end_y=630,
                color=Color(160, 165, 185, 150),
                line_width=2
            )
            
            for index, text_obj in enumerate(self.audio_text_objects):
                if index == self.hovered_index:
                    text_obj.color = arcade.color.WHITE
                else:
                    text_obj.color = (105, 108, 128)
                text_obj.draw()


def main() -> None:
    window = TechtrekWindow()
    arcade.run()


if __name__ == "__main__":
    main()