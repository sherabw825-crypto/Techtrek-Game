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

        # Pre-create static Arcade Text objects to fix the performance warning
        self.text_objects = []
        for index, option_text in enumerate(self.menu_options):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            center_x = self.btn_left + (self.btn_width / 2)
            center_y = current_btn_bottom + (self.btn_height / 2)
            
            # FIXED: Using x and y instead of start_x and start_y
            text_obj = arcade.Text(
                option_text,
                x=center_x,
                y=center_y,
                color=(105, 108, 128),  # Idle baseline color
                font_size=21,
                font_name="Times New Roman",
                anchor_x="center",
                anchor_y="center",
                bold=False,
            )
            self.text_objects.append(text_obj)

    def on_resize(self, width: float, height: float) -> None:
        super().on_resize(width, height)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        for index, option_text in enumerate(self.menu_options):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            
            if (self.btn_left <= x <= (self.btn_left + self.btn_width) and
                current_btn_bottom <= y <= (current_btn_bottom + self.btn_height)):
                
                if option_text == "QUIT":
                    arcade.exit()  

    def on_draw(self) -> None:
        self.clear()
        
        # 1. Renders background canvas graphic
        arcade.draw_texture_rect(
            self.background,
            LBWH(0, 0, self.width, self.height),
        )
        
        # 2. Process math overlays and render pre-cached elements
        for index, text_obj in enumerate(self.text_objects):
            current_btn_bottom = self.start_y_position - (index * self.y_spacing)
            
            is_hovered = (
                self.btn_left <= self.mouse_x <= (self.btn_left + self.btn_width) and
                current_btn_bottom <= self.mouse_y <= (current_btn_bottom + self.btn_height)
            )
            
            center_x = self.btn_left + (self.btn_width / 2)
            center_y = current_btn_bottom + (self.btn_height / 2)
            
            if is_hovered:
                # Hover box backdrop element rendering
                arcade.draw_rect_filled(
                    arcade.XYWH(center_x, center_y, self.btn_width, self.btn_height),
                    color=(115, 95, 155, 35),  
                )
                # Modify existing text properties quickly instead of drawing from scratch
                text_obj.font_size = 24
                text_obj.color = arcade.color.WHITE
            else:
                # Revert properties if cursor leaves the box
                text_obj.font_size = 21
                text_obj.color = (105, 108, 128)
                
            # Efficiently draw our pre-cached text item
            text_obj.draw()


def main() -> None:
    window = TechtrekWindow()
    arcade.run()


if __name__ == "__main__":
    main()