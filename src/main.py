import arcade
from player import PlayerCharacter

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Character Animation Test"

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        
        self.player = None
        self.player_list = None
        
        # Create a SpriteList for the environment to replace primitive drawing
        self.environment_list = None
        
        self.left_pressed = False
        self.right_pressed = False
        
        # Floor and Ledge Coordinates
        self.floor_y = 0
        self.ledge_left = 0
        self.ledge_right = 0
        self.ledge_top = 0

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.environment_list = arcade.SpriteList()
        
        self.player = PlayerCharacter()
        
        # Define Ground and Platform Boundaries
        self.floor_y = self.height // 3
        self.ledge_left = self.width // 2 + 100
        self.ledge_right = self.width // 2 + 400
        self.ledge_top = self.floor_y + 150
        
        self.player.center_x = self.width // 2
        self.player.center_y = self.floor_y
        self.player_list.append(self.player)

        # 1. Create Ground Sprite
        ground_height = self.floor_y - 35
        ground = arcade.SpriteSolidColor(width=self.width, height=ground_height, color=arcade.color.BLACK)
        ground.center_x = self.width // 2
        ground.center_y = ground_height // 2
        self.environment_list.append(ground)

        # 2. Create Ledge Sprite
        ledge_width = self.ledge_right - self.ledge_left
        ledge = arcade.SpriteSolidColor(width=ledge_width, height=20, color=arcade.color.BROWN)
        ledge.center_x = (self.ledge_left + self.ledge_right) // 2
        ledge.center_y = self.ledge_top - 10
        self.environment_list.append(ledge)

    def on_draw(self):
        self.clear()
        
        # Draw the environment blocks first so they stay in the background
        if self.environment_list:
            self.environment_list.draw()
            
        if self.player_list:
            self.player_list.draw()

    def on_update(self, delta_time):
        if self.player:
            # 1. Apply Gravity (Suspend if hanging or climbing)
            if (self.player.center_y > self.floor_y 
                and not self.player.is_on_ledge 
                and not self.player.is_climbing_ledge):
                self.player.change_y -= 0.5 
            
            # 2. Lock movement if sliding, attacking, hanging, or climbing
            if (not self.player.is_sliding 
                and not self.player.is_attacking 
                and not self.player.is_on_ledge 
                and not self.player.is_climbing_ledge):
                
                if self.left_pressed and not self.right_pressed:
                    self.player.change_x = -5
                elif self.right_pressed and not self.left_pressed:
                    self.player.change_x = 5
                else:
                    self.player.change_x = 0
            
            # Lock coordinates if holding onto the ledge
            if self.player.is_on_ledge and not self.player.is_climbing_ledge:
                self.player.change_x = 0
                self.player.change_y = 0
                
            # Move up automatically during the climb animation
            if self.player.is_climbing_ledge:
                self.player.change_y = 2.5
                self.player.change_x = 1 if self.player.character_face_direction == 0 else -1

            # 3. Apply speed to position
            self.player.center_x += self.player.change_x
            self.player.center_y += self.player.change_y
            
            # 4. Collisions
            # Floor Collision
            if self.player.center_y <= self.floor_y:
                self.player.center_y = self.floor_y
                self.player.change_y = 0
                
            # Ledge Top Collision (Only land on it if falling down onto it)
            if self.ledge_left < self.player.center_x < self.ledge_right:
                if self.player.change_y < 0 and self.player.center_y >= self.ledge_top:
                    if self.player.center_y + self.player.change_y <= self.ledge_top:
                        self.player.center_y = self.ledge_top
                        self.player.change_y = 0
            
            # 5. Update Animations
            self.player.update_animation(delta_time)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()
            return

        if not self.player: 
            return
            
        if key in (arcade.key.LEFT, arcade.key.A): 
            self.left_pressed = True
        elif key in (arcade.key.RIGHT, arcade.key.D): 
            self.right_pressed = True
            
        elif key == arcade.key.SPACE: 
            self.player.trigger_attack("ATTACK_1")
        elif key in (arcade.key.DOWN, arcade.key.S): 
            if self.player.center_y in (self.floor_y, self.ledge_top):
                self.player.trigger_slide()
        elif key == arcade.key.K: 
            self.player.trigger_knockback()
            
        # Ledge Grab Trigger
        elif key == arcade.key.L:
            self.player.center_x = self.ledge_left - 15
            self.player.center_y = self.ledge_top - 40
            self.player.is_on_ledge = True
            self.player.character_face_direction = 0 
            
        elif key in (arcade.key.UP, arcade.key.W): 
            if self.player.is_on_ledge:
                self.player.trigger_ledge_climb()
            elif self.player.center_y in (self.floor_y, self.ledge_top):
                self.player.change_y = 12  

    def on_key_release(self, key, modifiers):
        if not self.player: 
            return
            
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = False

def main():
    window = GameWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()