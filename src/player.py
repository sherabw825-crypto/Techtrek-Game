from pathlib import Path
import arcade

# Base Directory Path for Image Assets
ASSETS_PATH = Path(__file__).resolve().parent.parent / "assets" / "images"

# Facing Direction Constants
RIGHT_FACING = 0
LEFT_FACING = 1


def load_vertical_spritesheet(image_path: Path, frame_count: int) -> list[arcade.Texture]:
    """Slices a vertical sprite sheet into a list of arcade.Texture frames."""
    texture = arcade.load_texture(str(image_path))
    frame_width = texture.width
    frame_height = texture.height // frame_count

    textures = []
    for i in range(frame_count):
        y = texture.height - (i + 1) * frame_height
        sub_texture = texture.crop(0, y, frame_width, frame_height)
        textures.append(sub_texture)

    return textures


class PlayerCharacter(arcade.Sprite):
    """Main Player Character handling movement transitions, states, combat, and animations."""

    def __init__(self) -> None:
        super().__init__()

        # Direction and State Tracking
        self.character_face_direction = RIGHT_FACING
        self.current_state = "IDLE"
        self.cur_texture = 0
        self.time_counter = 0.0

        # Action Flags & State Locks
        self.is_attacking = False
        self.is_sliding = False
        self.is_landing = False
        self.is_climbing_ledge = False
        self.is_recovering = False
        self.is_on_wall = False
        self.is_on_ledge = False

        # Previous Physics Memory (for detecting landing impact)
        self.prev_change_y = 0.0

        # Dictionary to store [right_frames, left_frames] for all animations
        self.animations = {}

        # All sprite sheet configurations: (file_name, frame_count)
        sprite_configs = {
            # Standard Movement & Idle
            "IDLE": ("Idle.png", 8),
            "WALK": ("Walk.png", 10),
            "RUN_START": ("Run start.png", 1),
            "RUN": ("Run.png", 10),
            "RUN_STOP": ("Run stop.png", 6),
            
            # Aerial & Transitions
            "JUMP": ("Jump.png", 4),
            "JUMP_APEX": ("Jump Apex.png", 5),
            "FALL": ("Fall.png", 5),
            "LAND": ("Land.png", 4),
            "LAND_DISTANT": ("Land from Distance.png", 8),
            
            # Wall & Ledge Holds / Transitions
            "WALL_HOLD_START": ("Wall hold start.png", 3),
            "WALL_HOLD": ("Wall hold.png", 4),
            "LEDGE_HOLD": ("Ledge hold_2.png", 4),
            "LEDGE_CLIMB": ("(Ledge hold ) climb up.png", 5),
            
            # Sliding Phases
            "SLIDE_START": ("Slide start.png", 4),
            "SLIDE": ("Slide.png", 5),
            "SLIDE_END": ("Slide end.png", 5),
            
            # Combat Actions
            "ATTACK_1": ("Attack 1.png", 8),
            "ATTACK_2": ("Attack 2.png", 8),
            "WIDE_ATTACK_3": ("Wide Attack 3.png", 10),
            "UP_ATTACK_4": ("Up Attack 4.png", 5),
            "JUMP_ATTACK": ("Jump Up Attack.png", 6),
            "FALL_ATTACK": ("Fall Down Attack.png", 7),
            
            # Damage & Recovery
            "KNOCKBACK": ("Knockback.png", 5),
            "KNOCKBACK_RECOVER": ("Knockback recover.png", 7),
            "DEATH": ("Death.png", 9)
        }

        # Load and slice all sprite sheet assets
        for name, (file_name, count) in sprite_configs.items():
            path = ASSETS_PATH / file_name
            if path.exists():
                right_frames = load_vertical_spritesheet(path, count)
                left_frames = [f.flip_left_right() for f in right_frames]
                self.animations[name] = [right_frames, left_frames]
            else:
                print(f"Warning: Could not find sprite sheet at {path}")

        # Initialize base sprite texture
        if "IDLE" in self.animations and len(self.animations["IDLE"][RIGHT_FACING]) > 0:
            self.texture = self.animations["IDLE"][RIGHT_FACING][0]

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """Evaluates active state and handles transitions across sprite frames."""

        # 1. Flip Facing Direction
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        previous_state = self.current_state

        # 2. State Logic & Transition Checks
        # Do not interrupt combat, landing, ledge climbing, or damage recovery
        if self.is_attacking or self.is_landing or self.is_climbing_ledge or self.is_recovering:
            pass

        # Landing check
        elif self.prev_change_y < 0 and self.change_y == 0:
            if self.prev_change_y < -12:
                self.current_state = "LAND_DISTANT"
                self.is_landing = True
            else:
                self.current_state = "LAND"
                self.is_landing = True

        # Slide logic
        elif self.is_sliding:
            if self.current_state == "SLIDE_START" and self.cur_texture >= len(self.animations.get("SLIDE_START", [[], []])[0]) - 1:
                self.current_state = "SLIDE"

        # Ledge & Wall holds
        elif self.is_on_ledge:
            self.current_state = "LEDGE_HOLD"
        elif self.is_on_wall:
            if previous_state not in ("WALL_HOLD_START", "WALL_HOLD"):
                self.current_state = "WALL_HOLD_START"
            elif previous_state == "WALL_HOLD_START" and self.cur_texture >= len(self.animations.get("WALL_HOLD_START", [[], []])[0]) - 1:
                self.current_state = "WALL_HOLD"

        # Aerial states
        elif self.change_y > 0:
            if self.change_y < 2:
                self.current_state = "JUMP_APEX"
            else:
                self.current_state = "JUMP"
        elif self.change_y < 0:
            self.current_state = "FALL"

        # Ground movement transitions
        elif abs(self.change_x) > 3:
            if previous_state not in ("RUN_START", "RUN"):
                self.current_state = "RUN_START"
            elif previous_state == "RUN_START" and self.cur_texture >= len(self.animations.get("RUN_START", [[], []])[0]) - 1:
                self.current_state = "RUN"
        elif abs(self.change_x) > 0:
            self.current_state = "WALK"
        else:
            if previous_state in ("RUN", "RUN_START"):
                self.current_state = "RUN_STOP"
            elif previous_state == "RUN_STOP" and self.cur_texture < len(self.animations.get("RUN_STOP", [[], []])[0]) - 1:
                pass
            else:
                self.current_state = "IDLE"

        self.prev_change_y = self.change_y

        if previous_state != self.current_state:
            self.cur_texture = 0
            self.time_counter = 0.0

        # 3. Advance Animation Frames
        self.time_counter += delta_time
        frame_speed = 0.06 if "RUN" in self.current_state or "SLIDE" in self.current_state else 0.09

        if self.time_counter >= frame_speed:
            self.time_counter = 0.0

            if self.current_state in self.animations and len(self.animations[self.current_state][self.character_face_direction]) > 0:
                frames = self.animations[self.current_state][self.character_face_direction]
                self.cur_texture += 1

                # Sequence Loop / Transition Completion Rules
                if self.cur_texture >= len(frames):
                    if self.is_attacking:
                        self.is_attacking = False
                    elif self.is_landing:
                        self.is_landing = False
                    elif self.is_climbing_ledge:
                        self.is_climbing_ledge = False
                        self.is_on_ledge = False
                    elif self.is_recovering:
                        self.is_recovering = False
                    elif self.current_state == "SLIDE":
                        self.current_state = "SLIDE_END"
                        # Halt the forward momentum during the slide recovery animation
                        self.change_x = 0
                    elif self.current_state == "SLIDE_END":
                        self.is_sliding = False

                    self.cur_texture = 0
                self.texture = frames[self.cur_texture]

    def trigger_attack(self, attack_name: str = "ATTACK_1") -> None:
        """Triggers a combat action animation."""
        if not self.is_attacking and attack_name in self.animations:
            self.is_attacking = True
            self.current_state = attack_name
            self.cur_texture = 0
            self.time_counter = 0.0

    def trigger_slide(self) -> None:
        """Initiates ground slide sequence."""
        if not self.is_sliding and not self.is_attacking and self.change_y == 0:
            self.is_sliding = True
            self.current_state = "SLIDE_START"
            self.cur_texture = 0
            self.time_counter = 0.0
            
            # Apply automatic forward momentum
            slide_speed = 8  # You can increase/decrease this to change slide distance
            if self.character_face_direction == RIGHT_FACING:
                self.change_x = slide_speed
            else:
                self.change_x = -slide_speed

    def trigger_ledge_climb(self) -> None:
        """Triggers climb transition when holding a ledge."""
        if self.is_on_ledge and not self.is_climbing_ledge:
            self.is_climbing_ledge = True
            self.current_state = "LEDGE_CLIMB"
            self.cur_texture = 0
            self.time_counter = 0.0

    def trigger_knockback(self) -> None:
        """Triggers damage knockback and subsequent recovery phase."""
        self.is_recovering = True
        self.current_state = "KNOCKBACK"
        self.cur_texture = 0
        self.time_counter = 0.0