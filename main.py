import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)

class Direction(Enum):
    LEFT = 0
    RIGHT = 1

class TrackSegment:
    def __init__(self, start_x, start_y, angle, length):
        self.start_x = start_x
        self.start_y = start_y
        self.angle = angle  # in degrees
        self.length = length
        self.update_end_point()
    
    def update_end_point(self):
        angle_rad = math.radians(self.angle)
        self.end_x = self.start_x + math.cos(angle_rad) * self.length
        self.end_y = self.start_y - math.sin(angle_rad) * self.length
    
    def get_points(self):
        return (self.start_x, self.start_y), (self.end_x, self.end_y)

class TrolleyGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Trolley Problem")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.total_sacrificed = 0
        self.time_since_last_split = 0
        self.split_cooldown = 180
        self.current_split_active = False
        self.decision_made = False
        self.current_direction = None
        
        # Track parameters
        self.track_y = SCREEN_HEIGHT // 2
        self.split_angle = 30  # angle of divergence
        self.track_segments = []
        self.target_angle = 0
        self.current_angle = 0
        self.rotation_speed = 2  # degrees per frame
        
        # Split parameters
        self.split_start_x = None
        self.split_length = 300
        self.transition_progress = 0
        
        # People parameters
        self.left_count = 0
        self.right_count = 0
        
        # Trolley parameters
        self.trolley_x = SCREEN_WIDTH // 2
        self.trolley_y = self.track_y
        self.trolley_width = 40
        self.trolley_height = 30
        
        # Font
        self.font = pygame.font.Font(None, 36)

    def generate_split(self):
        self.left_count = random.randint(1, 10)
        self.right_count = random.randint(1, 10)
        self.split_start_x = SCREEN_WIDTH
        self.current_split_active = True
        self.decision_made = False
        self.current_direction = None
        self.current_angle = 0
        self.target_angle = 0
        self.transition_progress = 0
        
        # Generate track segments
        self.track_segments = [
            TrackSegment(self.split_start_x, self.track_y, -self.split_angle, self.split_length),  # Upper track
            TrackSegment(self.split_start_x, self.track_y, self.split_angle, self.split_length)    # Lower track
        ]

    def draw_trolley(self):
        # Draw trolley rotated according to current track angle
        trolley_surface = pygame.Surface((self.trolley_width, self.trolley_height), pygame.SRCALPHA)
        pygame.draw.rect(trolley_surface, RED, (0, 0, self.trolley_width, self.trolley_height))
        
        rotated_surface = pygame.transform.rotate(trolley_surface, self.current_angle)
        rotated_rect = rotated_surface.get_rect(center=(self.trolley_x, self.trolley_y))
        
        self.screen.blit(rotated_surface, rotated_rect)

    def draw_tracks(self):
        # Draw main track
        pygame.draw.line(self.screen, BROWN, (0, self.track_y), (SCREEN_WIDTH, self.track_y), 5)
        
        if self.current_split_active and self.split_start_x is not None:
            # Draw split tracks
            for i, segment in enumerate(self.track_segments):
                start_point, end_point = segment.get_points()
                
                # Calculate intermediate points for curved transition
                if self.decision_made:
                    chosen_angle = -self.split_angle if self.current_direction == Direction.LEFT else self.split_angle
                    transition_angle = chosen_angle * (1 - self.transition_progress)
                    
                    # Update segment angle for smooth transition
                    segment.angle = transition_angle
                    segment.update_end_point()
                    start_point, end_point = segment.get_points()
                
                # Draw track segment
                if (i == 0 and self.current_direction != Direction.RIGHT) or \
                   (i == 1 and self.current_direction != Direction.LEFT):
                    pygame.draw.line(self.screen, BROWN, start_point, end_point, 5)
                
                # Draw people counts
                if not self.decision_made:
                    offset = -30 if i == 0 else 30
                    count = self.left_count if i == 0 else self.right_count
                    self.draw_people_count(end_point[0], end_point[1] + offset, count)

    def draw_people_count(self, x, y, count):
        stick_figures = "🚶" * count
        text = self.font.render(stick_figures, True, BLACK)
        text_rect = text.get_rect(center=(x, y))
        self.screen.blit(text, text_rect)

    def draw_score(self):
        score_text = f"Sacrificed: {self.total_sacrificed}"
        text = self.font.render(score_text, True, BLACK)
        self.screen.blit(text, (SCREEN_WIDTH - 200, 20))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.current_split_active and not self.decision_made:
                    if event.key == pygame.K_UP:
                        self.current_direction = Direction.LEFT
                        self.total_sacrificed += self.left_count
                        self.decision_made = True
                        self.target_angle = -self.split_angle
                    elif event.key == pygame.K_DOWN:
                        self.current_direction = Direction.RIGHT
                        self.total_sacrificed += self.right_count
                        self.decision_made = True
                        self.target_angle = self.split_angle

    def update_track_rotation(self):
        if self.decision_made:
            # Update transition progress
            self.transition_progress = min(1.0, self.transition_progress + 0.02)
            
            # Smoothly rotate current angle towards target
            if abs(self.current_angle - self.target_angle) > 0.1:
                if self.current_angle < self.target_angle:
                    self.current_angle += self.rotation_speed
                else:
                    self.current_angle -= self.rotation_speed
            
            # Update trolley position based on current angle
            angle_rad = math.radians(self.current_angle)
            offset = 3  # Speed of vertical movement
            self.trolley_y += math.sin(angle_rad) * offset

    def update(self):
        # Move split leftward
        if self.current_split_active and self.split_start_x is not None:
            self.split_start_x -= 2
            for segment in self.track_segments:
                segment.start_x -= 2
                segment.update_end_point()
            
            self.update_track_rotation()
            
            # If split moves off screen, reset
            if self.split_start_x + self.split_length < 0:
                self.current_split_active = False
                self.time_since_last_split = 0
                self.trolley_y = self.track_y
                self.current_angle = 0
        
        # Generate new split after cooldown
        if not self.current_split_active:
            self.time_since_last_split += 1
            if self.time_since_last_split >= self.split_cooldown:
                self.generate_split()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()

            # Drawing
            self.screen.fill(WHITE)
            self.draw_tracks()
            self.draw_trolley()
            self.draw_score()
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = TrolleyGame()
    game.run()