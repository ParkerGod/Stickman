# -*- coding: utf-8 -*-
import pygame
import math
import sys

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (80, 80, 80)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

MAX_INK = 1000
INK_PER_PIXEL = 0.5
STICKMAN_SPEED = 3
ATTACH_DISTANCE = 15

LEVELS = [
    {
        "name": "第一关 - 入门",
        "start": (100, 600),
        "end": (1050, 600),
        "time_limit": 60,
        "obstacles": [
            {"type": "wall", "rect": (500, 400, 30, 300)},
            {"type": "platform", "rect": (300, 500, 150, 20)},
            {"type": "platform", "rect": (700, 450, 150, 20)},
        ]
    },
    {
        "name": "第二关 - 进阶",
        "start": (100, 650),
        "end": (1050, 200),
        "time_limit": 90,
        "obstacles": [
            {"type": "wall", "rect": (300, 300, 30, 500)},
            {"type": "wall", "rect": (600, 100, 30, 500)},
            {"type": "wall", "rect": (900, 100, 30, 400)},
            {"type": "platform", "rect": (400, 550, 150, 20)},
            {"type": "platform", "rect": (700, 350, 150, 20)},
        ]
    },
    {
        "name": "第三关 - 挑战",
        "start": (100, 700),
        "end": (1050, 100),
        "time_limit": 120,
        "obstacles": [
            {"type": "wall", "rect": (200, 200, 30, 600)},
            {"type": "wall", "rect": (400, 0, 30, 500)},
            {"type": "wall", "rect": (600, 300, 30, 500)},
            {"type": "wall", "rect": (800, 0, 30, 500)},
            {"type": "wall", "rect": (1000, 200, 30, 500)},
            {"type": "platform", "rect": (280, 600, 100, 20)},
            {"type": "platform", "rect": (480, 400, 100, 20)},
            {"type": "platform", "rect": (680, 450, 100, 20)},
            {"type": "platform", "rect": (880, 250, 100, 20)},
        ]
    }
]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("火柴人画线游戏")
clock = pygame.time.Clock()

def get_chinese_font(size):
    font_names = ["simhei", "msyh", "simsun", "microsoftyahei", "SourceHanSans"]
    for name in font_names:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
    return pygame.font.Font(None, size)

font_large = get_chinese_font(48)
font_medium = get_chinese_font(36)
font_small = get_chinese_font(24)

class Stickman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "Stoping"
        self.body_radius = 15
        self.anim_frame = 0
        self.anim_timer = 0
        self.path_index = 0
        self.on_path = False
        
    def update(self, lines):
        if self.state == "Running" and lines and len(lines) > 1:
            if not self.on_path:
                nearest_dist = float('inf')
                nearest_idx = 0
                for i in range(len(lines)):
                    dist = math.hypot(self.x - lines[i][0], self.y - lines[i][1])
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_idx = i
                self.path_index = nearest_idx
                self.on_path = True
            
            if self.on_path and self.path_index < len(lines):
                target_x, target_y = lines[self.path_index]
                dx = target_x - self.x
                dy = target_y - self.y
                dist = math.hypot(dx, dy)
                
                if dist < STICKMAN_SPEED:
                    self.x = target_x
                    self.y = target_y
                    self.path_index += 1
                else:
                    self.x += (dx / dist) * STICKMAN_SPEED
                    self.y += (dy / dist) * STICKMAN_SPEED
            
            self.anim_timer += 1
            if self.anim_timer >= 5:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 4
        
        self.x = max(20, min(SCREEN_WIDTH - 20, self.x))
        self.y = max(80, min(SCREEN_HEIGHT - 20, self.y))
    
    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        
        pygame.draw.circle(surface, BLACK, (x, y), self.body_radius, 2)
        
        pygame.draw.line(surface, BLACK, (x, y + self.body_radius), (x, y + self.body_radius + 25), 2)
        
        leg_offset = 10 if self.state == "Running" and self.anim_frame % 2 == 0 else -10
        pygame.draw.line(surface, BLACK, (x, y + self.body_radius + 25), (x - leg_offset, y + self.body_radius + 45), 2)
        pygame.draw.line(surface, BLACK, (x, y + self.body_radius + 25), (x + leg_offset, y + self.body_radius + 45), 2)
        
        arm_offset = 8 if self.state == "Running" and self.anim_frame % 2 == 1 else -8
        pygame.draw.line(surface, BLACK, (x, y + self.body_radius + 5), (x - 15 - arm_offset, y + self.body_radius + 15), 2)
        pygame.draw.line(surface, BLACK, (x, y + self.body_radius + 5), (x + 15 + arm_offset, y + self.body_radius + 15), 2)
        
        state_text = "运行中" if self.state == "Running" else "静止"
        text = font_small.render(state_text, True, BLUE)
        surface.blit(text, (x - 20, y - 35))

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False
    
    def draw(self, surface):
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)
        
        text_surf = font_medium.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class Game:
    def __init__(self):
        self.current_level = 0
        self.reset_level()
        
    def reset_level(self):
        level = LEVELS[self.current_level]
        self.stickman = Stickman(*level["start"])
        self.lines = []
        self.drawing = False
        self.ink_used = 0
        self.ink_remaining = MAX_INK
        self.time_remaining = level["time_limit"]
        self.game_started = False
        self.level_complete = False
        self.start_button = Button(SCREEN_WIDTH // 2 - 80, 10, 160, 50, "开始移动", GREEN)
        self.last_point = None
        self.timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timer_event, 1000)
        
    def draw_hud(self, surface):
        pygame.draw.rect(surface, DARK_GRAY, (0, 0, SCREEN_WIDTH, 70))
        pygame.draw.line(surface, BLACK, (0, 70), (SCREEN_WIDTH, 70), 2)
        
        level_text = font_medium.render(LEVELS[self.current_level]["name"], True, WHITE)
        surface.blit(level_text, (20, 20))
        
        ink_bar_width = 200
        ink_bar_height = 25
        ink_bar_x = 250
        ink_bar_y = 22
        
        pygame.draw.rect(surface, BLACK, (ink_bar_x - 2, ink_bar_y - 2, ink_bar_width + 4, ink_bar_height + 4), 2)
        pygame.draw.rect(surface, LIGHT_GRAY, (ink_bar_x, ink_bar_y, ink_bar_width, ink_bar_height))
        
        ink_percent = self.ink_remaining / MAX_INK
        ink_color = GREEN if ink_percent > 0.3 else (RED if ink_percent < 0.1 else ORANGE)
        pygame.draw.rect(surface, ink_color, (ink_bar_x, ink_bar_y, int(ink_bar_width * ink_percent), ink_bar_height))
        
        ink_text = font_small.render(f"墨水: {int(ink_percent * 100)}%", True, WHITE)
        surface.blit(ink_text, (ink_bar_x + ink_bar_width + 10, ink_bar_y + 3))
        
        time_color = WHITE if self.time_remaining > 10 else RED
        time_text = font_medium.render(f"时间: {self.time_remaining}s", True, time_color)
        surface.blit(time_text, (SCREEN_WIDTH - 180, 20))
    
    def draw_obstacles(self, surface):
        level = LEVELS[self.current_level]
        for obs in level["obstacles"]:
            if obs["type"] == "wall":
                pygame.draw.rect(surface, GRAY, obs["rect"])
                pygame.draw.rect(surface, BLACK, obs["rect"], 2)
            elif obs["type"] == "platform":
                pygame.draw.rect(surface, DARK_GRAY, obs["rect"])
                pygame.draw.rect(surface, BLACK, obs["rect"], 2)
        
        start = level["start"]
        end = level["end"]
        pygame.draw.circle(surface, GREEN, start, 20)
        pygame.draw.circle(surface, BLACK, start, 20, 2)
        start_text = font_small.render("起点", True, BLACK)
        surface.blit(start_text, (start[0] - 20, start[1] + 25))
        
        pygame.draw.circle(surface, RED, end, 20)
        pygame.draw.circle(surface, BLACK, end, 20, 2)
        end_text = font_small.render("终点", True, BLACK)
        surface.blit(end_text, (end[0] - 20, end[1] + 25))
    
    def check_collision(self, x, y):
        level = LEVELS[self.current_level]
        for obs in level["obstacles"]:
            rect = pygame.Rect(obs["rect"])
            if rect.collidepoint(x, y):
                return True
        return False
    
    def check_win(self):
        level = LEVELS[self.current_level]
        end_x, end_y = level["end"]
        dist = math.hypot(self.stickman.x - end_x, self.stickman.y - end_y)
        return dist < 30
    
    def show_level_complete(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        title = font_large.render("关卡完成!", True, GREEN)
        surface.blit(title, title.get_rect(center=(center_x, center_y - 100)))
        
        ink_efficiency = max(0, (1 - self.ink_used / MAX_INK) * 100)
        score_text = font_medium.render(f"墨水利用率: {int(ink_efficiency)}%", True, YELLOW)
        surface.blit(score_text, score_text.get_rect(center=(center_x, center_y - 30)))
        
        time_text = font_medium.render(f"剩余时间: {self.time_remaining}s", True, WHITE)
        surface.blit(time_text, time_text.get_rect(center=(center_x, center_y + 10)))
        
        if self.current_level < len(LEVELS) - 1:
            next_btn_text = "下一关"
            next_btn_y = center_y + 80
        else:
            next_btn_text = "恭喜通关! 重玩"
            next_btn_y = center_y + 80
            
        next_button = Button(center_x - 80, next_btn_y, 160, 50, next_btn_text, GREEN)
        next_button.draw(surface)
        
        return next_button
    
    def run(self):
        running = True
        while running:
            screen.fill(WHITE)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == self.timer_event and self.game_started and not self.level_complete:
                    self.time_remaining -= 1
                    if self.time_remaining <= 0:
                        self.reset_level()
                
                if not self.level_complete:
                    if self.start_button.handle_event(event):
                        self.game_started = True
                        self.stickman.state = "Running"
                        self.stickman.path_index = 0
                        self.stickman.on_path = False
                    
                    if not self.game_started:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1 and not self.start_button.rect.collidepoint(event.pos):
                                self.drawing = True
                                mx, my = event.pos
                                if my > 70 and not self.check_collision(mx, my):
                                    self.last_point = (mx, my)
                                    self.lines.append((mx, my))
                        
                        elif event.type == pygame.MOUSEMOTION and self.drawing:
                            mx, my = event.pos
                            if my > 70 and self.ink_remaining > 0 and not self.check_collision(mx, my):
                                if self.last_point:
                                    dist = math.hypot(mx - self.last_point[0], my - self.last_point[1])
                                    ink_cost = dist * INK_PER_PIXEL
                                    if self.ink_remaining >= ink_cost:
                                        self.lines.append((mx, my))
                                        self.ink_remaining -= ink_cost
                                        self.ink_used += ink_cost
                                        self.last_point = (mx, my)
                        
                        elif event.type == pygame.MOUSEBUTTONUP:
                            self.drawing = False
                            self.last_point = None
                else:
                    center_x = SCREEN_WIDTH // 2
                    center_y = SCREEN_HEIGHT // 2
                    next_button_rect = pygame.Rect(center_x - 80, center_y + 80, 160, 50)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if next_button_rect.collidepoint(event.pos):
                            if self.current_level < len(LEVELS) - 1:
                                self.current_level += 1
                            else:
                                self.current_level = 0
                            self.reset_level()
            
            self.draw_obstacles(screen)
            
            if len(self.lines) > 1:
                pygame.draw.lines(screen, BLUE, False, self.lines, 4)
            
            if self.game_started and not self.level_complete:
                self.stickman.update(self.lines)
                
                if self.check_win():
                    self.level_complete = True
                    self.stickman.state = "Stoping"
            
            self.stickman.draw(screen)
            self.draw_hud(screen)
            
            if not self.game_started and not self.level_complete:
                self.start_button.draw(screen)
            
            if self.level_complete:
                next_button = self.show_level_complete(screen)
            
            pygame.display.flip()
            clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
