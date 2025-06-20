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
            
            # Create a pig surface with more detail
            self.pig = pygame.Surface((self.pig_width, self.pig_height), pygame.SRCALPHA)
            
            # Animation properties
            self.bounce_offset = 0
            self.bounce_speed = 0.1
            self.bounce_height = 3
            self.bounce_time = 0
            
            # Sound effects
            try:
                self.oink_sound = pygame.mixer.Sound(os.path.join("assets", "oink.mp3"))
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
                self.fart_sound = pygame.mixer.Sound(os.path.join("assets", "fart.mp3"))
            except:
                print("Warning: Could not load fart sound file")
                self.fart_sound = None
        except Exception as e:
            print(f"Error initializing game: {e}")
            input("Press Enter to exit...")
            sys.exit(1)

    def draw_pig(self, surface, x, y):
        # Body (oval)
        pygame.draw.ellipse(surface, PINK, (0, 0, self.pig_width, self.pig_height))
        
        # Eyes
        eye_x1 = 20 if self.facing_right else 45
        eye_x2 = 45 if self.facing_right else 20
        pygame.draw.circle(surface, BLACK, (eye_x1, 30), 6)
        pygame.draw.circle(surface, BLACK, (eye_x2, 30), 6)
        pygame.draw.circle(surface, WHITE, (eye_x1 - 2, 28), 2)
        pygame.draw.circle(surface, WHITE, (eye_x2 - 2, 28), 2)
        
        # Nose (snout)
        nose_x = 25 if self.facing_right else 30
        pygame.draw.ellipse(surface, (255, 150, 170), (nose_x, 40, 25, 20))
        pygame.draw.circle(surface, BLACK, (nose_x + 8, 48), 4)
        pygame.draw.circle(surface, BLACK, (nose_x + 17, 48), 4)
        
        # Ears
        ear_x1 = 10 if self.facing_right else 50
        ear_x2 = 40 if self.facing_right else 20
        pygame.draw.ellipse(surface, PINK, (ear_x1, 5, 20, 25))
        pygame.draw.ellipse(surface, PINK, (ear_x2, 5, 20, 25))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        moved = False
        pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -self.pig_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            dx = self.pig_speed
            self.facing_right = True
        if not self.is_jumping:
            if keys[pygame.K_UP]:
                dy = -self.pig_speed
            if keys[pygame.K_DOWN]:
                dy = self.pig_speed
        # Move horizontally (allow in air)
        if dx != 0:
            new_rect = pig_rect.move(dx, 0)
            if not self.check_collision(new_rect):
                self.pig_x += dx
                moved = True
        # Move vertically (only if not jumping)
        if dy != 0 and not self.is_jumping:
            new_rect = pig_rect.move(0, dy)
            if not self.check_collision(new_rect):
                self.pig_y += dy
                moved = True
        # Jumping
        if not self.is_jumping and keys[pygame.K_SPACE]:
            self.is_jumping = True
            self.jump_velocity = -self.jump_strength
            if self.fart_sound:
                self.fart_sound.play()
        # Apply jump physics
        if self.is_jumping:
            self.pig_y += self.jump_velocity
            self.jump_velocity += self.gravity
            pig_rect = pygame.Rect(self.pig_x, self.pig_y, self.pig_width, self.pig_height)
            floor_y = self.get_floor_y(pig_rect)
            if self.pig_y >= floor_y:
                self.pig_y = floor_y
                self.is_jumping = False
                self.jump_velocity = 0
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
        else:
            self.bounce_offset = 0
            self.bounce_time = 0

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