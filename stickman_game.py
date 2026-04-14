# -*- coding: utf-8 -*-
"""
Stickman Line Drawing Game
"""

import pygame
import math
import sys

# ==================== 常量定义 ====================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (135, 206, 250)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)

# 游戏常量
MAX_INK = 1000
LINE_THICKNESS = 3
STICKMAN_SPEED = 3
STICKMAN_RADIUS = 5

# ==================== 关卡数据 (硬编码) ====================
# 每个关卡: [起点x, 起点y, 终点x, 终点y, 时间限制(秒), 障碍物列表, 平台列表]
# 障碍物: [x, y, width, height] - 墙壁
# 平台: [x, y, width, height] - 可站立的平台

LEVELS = [
    {
        "name": "Level 1 - Beginner",
        "start": [100, 600],
        "end": [1100, 600],
        "time_limit": 60,
        "walls": [
            [400, 400, 30, 300],
            [700, 300, 30, 400],
        ],
        "platforms": [
            [200, 500, 150, 20],
            [500, 450, 150, 20],
            [850, 500, 150, 20],
        ],
        "ink_bonus": 1.0,
    },
    {
        "name": "Level 2 - Intermediate",
        "start": [100, 700],
        "end": [1100, 200],
        "time_limit": 45,
        "walls": [
            [300, 300, 30, 400],
            [500, 200, 30, 400],
            [700, 100, 30, 500],
            [900, 200, 30, 400],
        ],
        "platforms": [
            [150, 600, 100, 20],
            [350, 500, 100, 20],
            [550, 400, 100, 20],
            [750, 300, 100, 20],
            [950, 250, 100, 20],
        ],
        "ink_bonus": 0.8,
    },
    {
        "name": "Level 3 - Expert",
        "start": [100, 700],
        "end": [1100, 100],
        "time_limit": 30,
        "walls": [
            [200, 400, 30, 350],
            [350, 200, 30, 400],
            [500, 400, 30, 350],
            [650, 100, 30, 500],
            [800, 300, 30, 400],
            [950, 150, 30, 500],
        ],
        "platforms": [
            [100, 650, 80, 20],
            [250, 550, 80, 20],
            [400, 450, 80, 20],
            [550, 350, 80, 20],
            [700, 250, 80, 20],
            [850, 180, 80, 20],
            [1000, 150, 80, 20],
        ],
        "ink_bonus": 0.6,
    },
]


class Line:
    def __init__(self, start_pos, end_pos):
        self.start = start_pos
        self.end = end_pos
        self.length = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
    
    def get_point_at_distance(self, distance):
        if self.length == 0:
            return self.start
        ratio = distance / self.length
        ratio = max(0, min(1, ratio))
        x = self.start[0] + (self.end[0] - self.start[0]) * ratio
        y = self.start[1] + (self.end[1] - self.start[1]) * ratio
        return (x, y)
    
    def get_slope(self):
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        if dx == 0:
            return float('inf')
        return dy / dx
    
    def get_angle(self):
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.atan2(dy, dx)
    
    def distance_to_point(self, point):
        px, py = point
        x1, y1 = self.start
        x2, y2 = self.end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    def get_closest_point(self, point):
        px, py = point
        x1, y1 = self.start
        x2, y2 = self.end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return self.start
        
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        return (x1 + t * dx, y1 + t * dy)


class Stickman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "Stoping"
        self.current_line = None
        self.current_line_progress = 0
        self.speed = STICKMAN_SPEED
        self.direction = 1
        self.lines = []
    
    def update(self, lines):
        if self.state != "Running":
            return
        
        self.lines = lines
        
        if self.current_line is None:
            self.find_nearest_line(lines)
        
        if self.current_line is not None:
            self.move_along_line()
    
    def find_nearest_line(self, lines, prefer_start=None):
        min_distance = float('inf')
        nearest_line = None
        nearest_progress = 0
        
        foot_pos = (self.x, self.y + 20)
        
        for line in lines:
            dist = line.distance_to_point(foot_pos)
            if dist < min_distance:
                min_distance = dist
                nearest_line = line
                closest_point = line.get_closest_point(foot_pos)
                dx = closest_point[0] - line.start[0]
                dy = closest_point[1] - line.start[1]
                nearest_progress = math.sqrt(dx**2 + dy**2)
        
        if nearest_line and min_distance < 50:
            self.current_line = nearest_line
            self.current_line_progress = nearest_progress
            
            if prefer_start is not None:
                if prefer_start == "end":
                    self.current_line_progress = nearest_line.length
                    self.direction = -1
                else:
                    self.current_line_progress = 0
                    self.direction = 1
            else:
                angle = nearest_line.get_angle()
                if abs(angle) < math.pi / 2:
                    self.direction = 1
                else:
                    self.direction = -1
        else:
            self.current_line = None
    
    def find_connected_line(self, current_end, lines):
        threshold = 30
        best_line = None
        best_dist = float('inf')
        connect_at_start = True
        
        for line in lines:
            if line == self.current_line:
                continue
            
            dist_to_start = math.sqrt((current_end[0] - line.start[0])**2 + 
                                      (current_end[1] - line.start[1])**2)
            dist_to_end = math.sqrt((current_end[0] - line.end[0])**2 + 
                                    (current_end[1] - line.end[1])**2)
            
            if dist_to_start < threshold and dist_to_start < best_dist:
                best_dist = dist_to_start
                best_line = line
                connect_at_start = True
            
            if dist_to_end < threshold and dist_to_end < best_dist:
                best_dist = dist_to_end
                best_line = line
                connect_at_start = False
        
        return best_line, connect_at_start
    
    def move_along_line(self):
        if self.current_line is None:
            return
        
        line = self.current_line
        self.current_line_progress += self.speed * self.direction
        
        if self.current_line_progress >= line.length:
            end_point = line.end
            next_line, connect_at_start = self.find_connected_line(end_point, self.lines)
            
            if next_line:
                self.current_line = next_line
                if connect_at_start:
                    self.current_line_progress = 0
                    self.direction = 1
                else:
                    self.current_line_progress = next_line.length
                    self.direction = -1
            else:
                self.current_line_progress = line.length
                self.direction = -1
        
        elif self.current_line_progress <= 0:
            end_point = line.start
            next_line, connect_at_start = self.find_connected_line(end_point, self.lines)
            
            if next_line:
                self.current_line = next_line
                if connect_at_start:
                    self.current_line_progress = 0
                    self.direction = 1
                else:
                    self.current_line_progress = next_line.length
                    self.direction = -1
            else:
                self.current_line_progress = 0
                self.direction = 1
        
        new_pos = line.get_point_at_distance(self.current_line_progress)
        self.x = new_pos[0]
        self.y = new_pos[1] - 20
    
    def draw(self, screen):
        head_radius = 12
        body_length = 25
        arm_length = 18
        leg_length = 20
        
        head_y = self.y - body_length - head_radius
        pygame.draw.circle(screen, BLACK, (int(self.x), int(head_y)), head_radius, 2)
        
        body_top = head_y + head_radius
        body_bottom = self.y
        pygame.draw.line(screen, BLACK, (self.x, body_top), (self.x, body_bottom), 2)
        
        arm_y = body_top + 8
        
        if self.state == "Running":
            arm_angle = math.sin(pygame.time.get_ticks() / 100) * 0.5
            leg_angle = math.sin(pygame.time.get_ticks() / 100 + math.pi) * 0.4
        else:
            arm_angle = 0
            leg_angle = 0
        
        left_arm_end = (self.x - arm_length * math.cos(0.5 + arm_angle),
                       arm_y + arm_length * math.sin(0.5 + arm_angle))
        right_arm_end = (self.x + arm_length * math.cos(0.5 - arm_angle),
                        arm_y + arm_length * math.sin(0.5 - arm_angle))
        pygame.draw.line(screen, BLACK, (self.x, arm_y), left_arm_end, 2)
        pygame.draw.line(screen, BLACK, (self.x, arm_y), right_arm_end, 2)
        
        left_leg_end = (self.x - leg_length * math.cos(0.3 + leg_angle),
                       body_bottom + leg_length * math.sin(0.3 + leg_angle))
        right_leg_end = (self.x + leg_length * math.cos(0.3 - leg_angle),
                        body_bottom + leg_length * math.sin(0.3 - leg_angle))
        pygame.draw.line(screen, BLACK, (self.x, body_bottom), left_leg_end, 2)
        pygame.draw.line(screen, BLACK, (self.x, body_bottom), right_leg_end, 2)
        
        eye_offset = 4 if self.direction > 0 else -4
        pygame.draw.circle(screen, BLACK, (int(self.x + eye_offset), int(head_y - 2)), 2)
    
    def check_reached_end(self, end_pos, threshold=50):
        dist = math.sqrt((self.x - end_pos[0])**2 + (self.y - end_pos[1])**2)
        return dist < threshold


class Button:
    def __init__(self, x, y, width, height, text, color=GREEN, hover_color=BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.Font(None, 36)
    
    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
        else:
            color = self.color
        
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 3, border_radius=10)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Stickman Line Drawing Game")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        try:
            self.font_large = pygame.font.SysFont("microsoftyahei", 48)
            self.font_medium = pygame.font.SysFont("microsoftyahei", 32)
            self.font_small = pygame.font.SysFont("microsoftyahei", 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        
        self.current_level = 0
        self.ink_remaining = MAX_INK
        self.lines = []
        self.current_drawing = []
        self.is_drawing = False
        
        self.game_state = "menu"
        self.time_remaining = 0
        self.level_complete = False
        self.ink_used = 0
        
        self.start_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50, "START")
        self.next_level_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 50, "Next Level")
        self.restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 160, 200, 50, "Restart")
        
        self.load_level(0)
    
    def load_level(self, level_index):
        if level_index >= len(LEVELS):
            self.game_state = "game_complete"
            return
        
        self.current_level = level_index
        level = LEVELS[level_index]
        
        self.stickman = Stickman(level["start"][0], level["start"][1])
        self.start_pos = level["start"]
        self.end_pos = level["end"]
        self.time_remaining = level["time_limit"]
        self.walls = level["walls"]
        self.platforms = level["platforms"]
        self.level_name = level["name"]
        self.ink_bonus = level["ink_bonus"]
        
        self.lines = []
        self.current_drawing = []
        self.ink_remaining = MAX_INK * self.ink_bonus
        self.ink_used = 0
        self.game_state = "drawing"
        self.level_complete = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.game_state == "menu":
                if self.start_button.is_clicked(event):
                    self.load_level(0)
            
            elif self.game_state == "drawing":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.is_drawing = True
                        self.current_drawing = [event.pos]
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_drawing and self.ink_remaining > 0:
                        last_pos = self.current_drawing[-1]
                        dist = math.sqrt((event.pos[0] - last_pos[0])**2 + 
                                        (event.pos[1] - last_pos[1])**2)
                        if dist > 5:
                            self.current_drawing.append(event.pos)
                            self.ink_remaining -= dist * 0.5
                            self.ink_used += dist * 0.5
                            self.ink_remaining = max(0, self.ink_remaining)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.is_drawing:
                        self.is_drawing = False
                        if len(self.current_drawing) >= 2:
                            for i in range(len(self.current_drawing) - 1):
                                line = Line(self.current_drawing[i], self.current_drawing[i + 1])
                                self.lines.append(line)
                        self.current_drawing = []
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.game_state = "running"
                        self.stickman.state = "Running"
                    if event.key == pygame.K_c:
                        self.lines = []
                        self.ink_remaining = MAX_INK * self.ink_bonus
                        self.ink_used = 0
            
            elif self.game_state == "running":
                pass
            
            elif self.game_state == "level_complete":
                if self.next_level_button.is_clicked(event):
                    self.load_level(self.current_level + 1)
                if self.restart_button.is_clicked(event):
                    self.load_level(self.current_level)
            
            elif self.game_state == "time_up":
                if self.restart_button.is_clicked(event):
                    self.load_level(self.current_level)
            
            elif self.game_state == "game_complete":
                if self.restart_button.is_clicked(event):
                    self.current_level = 0
                    self.load_level(0)
        
        return True
    
    def update(self):
        if self.game_state == "running":
            self.stickman.update(self.lines)
            
            self.time_remaining -= 1 / FPS
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.game_state = "time_up"
            
            if self.stickman.check_reached_end(self.end_pos):
                self.game_state = "level_complete"
                self.level_complete = True
        
        elif self.game_state == "drawing":
            self.stickman.x = self.start_pos[0]
            self.stickman.y = self.start_pos[1]
    
    def draw_hud(self):
        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, 60))
        
        ink_ratio = self.ink_remaining / (MAX_INK * self.ink_bonus)
        bar_width = 300
        bar_height = 25
        bar_x = 20
        bar_y = 20
        
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, BLUE, (bar_x, bar_y, int(bar_width * ink_ratio), bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        ink_text = self.font_small.render(f"Ink: {int(self.ink_remaining)}/{int(MAX_INK * self.ink_bonus)}", True, WHITE)
        self.screen.blit(ink_text, (bar_x + bar_width + 10, bar_y + 2))
        
        time_color = RED if self.time_remaining < 10 else WHITE
        time_text = self.font_medium.render(f"Time: {int(self.time_remaining)}s", True, time_color)
        self.screen.blit(time_text, (SCREEN_WIDTH // 2 - 50, 15))
        
        level_text = self.font_medium.render(self.level_name, True, YELLOW)
        self.screen.blit(level_text, (SCREEN_WIDTH - 300, 15))
    
    def draw_level_elements(self):
        for wall in self.walls:
            pygame.draw.rect(self.screen, BROWN, wall)
            pygame.draw.rect(self.screen, BLACK, wall, 2)
        
        for platform in self.platforms:
            pygame.draw.rect(self.screen, GRAY, platform)
            pygame.draw.rect(self.screen, BLACK, platform, 2)
        
        pygame.draw.circle(self.screen, GREEN, self.start_pos, 20)
        pygame.draw.circle(self.screen, BLACK, self.start_pos, 20, 2)
        start_text = self.font_small.render("S", True, WHITE)
        start_rect = start_text.get_rect(center=self.start_pos)
        self.screen.blit(start_text, start_rect)
        
        pygame.draw.circle(self.screen, RED, self.end_pos, 25)
        pygame.draw.circle(self.screen, BLACK, self.end_pos, 25, 2)
        end_text = self.font_small.render("E", True, WHITE)
        end_rect = end_text.get_rect(center=self.end_pos)
        self.screen.blit(end_text, end_rect)
    
    def draw_lines(self):
        for line in self.lines:
            pygame.draw.line(self.screen, BLUE, line.start, line.end, LINE_THICKNESS)
        
        if len(self.current_drawing) >= 2:
            pygame.draw.lines(self.screen, PURPLE, False, self.current_drawing, LINE_THICKNESS)
    
    def draw_menu(self):
        self.screen.fill(LIGHT_BLUE)
        
        title = self.font_large.render("Stickman Line Drawing Game", True, BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        instructions = [
            "Draw lines with mouse to guide the stickman",
            "Press SPACE to start moving",
            "Press C to clear all lines",
            "Reach the red endpoint before time runs out!"
        ]
        
        for i, text in enumerate(instructions):
            inst_text = self.font_small.render(text, True, DARK_GRAY)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 + i * 30))
            self.screen.blit(inst_text, inst_rect)
        
        self.start_button.draw(self.screen)
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        complete_text = self.font_large.render("Level Complete!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(complete_text, complete_rect)
        
        max_ink = MAX_INK * self.ink_bonus
        efficiency = (max_ink - self.ink_used) / max_ink * 100
        efficiency = max(0, min(100, efficiency))
        
        if efficiency >= 80:
            grade = "S"
            grade_color = YELLOW
        elif efficiency >= 60:
            grade = "A"
            grade_color = GREEN
        elif efficiency >= 40:
            grade = "B"
            grade_color = BLUE
        elif efficiency >= 20:
            grade = "C"
            grade_color = ORANGE
        else:
            grade = "D"
            grade_color = RED
        
        efficiency_text = self.font_medium.render(f"Ink Efficiency: {efficiency:.1f}%", True, WHITE)
        efficiency_rect = efficiency_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(efficiency_text, efficiency_rect)
        
        grade_text = self.font_large.render(f"Grade: {grade}", True, grade_color)
        grade_rect = grade_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(grade_text, grade_rect)
        
        if self.current_level < len(LEVELS) - 1:
            self.next_level_button.draw(self.screen)
        self.restart_button.draw(self.screen)
    
    def draw_time_up(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        time_up_text = self.font_large.render("Time's Up!", True, RED)
        time_up_rect = time_up_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(time_up_text, time_up_rect)
        
        self.restart_button.rect.y = SCREEN_HEIGHT // 2 + 50
        self.restart_button.draw(self.screen)
    
    def draw_game_complete(self):
        self.screen.fill(LIGHT_BLUE)
        
        complete_text = self.font_large.render("Congratulations! All Levels Complete!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(complete_text, complete_rect)
        
        self.restart_button.rect.y = SCREEN_HEIGHT // 2 + 50
        self.restart_button.draw(self.screen)
    
    def draw(self):
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "game_complete":
            self.draw_game_complete()
        else:
            self.screen.fill(LIGHT_BLUE)
            
            self.draw_level_elements()
            self.draw_lines()
            self.stickman.draw(self.screen)
            self.draw_hud()
            
            if self.game_state == "drawing":
                hint_text = self.font_small.render("Press SPACE to start | Press C to clear lines", True, DARK_GRAY)
                hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
                self.screen.blit(hint_text, hint_rect)
            
            if self.game_state == "level_complete":
                self.draw_level_complete()
            
            if self.game_state == "time_up":
                self.draw_time_up()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
