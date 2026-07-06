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
        
        # Track runtime hardware mouse interaction variables
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Configuration setup for the vertical menu items button panel
        self.menu_options = [
            "CONTINUE",
            "NEW GAME",
            "OPTIONS",
            "JOURNAL",
            "CREDITS",
            "QUIT"
        ]
        
        # Dimensions for individual logical button hover bounding zones
        self.btn_width = 360          
        self.btn_height = 50          
        
        # Anchor offset position metrics on the left sidebar column area
        self.btn_left = 75            
        self.start_y_position = 430   
        self.y_spacing = 60           

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        # Loop through the layout positions to find exactly which button was clicked
        for index, option_text in enumerate(self.menu_options):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            
            # Check if the click coordinates fall inside this specific button's hitbox
            if (self.btn_left <= x <= (self.btn_left + self.btn_width) and
                current_btn_bottom <= y <= (current_btn_bottom + self.btn_height)):
                
                # Check if the text on the clicked button is "QUIT"
                if option_text == "QUIT":
                    arcade.exit()  # Closes the window and cleanly terminates the game process

    def on_draw(self) -> None:
        self.clear()
        
        # 1. Renders background canvas graphic
        arcade.draw_texture_rect(
            self.background,
            LBWH(0, 0, self.width, self.height),
        )
        
        # 2. Process math and rendering for each option
        for index, option_text in enumerate(self.menu_options):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            
            is_hovered = (
                self.btn_left <= self.mouse_x <= (self.btn_left + self.btn_width) and
                current_btn_bottom <= self.mouse_y <= (current_btn_bottom + self.btn_height)
            )
            
            center_x = self.btn_left + (self.btn_width / 2)
            center_y = current_btn_bottom + (self.btn_height / 2)
            
            if is_hovered:
                arcade.draw_rect_filled(
                    arcade.XYWH(center_x, center_y, self.btn_width, self.btn_height),
                    color=(115, 95, 155, 35),  
                )
                font_size_to_use = 24
                text_color_to_use = arcade.color.WHITE
            else:
                font_size_to_use = 21
                text_color_to_use = (105, 108, 128)
                
            arcade.draw_text(
                option_text,
                x=center_x,
                y=center_y,
                color=text_color_to_use,
                font_size=font_size_to_use,
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
                bold=False,
            )


def main() -> None:
    window = TechtrekWindow()
    arcade.run()


if __name__ == "__main__":
    main()