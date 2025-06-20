import pygame
import os
import sys
import math  # Add this import that was missing

# Initialize Pygame
try:
    pygame.init()
    pygame.mixer.init()
except:
    print("Error initializing Pygame")
    input("Press Enter to exit...")
    sys.exit(1)

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GROUND_Y = 500  # y-coordinate of the ground
FPS = 60

# Colors
WHITE = (255, 255, 255)
PINK = (255, 192, 203)
BLACK = (0, 0, 0)

class PiggyGame:
    def __init__(self):
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Piggy Adventure")
            self.clock = pygame.time.Clock()
            
            # Pig properties
            self.pig_width = 80
            self.pig_height = 80
            self.pig_x = WINDOW_WIDTH // 2
            self.pig_y = GROUND_Y - self.pig_height  # Start piggy on the ground
            self.pig_speed = 5
            self.facing_right = True
            
            # Asset directory relative to script
            self.asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
            # Load piggy images for left movement only
            self.piggy_fly_left_img = pygame.image.load(os.path.join(self.asset_dir, "piggy_fly_left.png")).convert_alpha()
            self.piggy_jump_left_img = pygame.image.load(os.path.join(self.asset_dir, "piggy_jump_left.png")).convert_alpha()
            self.piggy_sit_left_img = pygame.image.load(os.path.join(self.asset_dir, "piggy_sit_left.png")).convert_alpha()
            # Load piggy images for right movement animation
            self.piggy_right_imgs = [
                pygame.image.load(os.path.join(self.asset_dir, f"piggy_right{i+1}.png")).convert_alpha()
                for i in range(3)
            ]
            self.piggy_right_frame = 0
            self.piggy_right_anim_speed = 0.15  # Animation speed
            self.piggy_right_anim_time = 0
            
            # Create a pig surface with more detail
            self.pig = pygame.Surface((self.pig_width, self.pig_height), pygame.SRCALPHA)
            
            # Animation properties
            self.bounce_offset = 0
            self.bounce_speed = 0.1
            self.bounce_height = 3
            self.bounce_time = 0
            
            # Sound effects
            try:
                self.oink_sound = pygame.mixer.Sound(os.path.join(self.asset_dir, "oink.mp3"))
            except:
                print("Warning: Could not load sound file")
                self.oink_sound = None
                
            # Sound cooldown
            self.last_sound_time = 0
            self.sound_cooldown = 500  # milliseconds
            # Obstacles (placed on the ground)
            self.obstacles = [
                pygame.Rect(250, GROUND_Y - 40, 100, 40),
                pygame.Rect(450, GROUND_Y - 60, 120, 60),
                pygame.Rect(650, GROUND_Y - 30, 80, 30)
            ]
            # Jump properties
            self.is_jumping = False
            self.jump_velocity = 0
            self.jump_strength = 13
            self.gravity = 0.7
            # Fart sound
            try:
                self.fart_sound = pygame.mixer.Sound(os.path.join(self.asset_dir, "fart.mp3"))
            except:
                print("Warning: Could not load fart sound file")
                self.fart_sound = None
            # Flower properties
            self.flower_img = pygame.image.load(os.path.join(self.asset_dir, "flowers.png")).convert_alpha()
            self.flower_width = 50
            self.flower_height = 50
            self.flower_rects = [
                pygame.Rect(350, GROUND_Y - self.flower_height, self.flower_width, self.flower_height),
                pygame.Rect(600, GROUND_Y - self.flower_height, self.flower_width, self.flower_height)
            ]
            self.collected_flowers = set()
            # Background music
            self.music_file = os.path.join(self.asset_dir, "youcanhavesomeflowers.mp3")
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except Exception as e:
                print(f"Warning: Could not play background music: {e}")
        except Exception as e:
            print(f"Error initializing game: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

    def draw_pig(self, surface, x, y):
        # Only use special images when moving left or right
        if not self.facing_right:
            if self.is_jumping:
                if self.jump_velocity < 0:
                    piggy_img = self.piggy_jump_left_img  # Going up left
                else:
                    piggy_img = self.piggy_fly_left_img   # Falling/flying left
            elif not self.moving:
                piggy_img = self.piggy_sit_left_img      # Sitting left
            else:
                piggy_img = self.piggy_sit_left_img      # Default to sit when moving on ground left
            # No flip needed, images are already left-facing
        else:
            # Animate piggy moving right
            if self.moving:
                self.piggy_right_anim_time += self.piggy_right_anim_speed
                self.piggy_right_frame = int(self.piggy_right_anim_time) % len(self.piggy_right_imgs)
            else:
                self.piggy_right_frame = 0
                self.piggy_right_anim_time = 0
            piggy_img = self.piggy_right_imgs[self.piggy_right_frame]
        # Scale image to piggy size
        piggy_img = pygame.transform.smoothscale(piggy_img, (self.pig_width, self.pig_height))
        surface.blit(piggy_img, (0, 0))
        # Remove all custom drawing code below, only use the image
        # ...existing code...

    def handle_input(self):
        # Remove vertical movement from handle_input
        # Only handle horizontal movement and jumping intent here
        keys = pygame.key.get_pressed()
        moved = False
        self.moving = False  # Track if piggy is moving for animation
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        dx = 0
        if keys[pygame.K_LEFT]:
            dx = -self.pig_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            dx = self.pig_speed
            self.facing_right = True
        # Move horizontally (allow in air)
        if dx != 0:
            new_rect = pig_rect.move(dx, 0)
            if not self.check_collision(new_rect):
                self.pig_x += dx
                moved = True
        # Jumping
        if not self.is_jumping and keys[pygame.K_SPACE]:
            self.is_jumping = True
            self.jump_velocity = -self.jump_strength
        # Play oink sound when moving (not jumping)
        current_time = pygame.time.get_ticks()
        if moved and not self.is_jumping and current_time - self.last_sound_time > self.sound_cooldown:
            if self.oink_sound:
                self.oink_sound.play()
            self.last_sound_time = current_time
        # Update bounce animation
        if moved and not self.is_jumping:
            self.bounce_time += self.bounce_speed
            self.bounce_offset = abs(math.sin(self.bounce_time) * self.bounce_height)
            self.moving = True
        else:
            self.bounce_offset = 0
            self.bounce_time = 0
            self.moving = False
        # Update right-facing animation
        if self.facing_right:
            self.piggy_right_anim_time += self.piggy_right_anim_speed
            if self.piggy_right_anim_time >= 1:
                self.piggy_right_anim_time = 0
                self.piggy_right_frame = (self.piggy_right_frame + 1) % len(self.piggy_right_imgs)

    def apply_gravity(self):
        if self.is_jumping:
            self.pig_y += self.jump_velocity
            self.jump_velocity += self.gravity
            # Check if piggy has landed
            if self.pig_y >= WINDOW_HEIGHT - self.pig_height:
                self.pig_y = WINDOW_HEIGHT - self.pig_height
                self.is_jumping = False
                self.jump_velocity = 0

    def check_collisions(self):
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        for obstacle in self.obstacles:
            if pig_rect.colliderect(obstacle):
                # Simple collision response: stop piggy from moving through the obstacle
                if self.facing_right:
                    self.pig_x = obstacle.left - self.pig_width
                else:
                    self.pig_x = obstacle.right
                self.is_jumping = False
                self.jump_velocity = 0
                break

    def draw_obstacles(self):
        for obs in self.obstacles:
            pygame.draw.rect(self.screen, (120, 80, 40), obs)
    def draw_ground(self):
        pygame.draw.rect(self.screen, (60, 180, 75), (0, GROUND_Y, WINDOW_WIDTH, WINDOW_HEIGHT - GROUND_Y))

    def check_collision(self, rect):
        for obs in self.obstacles:
            if rect.colliderect(obs):
                return True
        return False

    def get_floor_y(self, pig_rect):
        # Returns the y-coordinate where the piggy should land (ground or top of obstacle)
        ground_y = GROUND_Y - self.pig_height
        min_y = ground_y
        for obs in self.obstacles:
            # Check if pig is horizontally over the obstacle
            if pig_rect.right > obs.left and pig_rect.left < obs.right:
                obs_top = obs.top - self.pig_height
                if pig_rect.bottom <= obs.top + 10 and obs_top < min_y:
                    min_y = obs_top
        return min_y

    def draw_flowers(self):
        for idx, rect in enumerate(self.flower_rects):
            if idx not in self.collected_flowers:
                flower_img = pygame.transform.smoothscale(self.flower_img, (self.flower_width, self.flower_height))
                self.screen.blit(flower_img, (rect.x, rect.y))

    def check_flower_collision(self):
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        for idx, rect in enumerate(self.flower_rects):
            if idx not in self.collected_flowers and pig_rect.colliderect(rect):
                self.collected_flowers.add(idx)
                if self.fart_sound:
                    self.fart_sound.play()

    def update_vertical_position(self):
        # Always apply gravity if not standing on ground or obstacle
        prev_y = self.pig_y
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        floor_y = self.get_floor_y(pig_rect)
        if self.is_jumping:
            next_y = self.pig_y + self.jump_velocity
            self.jump_velocity += self.gravity
            # Predict next position
            test_rect = pygame.Rect(self.pig_x, next_y, self.pig_width, self.pig_height)
            landed = False
            for obs in self.obstacles:
                # Only check if moving downward and crossing the top of the obstacle
                if prev_y + self.pig_height <= obs.top and next_y + self.pig_height >= obs.top:
                    if test_rect.right > obs.left and test_rect.left < obs.right:
                        self.pig_y = obs.top - self.pig_height
                        self.is_jumping = False
                        self.jump_velocity = 0
                        landed = True
                        break
            if not landed:
                # Check for ground
                ground_y = GROUND_Y - self.pig_height
                if next_y >= ground_y:
                    self.pig_y = ground_y
                    self.is_jumping = False
                    self.jump_velocity = 0
                else:
                    self.pig_y = next_y
        else:
            # If not jumping, check if piggy is standing on something
            if self.pig_y < floor_y:
                self.is_jumping = True
                self.jump_velocity = 0
            else:
                self.pig_y = floor_y
                self.is_jumping = False
                self.jump_velocity = 0

    def run(self):
        try:
            running = True
            while running:
                # Event handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False

                # Handle input
                self.handle_input()
                # Always update vertical position (gravity/falling)
                self.update_vertical_position()

                # Clear screen
                self.screen.fill(WHITE)
                self.draw_ground()
                
                # Draw obstacles
                self.draw_obstacles()
                
                # Create new pig surface and draw pig
                self.pig.fill((0, 0, 0, 0))  # Clear with transparency
                self.draw_pig(self.pig, 0, 0)
                
                # Draw the pig with bounce offset
                self.screen.blit(self.pig, (self.pig_x, self.pig_y - self.bounce_offset))
                # Draw flowers
                self.draw_flowers()
                # Check for flower collision
                self.check_flower_collision()

                pygame.display.flip()
                self.clock.tick(FPS)

        except Exception as e:
            print(f"Error during game loop: {e}")
            input("Press Enter to exit...")
        finally:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    try:
        game = PiggyGame()
        game.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")