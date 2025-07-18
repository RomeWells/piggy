import pygame
import os
import sys
import math  # Add this import that was missing
import random  # Import random for placing obstacles
import cv2  # For video playback

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
            # Load new obstacle images
            self.bush_img = pygame.image.load(os.path.join(self.asset_dir, "bush.png")).convert_alpha()
            self.flower1_img = pygame.image.load(os.path.join(self.asset_dir, "flower1.png")).convert_alpha()
            self.rock_img = pygame.image.load(os.path.join(self.asset_dir, "rock.png")).convert_alpha()
            self.bird_img = pygame.image.load(os.path.join(self.asset_dir, "bird.png")).convert_alpha()
            self.obstacle_sprites = []  # List of dicts: {rect, type, img, collected}
            
            # Flower1 video size (for video flower obstacle)
            self.flower1_video_width = 60
            self.flower1_video_height = 80
            # Load flower1.mp4 as a video obstacle
            self.flower1_video_path = os.path.join(self.asset_dir, "flower1.mp4")
            self.flower1_video = cv2.VideoCapture(self.flower1_video_path)
            self.flower1_video_rect = None  # Will be set in _place_extra_obstacles
            self.flower1_video_collected = False
            self.flower1_video_frame = None
            self.flower1_video_last_update = 0
            self.flower1_video_fps = self.flower1_video.get(cv2.CAP_PROP_FPS) or 24
            
            self._place_extra_obstacles()
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
            # Background image
            self.background_img = pygame.image.load(os.path.join(self.asset_dir, "background.png")).convert()
            self.background_img = pygame.transform.smoothscale(self.background_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
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

    def _place_extra_obstacles(self):
        import random
        # Helper to avoid overlap
        def is_overlapping(new_rect, rects):
            for r in rects:
                if new_rect.colliderect(r):
                    return True
            return False
        placed_rects = [*self.obstacles]
        # Place bush (on ground)
        bush_rect = pygame.Rect(random.randint(50, 700), GROUND_Y - 60, 100, 60)
        while is_overlapping(bush_rect, placed_rects):
            bush_rect.x = random.randint(50, 700)
        self.obstacle_sprites.append({'rect': bush_rect, 'type': 'bush', 'img': self.bush_img, 'collected': False})
        placed_rects.append(bush_rect)
        # Place flower1 (on ground)
        flower_rect = pygame.Rect(random.randint(50, 700), GROUND_Y - 80, 60, 80)
        while is_overlapping(flower_rect, placed_rects):
            flower_rect.x = random.randint(50, 700)
        self.obstacle_sprites.append({'rect': flower_rect, 'type': 'flower1', 'img': self.flower1_img, 'collected': False})
        placed_rects.append(flower_rect)
        # Place rock (on ground or on top of a rectangular obstacle)
        if random.random() < 0.5:
            # On ground
            rock_rect = pygame.Rect(random.randint(50, 700), GROUND_Y - 50, 70, 50)
            while is_overlapping(rock_rect, placed_rects):
                rock_rect.x = random.randint(50, 700)
        else:
            # On top of a rectangular obstacle
            obs = random.choice(self.obstacles)
            rock_rect = pygame.Rect(obs.centerx - 35, obs.top - 50, 70, 50)
        self.obstacle_sprites.append({'rect': rock_rect, 'type': 'rock', 'img': self.rock_img, 'collected': False})
        placed_rects.append(rock_rect)
        # Place bird (above a rectangular obstacle)
        obs = random.choice(self.obstacles)
        bird_rect = pygame.Rect(obs.centerx - 30, obs.top - 90, 60, 60)
        self.obstacle_sprites.append({'rect': bird_rect, 'type': 'bird', 'img': self.bird_img, 'collected': False})
        # Place flower1.mp4 video obstacle (on ground, like flower1)
        import random
        flower1_video_rect = pygame.Rect(random.randint(50, 700), GROUND_Y - 80, self.flower1_video_width, self.flower1_video_height)
        def is_overlapping(new_rect, rects):
            for r in rects:
                if new_rect.colliderect(r):
                    return True
            return False
        placed_rects = [*self.obstacles] + [o['rect'] for o in self.obstacle_sprites]
        while is_overlapping(flower1_video_rect, placed_rects):
            flower1_video_rect.x = random.randint(50, 700)
        self.flower1_video_rect = flower1_video_rect
        placed_rects.append(flower1_video_rect)

    def draw_extra_obstacles(self):
        for obs in self.obstacle_sprites:
            if not obs["collected"]:
                img = pygame.transform.smoothscale(obs["img"], (obs["rect"].width, obs["rect"].height))
                self.screen.blit(img, (obs["rect"].x, obs["rect"].y))

    def check_extra_obstacle_collision(self):
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        for obs in self.obstacle_sprites:
            if not obs['collected'] and pig_rect.colliderect(obs['rect']):
                obs['collected'] = True
                if self.fart_sound:
                    self.fart_sound.play()

    def draw_flower1_video(self):
        if self.flower1_video_collected:
            return
        # Update video frame based on FPS
        now = pygame.time.get_ticks()
        interval = int(1000 / self.flower1_video_fps)
        if now - self.flower1_video_last_update > interval or self.flower1_video_frame is None:
            ret, frame = self.flower1_video.read()
            if not ret:
                self.flower1_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.flower1_video.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.flower1_video_width, self.flower1_video_height))
                surf = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                surf.set_colorkey((0, 0, 0))  # Make black transparent
                self.flower1_video_frame = surf
            self.flower1_video_last_update = now
        if self.flower1_video_frame:
            self.screen.blit(self.flower1_video_frame, (self.flower1_video_rect.x, self.flower1_video_rect.y))

    def check_flower1_video_collision(self):
        if self.flower1_video_collected:
            return
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        if pig_rect.colliderect(self.flower1_video_rect):
            self.flower1_video_collected = True
            if self.fart_sound:
                self.fart_sound.play()

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
                # Draw background FIRST
                self.screen.blit(self.background_img, (0, 0))
                # Draw ground
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
                # Draw extra obstacles
                self.draw_extra_obstacles()
                # Draw flower1 video if not collected
                self.draw_flower1_video()
                # Check for flower collision
                self.check_flower_collision()
                # Check for extra obstacle collision
                self.check_extra_obstacle_collision()
                # Check for flower1 video collision
                self.check_flower1_video_collision()

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