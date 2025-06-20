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
            self.pig_y = WINDOW_HEIGHT // 2
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
                self.oink_sound = pygame.mixer.Sound(os.path.join("assets", "oink.wav"))
            except:
                print("Warning: Could not load sound file")
                self.oink_sound = None
                
            # Sound cooldown
            self.last_sound_time = 0
            self.sound_cooldown = 500  # milliseconds
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
        
        if keys[pygame.K_LEFT]:
            self.pig_x = max(0, self.pig_x - self.pig_speed)
            self.facing_right = False
            moved = True
        if keys[pygame.K_RIGHT]:
            self.pig_x = min(WINDOW_WIDTH - self.pig_width, self.pig_x + self.pig_speed)
            self.facing_right = True
            moved = True
        if keys[pygame.K_UP]:
            self.pig_y = max(0, self.pig_y - self.pig_speed)
            moved = True
        if keys[pygame.K_DOWN]:
            self.pig_y = min(WINDOW_HEIGHT - self.pig_height, self.pig_y + self.pig_speed)
            moved = True
        
        # Handle space bar for oink sound
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_sound_time > self.sound_cooldown:
                if self.oink_sound:
                    self.oink_sound.play()
                self.last_sound_time = current_time
        
        # Update bounce animation
        if moved:
            self.bounce_time += self.bounce_speed
            self.bounce_offset = abs(math.sin(self.bounce_time) * self.bounce_height)
        else:
            self.bounce_offset = 0
            self.bounce_time = 0

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