from pathlib import Path

import arcade
from arcade.types import LBWH


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "False Face"
BACKGROUND_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "images" / "GUI.jpg"
)
LOGO_PATH = (Path(__file__).resolve().parent.parent / "assets" / "images" / "logo.png"
)


class TechtrekWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color((22, 22, 30))
        self.background = arcade.load_texture(str(BACKGROUND_PATH))
        self.logo = arcade.load_texture(str(LOGO_PATH))

    def on_resize(self, width: float, height: float) -> None:
        # This fixes the stretching issue by resetting the viewport to the new window size
        super().on_resize(width, height)

    def on_draw(self) -> None:
        self.clear()
        
        # Draws the background stretched to the actual window size
        arcade.draw_texture_rect(
            self.background,
            LBWH(0, 0, self.width, self.height),
        )
        
        # Draws your larger logo in the top left area
        arcade.draw_texture_rect(
            self.logo,
            LBWH(35, self.height - 180 - 45, 380, 180),
        )


def main() -> None:
    window = TechtrekWindow()
    arcade.run()


if __name__ == "__main__":
    main()