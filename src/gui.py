from pathlib import Path
import arcade
from arcade.types import LBWH


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "False Face"

BACKGROUND_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "GUI.jpg"
)


class TechtrekWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color((22, 22, 30))
        self.background = arcade.load_texture(str(BACKGROUND_PATH))
        
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.audio_muted = False
        self.current_state = "MAIN_MENU"  
        
        self.menu_options = [
            "CONTINUE",
            "NEW GAME",
            "OPTIONS",
            "JOURNAL",
            "CREDITS",
            "QUIT"
        ]
        
        self.option_options = [
            "AUDIO: UNMUTED",
            "BACK"
        ]
        
        self.btn_width = 360          
        self.btn_height = 50          
        self.btn_left = 75            
        self.start_y_position = 430   
        self.y_spacing = 60           

        self.hovered_index = -1

        # Pre-create Main Menu Text
        self.text_objects = []
        for index, option_text in enumerate(self.menu_options):
            center_x = self.btn_left + (self.btn_width / 2)
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            center_y = current_btn_bottom + (self.btn_height / 2)
            
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  
                font_size=21,
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
            )
            self.text_objects.append(text_obj)

        # Pre-create Options Menu Text
        self.options_text_objects = []
        for index, option_text in enumerate(self.option_options):
            center_x = self.btn_left + (self.btn_width / 2)
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            center_y = current_btn_bottom + (self.btn_height / 2)
            
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  
                font_size=21,
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
            )
            self.options_text_objects.append(text_obj)

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_update(self, delta_time: float) -> None:
        active_list = self.menu_options if self.current_state == "MAIN_MENU" else self.option_options
        
        current_hover = -1
        for index in range(len(active_list)):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            
            if (self.btn_left <= self.mouse_x <= (self.btn_left + self.btn_width) and
                current_btn_bottom <= self.mouse_y <= (current_btn_bottom + self.btn_height)):
                current_hover = index
                break
        
        self.hovered_index = current_hover

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.current_state == "MAIN_MENU":
            for index, option_text in enumerate(self.menu_options):
                current_btn_bottom = self.start_y_position - (index * self.y_spacing)
                
                if (self.btn_left <= x <= (self.btn_left + self.btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.btn_height)):
                    
                    if option_text == "OPTIONS":
                        self.current_state = "OPTIONS"
                        self.hovered_index = -1
                    elif option_text == "QUIT":
                        arcade.exit()  
                        
        elif self.current_state == "OPTIONS":
            for index, option_text in enumerate(self.option_options):
                current_btn_bottom = self.start_y_position - (index * self.y_spacing)
                
                if (self.btn_left <= x <= (self.btn_left + self.btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.btn_height)):
                    
                    if index == 0: 
                        self.audio_muted = not self.audio_muted
                        new_text = "AUDIO: MUTED" if self.audio_muted else "AUDIO: UNMUTED"
                        self.options_text_objects[0].text = new_text
                        
                    elif option_text == "BACK":
                        self.current_state = "MAIN_MENU"
                        self.hovered_index = -1

    def on_draw(self) -> None:
        self.clear()
        
        # 1. Background
        arcade.draw_texture_rect(
            self.background,
            LBWH(0, 0, self.width, self.height),
        )

        active_text_list = (
            self.text_objects if self.current_state == "MAIN_MENU" 
            else self.options_text_objects
        )
        
        # 2. Text Overlay (Keeps stable font_size to prevent visual bounding box artifacts)
        for index, text_obj in enumerate(active_text_list):
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