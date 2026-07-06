from pathlib import Path
import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "False Face"

BACKGROUND_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "GUI.jpg"
)


class TechtrekWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color(arcade.color.BLACK)
        
        try:
            self.background = arcade.load_texture(str(BACKGROUND_PATH))
        except Exception:
            self.background = None
        
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.runtime_width = SCREEN_WIDTH
        self.runtime_height = SCREEN_HEIGHT
        
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
            "GAME",
            "AUDIO",
            "VIDEO",
            "KEYBOARD",
            "BACK"
        ]
        
        # Left-aligned Main Menu configuration layout bounds
        self.main_btn_width = 300          
        self.main_btn_height = 50          
        self.main_btn_left = 180           
        self.main_start_y = 453   
        self.main_y_spacing = 65           

        # ADJUSTED: Shifted horizontal anchor right by another +140 pixels (total +280 pixels / ~10cm)
        self.opt_btn_width = 350
        self.opt_btn_height = 45
        self.opt_btn_left = ((SCREEN_WIDTH / 2) - (self.opt_btn_width / 2)) + 280
        self.opt_start_y = 390
        self.opt_y_spacing = 55

        self.hovered_index = -1

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
                font_size=32.5, 
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
            )
            self.text_objects.append(text_obj)

        # ADJUSTED: Title Text shifted right to follow the button alignment
        self.options_title_text = arcade.Text(
            "OPTIONS",
            x=(SCREEN_WIDTH / 2) + 280,
            y=480,
            color=arcade.color.WHITE,
            font_size=38,
            font_name="Times New Roman",
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
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
            )
            self.options_text_objects.append(text_obj)

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)
        self.runtime_width = width
        self.runtime_height = height

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_update(self, delta_time: float) -> None:
        if self.current_state == "MAIN_MENU":
            active_list = self.menu_options
            btn_left = self.main_btn_left
            btn_width = self.main_btn_width
            start_y = self.main_start_y
            y_spacing = self.main_y_spacing
            btn_height = self.main_btn_height
        else:
            active_list = self.option_options
            btn_left = self.opt_btn_left
            btn_width = self.opt_btn_width
            start_y = self.opt_start_y
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

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.current_state == "MAIN_MENU":
            for index, option_text in enumerate(self.menu_options):
                current_btn_bottom = self.main_start_y - (index * self.main_y_spacing)
                
                if (self.main_btn_left <= x <= (self.main_btn_left + self.main_btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.main_btn_height)):
                    
                    if option_text == "OPTIONS":
                        self.current_state = "OPTIONS"
                        self.hovered_index = -1
                    elif option_text == "QUIT":
                        arcade.exit()  
                        
        elif self.current_state == "OPTIONS":
            for index, option_text in enumerate(self.option_options):
                current_btn_bottom = self.opt_start_y - (index * self.opt_y_spacing)
                
                if (self.opt_btn_left <= x <= (self.opt_btn_left + self.opt_btn_width) and
                    current_btn_bottom <= y <= (current_btn_bottom + self.opt_btn_height)):
                    
                    if index == 1: 
                        self.audio_muted = not self.audio_muted
                        new_text = "AUDIO: MUTED" if self.audio_muted else "AUDIO"
                        self.options_text_objects[1].text = new_text
                        
                    elif option_text == "BACK":
                        self.current_state = "MAIN_MENU"
                        self.hovered_index = -1

    def on_draw(self) -> None:
        self.clear()
        
        if self.current_state == "MAIN_MENU":
            if self.background:
                arcade.draw_texture_rect(
                    texture=self.background,
                    rect=arcade.XYWH(self.runtime_width / 2, self.runtime_height / 2, self.runtime_width, self.runtime_height)
                )
            
            for index, text_obj in enumerate(self.text_objects):
                if index == self.hovered_index:
                    text_obj.color = arcade.color.WHITE
                else:
                    text_obj.color = (105, 108, 128)
                text_obj.draw()
                
        elif self.current_state == "OPTIONS":
            self.options_title_text.draw()
            
            # ADJUSTED: Decorative divider line shifted right to match the new container positions
            arcade.draw_line(
                start_x=((SCREEN_WIDTH / 2) + 280) - 180,
                start_y=450,
                end_x=((SCREEN_WIDTH / 2) + 280) + 180,
                end_y=450,
                color=(160, 165, 185, 150),
                line_width=2
            )
            
            for index, text_obj in enumerate(self.options_text_objects):
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