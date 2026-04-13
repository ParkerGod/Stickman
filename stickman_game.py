# -*- coding: utf-8 -*-
import pygame
import math
import random
import sys

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
GREEN = (50, 255, 100)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (180, 100, 255)
CYAN = (0, 255, 255)
DARK_BLUE = (30, 60, 120)
GROUND_COLOR = (80, 60, 40)
PLATFORM_COLOR = (100, 80, 60)

GRAVITY = 0.8
FRICTION = 0.85
JUMP_FORCE = -15
WALL_SLIDE_FRICTION = 0.3
WALL_JUMP_FORCE_X = 12
WALL_JUMP_FORCE_Y = -12

BASE_SCROLL_SPEED = 3
MAX_SCROLL_SPEED = 8
SPEED_INCREMENT = 0.0005

ENERGY_MAX = 100
ENERGY_FILL_AMOUNT = 10
DASH_DURATION = 60
DASH_SPEED_MULTIPLIER = 2.5

JUMP_COOLDOWN = 10

LEVEL_TERRAIN = [
    {"type": "ground", "x": 0, "y": 500, "width": 3000, "height": 100},
    {"type": "platform", "x": 400, "y": 400, "width": 200, "height": 20},
    {"type": "platform", "x": 700, "y": 350, "width": 150, "height": 20},
    {"type": "platform", "x": 950, "y": 300, "width": 200, "height": 20},
    {"type": "ground", "x": 1200, "y": 500, "width": 800, "height": 100},
    {"type": "platform", "x": 1300, "y": 400, "width": 100, "height": 20},
    {"type": "platform", "x": 1500, "y": 350, "width": 150, "height": 20},
    {"type": "wall", "x": 1700, "y": 350, "width": 30, "height": 150},
    {"type": "platform", "x": 1800, "y": 300, "width": 100, "height": 20},
    {"type": "ground", "x": 2100, "y": 500, "width": 1500, "height": 100},
    {"type": "platform", "x": 2200, "y": 420, "width": 120, "height": 20},
    {"type": "wall", "x": 2400, "y": 300, "width": 30, "height": 200},
    {"type": "platform", "x": 2500, "y": 380, "width": 150, "height": 20},
    {"type": "platform", "x": 2750, "y": 320, "width": 100, "height": 20},
    {"type": "ground", "x": 3000, "y": 500, "width": 2000, "height": 100},
    {"type": "platform", "x": 3100, "y": 400, "width": 200, "height": 20},
    {"type": "wall", "x": 3400, "y": 350, "width": 30, "height": 150},
    {"type": "platform", "x": 3600, "y": 300, "width": 150, "height": 20},
    {"type": "ground", "x": 5000, "y": 500, "width": 3000, "height": 100},
]

LEVEL_SPIKES = [
    {"x": 600, "y": 480, "width": 60, "height": 20},
    {"x": 1100, "y": 480, "width": 80, "height": 20},
    {"x": 2000, "y": 480, "width": 60, "height": 20},
    {"x": 2900, "y": 480, "width": 80, "height": 20},
    {"x": 3800, "y": 480, "width": 60, "height": 20},
    {"x": 4500, "y": 480, "width": 100, "height": 20},
]

ENERGY_PARTICLE_SPAWN_INTERVAL = 120


class PhysicsEngine:
    def __init__(self):
        self.gravity = GRAVITY
        self.friction = FRICTION
        self.wall_slide_friction = WALL_SLIDE_FRICTION
    
    def apply_gravity(self, entity):
        if not entity.on_ground:
            if entity.is_wall_sliding:
                entity.vel_y = min(entity.vel_y + self.gravity * self.wall_slide_friction, 5)
            else:
                entity.vel_y += self.gravity
    
    def apply_friction(self, entity):
        if entity.on_ground:
            entity.vel_x *= self.friction
    
    def calculate_jump(self, entity, is_wall_jump=False, wall_direction=0):
        if is_wall_jump:
            entity.vel_y = WALL_JUMP_FORCE_Y
            entity.vel_x = wall_direction * WALL_JUMP_FORCE_X
        else:
            entity.vel_y = JUMP_FORCE
    
    def update_velocity(self, entity):
        entity.vel_x = max(-20, min(20, entity.vel_x))
        entity.vel_y = max(-25, min(25, entity.vel_y))


class StickmanRenderer:
    def __init__(self):
        self.head_radius = 12
        self.body_length = 30
        self.arm_length = 20
        self.leg_length = 25
        self.line_width = 3
    
    def draw(self, surface, x, y, animation_state, facing_right=True, is_dashing=False):
        color = CYAN if is_dashing else BLACK
        
        if animation_state == "running":
            self._draw_running(surface, x, y, color, facing_right)
        elif animation_state == "jumping":
            self._draw_jumping(surface, x, y, color, facing_right)
        elif animation_state == "wall_sliding":
            self._draw_wall_sliding(surface, x, y, color, facing_right)
        elif animation_state == "dashing":
            self._draw_dashing(surface, x, y, color, facing_right)
        else:
            self._draw_idle(surface, x, y, color, facing_right)
    
    def _draw_idle(self, surface, x, y, color, facing_right):
        head_y = y - self.body_length - self.head_radius
        pygame.draw.circle(surface, color, (int(x), int(head_y)), self.head_radius, self.line_width)
        
        shoulder_y = y - self.body_length + 5
        hip_y = y
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(x), int(hip_y)), self.line_width)
        
        arm_angle = 0.3
        if facing_right:
            left_arm_end = (x - self.arm_length * math.cos(arm_angle), shoulder_y + self.arm_length * math.sin(arm_angle))
            right_arm_end = (x + self.arm_length * math.cos(arm_angle), shoulder_y + self.arm_length * math.sin(arm_angle))
        else:
            left_arm_end = (x + self.arm_length * math.cos(arm_angle), shoulder_y + self.arm_length * math.sin(arm_angle))
            right_arm_end = (x - self.arm_length * math.cos(arm_angle), shoulder_y + self.arm_length * math.sin(arm_angle))
        
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(left_arm_end[0]), int(left_arm_end[1])), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(right_arm_end[0]), int(right_arm_end[1])), self.line_width)
        
        leg_spread = 8
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x - leg_spread), int(hip_y + self.leg_length)), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x + leg_spread), int(hip_y + self.leg_length)), self.line_width)
    
    def _draw_running(self, surface, x, y, color, facing_right):
        import time
        phase = (pygame.time.get_ticks() / 100) % (2 * math.pi)
        
        head_y = y - self.body_length - self.head_radius
        pygame.draw.circle(surface, color, (int(x), int(head_y)), self.head_radius, self.line_width)
        
        shoulder_y = y - self.body_length + 5
        hip_y = y
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(x), int(hip_y)), self.line_width)
        
        arm_swing = math.sin(phase) * 0.5
        left_arm_end = (x - self.arm_length * math.cos(arm_swing), shoulder_y + self.arm_length * math.sin(abs(arm_swing)))
        right_arm_end = (x + self.arm_length * math.cos(arm_swing), shoulder_y + self.arm_length * math.sin(abs(arm_swing)))
        
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(left_arm_end[0]), int(left_arm_end[1])), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(right_arm_end[0]), int(right_arm_end[1])), self.line_width)
        
        leg_swing = math.sin(phase) * 0.6
        left_leg_end_x = x - 10 * math.sin(leg_swing)
        left_leg_end_y = hip_y + self.leg_length * math.cos(leg_swing * 0.5)
        right_leg_end_x = x + 10 * math.sin(leg_swing)
        right_leg_end_y = hip_y + self.leg_length * math.cos(leg_swing * 0.5)
        
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(left_leg_end_x), int(left_leg_end_y)), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(right_leg_end_x), int(right_leg_end_y)), self.line_width)
    
    def _draw_jumping(self, surface, x, y, color, facing_right):
        head_y = y - self.body_length - self.head_radius
        pygame.draw.circle(surface, color, (int(x), int(head_y)), self.head_radius, self.line_width)
        
        shoulder_y = y - self.body_length + 5
        hip_y = y
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(x), int(hip_y)), self.line_width)
        
        arm_angle = 1.2
        left_arm_end = (x - self.arm_length * math.cos(arm_angle), shoulder_y - self.arm_length * math.sin(arm_angle) * 0.5)
        right_arm_end = (x + self.arm_length * math.cos(arm_angle), shoulder_y - self.arm_length * math.sin(arm_angle) * 0.5)
        
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(left_arm_end[0]), int(left_arm_end[1])), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(right_arm_end[0]), int(right_arm_end[1])), self.line_width)
        
        leg_spread = 15
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x - leg_spread), int(hip_y + self.leg_length * 0.8)), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x + leg_spread), int(hip_y + self.leg_length * 0.8)), self.line_width)
    
    def _draw_wall_sliding(self, surface, x, y, color, facing_right):
        head_y = y - self.body_length - self.head_radius
        pygame.draw.circle(surface, color, (int(x), int(head_y)), self.head_radius, self.line_width)
        
        shoulder_y = y - self.body_length + 5
        hip_y = y
        
        lean = 5 if facing_right else -5
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(x + lean), int(hip_y)), self.line_width)
        
        if facing_right:
            left_arm_end = (x + 15, shoulder_y)
            right_arm_end = (x - self.arm_length, shoulder_y + 5)
        else:
            left_arm_end = (x - self.arm_length, shoulder_y + 5)
            right_arm_end = (x + 15, shoulder_y)
        
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(left_arm_end[0]), int(left_arm_end[1])), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(right_arm_end[0]), int(right_arm_end[1])), self.line_width)
        
        pygame.draw.line(surface, color, (int(x + lean), int(hip_y)), (int(x - 5), int(hip_y + self.leg_length)), self.line_width)
        pygame.draw.line(surface, color, (int(x + lean), int(hip_y)), (int(x + 10), int(hip_y + self.leg_length * 0.7)), self.line_width)
    
    def _draw_dashing(self, surface, x, y, color, facing_right):
        head_y = y - self.body_length - self.head_radius
        pygame.draw.circle(surface, color, (int(x), int(head_y)), self.head_radius, self.line_width)
        
        shoulder_y = y - self.body_length + 5
        hip_y = y
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(x), int(hip_y)), self.line_width)
        
        arm_angle = 0.1
        direction = 1 if facing_right else -1
        left_arm_end = (x - direction * self.arm_length * 0.8, shoulder_y + self.arm_length * 0.3)
        right_arm_end = (x + direction * self.arm_length * 0.8, shoulder_y + self.arm_length * 0.3)
        
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(left_arm_end[0]), int(left_arm_end[1])), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(shoulder_y)), (int(right_arm_end[0]), int(right_arm_end[1])), self.line_width)
        
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x - direction * 15), int(hip_y + self.leg_length)), self.line_width)
        pygame.draw.line(surface, color, (int(x), int(hip_y)), (int(x + direction * 5), int(hip_y + self.leg_length * 0.9)), self.line_width)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.width = 30
        self.height = 60
        
        self.on_ground = False
        self.is_wall_sliding = False
        self.wall_direction = 0
        self.facing_right = True
        
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_cooldown = 0
        
        self.energy = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.is_invincible = False
        
        self.renderer = StickmanRenderer()
        self.animation_state = "idle"
        
        self.distance_traveled = 0
    
    def update(self, physics_engine, platforms, walls, scroll_speed):
        physics_engine.apply_gravity(self)
        physics_engine.apply_friction(self)
        
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
        
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.is_invincible = False
        
        old_x = self.x
        old_y = self.y
        
        self.x += self.vel_x
        self.check_collision_x(platforms, walls)
        
        self.y += self.vel_y
        self.check_collision_y(platforms, walls)
        
        physics_engine.update_velocity(self)
        
        self.update_animation_state()
        
        self.distance_traveled += scroll_speed
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height, self.width, self.height)
    
    def check_collision_x(self, platforms, walls):
        player_rect = self.get_rect()
        
        all_obstacles = platforms + walls
        
        for obstacle in all_obstacles:
            obs_rect = pygame.Rect(obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"])
            
            if player_rect.colliderect(obs_rect):
                if self.vel_x > 0:
                    self.x = obs_rect.left - self.width // 2
                    self.vel_x = 0
                    
                    if not self.on_ground and obstacle.get("type") == "wall":
                        self.is_wall_sliding = True
                        self.wall_direction = -1
                        self.facing_right = False
                elif self.vel_x < 0:
                    self.x = obs_rect.right + self.width // 2
                    self.vel_x = 0
                    
                    if not self.on_ground and obstacle.get("type") == "wall":
                        self.is_wall_sliding = True
                        self.wall_direction = 1
                        self.facing_right = True
    
    def check_collision_y(self, platforms, walls):
        self.on_ground = False
        
        player_rect = self.get_rect()
        
        all_obstacles = platforms + walls
        
        for obstacle in all_obstacles:
            obs_rect = pygame.Rect(obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"])
            
            if player_rect.colliderect(obs_rect):
                if self.vel_y > 0:
                    self.y = obs_rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0
                    self.is_wall_sliding = False
                elif self.vel_y < 0:
                    self.y = obs_rect.bottom + self.height
                    self.vel_y = 0
    
    def update_animation_state(self):
        if self.is_dashing:
            self.animation_state = "dashing"
        elif self.is_wall_sliding:
            self.animation_state = "wall_sliding"
        elif not self.on_ground:
            self.animation_state = "jumping"
        elif abs(self.vel_x) > 0.5:
            self.animation_state = "running"
        else:
            self.animation_state = "idle"
    
    def jump(self, physics_engine):
        if self.jump_cooldown > 0:
            return
        
        if self.is_wall_sliding:
            physics_engine.calculate_jump(self, is_wall_jump=True, wall_direction=self.wall_direction)
            self.is_wall_sliding = False
            self.jump_cooldown = JUMP_COOLDOWN
            self.facing_right = self.wall_direction > 0
        elif self.jump_count < self.max_jumps:
            physics_engine.calculate_jump(self)
            self.jump_count += 1
            self.jump_cooldown = JUMP_COOLDOWN
            self.on_ground = False
    
    def move_left(self):
        if not self.is_dashing:
            self.vel_x = -5
            self.facing_right = False
    
    def move_right(self):
        if not self.is_dashing:
            self.vel_x = 5
            self.facing_right = True
    
    def activate_dash(self):
        if self.energy >= ENERGY_MAX and not self.is_dashing:
            self.is_dashing = True
            self.is_invincible = True
            self.dash_timer = DASH_DURATION
            self.energy = 0
            direction = 1 if self.facing_right else -1
            self.vel_x = direction * 15
    
    def add_energy(self, amount):
        self.energy = min(ENERGY_MAX, self.energy + amount)
    
    def draw(self, surface, scroll_x):
        screen_x = self.x - scroll_x
        self.renderer.draw(surface, screen_x, self.y, self.animation_state, self.facing_right, self.is_dashing)


class Camera:
    def __init__(self):
        self.scroll_x = 0
        self.base_speed = BASE_SCROLL_SPEED
        self.current_speed = BASE_SCROLL_SPEED
    
    def update(self, distance_traveled):
        self.current_speed = min(MAX_SCROLL_SPEED, self.base_speed + distance_traveled * SPEED_INCREMENT)
        self.scroll_x += self.current_speed
    
    def reset(self):
        self.scroll_x = 0
        self.current_speed = BASE_SCROLL_SPEED


class Background:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bg1_x = 0
        self.bg2_x = width
        self.surface1 = self._create_background()
        self.surface2 = self._create_background()
    
    def _create_background(self):
        surface = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            ratio = y / self.height
            r = int(30 + ratio * 50)
            g = int(60 + ratio * 80)
            b = int(120 + ratio * 60)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))
        
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height // 2)
            size = random.randint(1, 3)
            pygame.draw.circle(surface, WHITE, (x, y), size)
        
        return surface
    
    def update(self, scroll_speed):
        self.bg1_x -= scroll_speed * 0.5
        self.bg2_x -= scroll_speed * 0.5
        
        if self.bg1_x <= -self.width:
            self.bg1_x = self.bg2_x + self.width
        if self.bg2_x <= -self.width:
            self.bg2_x = self.bg1_x + self.width
    
    def draw(self, surface):
        surface.blit(self.surface1, (self.bg1_x, 0))
        surface.blit(self.surface2, (self.bg2_x, 0))


class EnergyParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.collected = False
        self.glow_phase = random.random() * math.pi * 2
    
    def update(self):
        self.glow_phase += 0.1
    
    def draw(self, surface, scroll_x):
        if self.collected:
            return
        
        screen_x = self.x - scroll_x
        glow_size = int(self.radius + math.sin(self.glow_phase) * 3)
        
        for i in range(3):
            alpha = 100 - i * 30
            color = (255, 255, 100)
            pygame.draw.circle(surface, color, (int(screen_x), int(self.y)), glow_size + i * 3, 2)
        
        pygame.draw.circle(surface, YELLOW, (int(screen_x), int(self.y)), self.radius)
    
    def check_collision(self, player_rect, scroll_x):
        if self.collected:
            return False
        
        particle_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        return player_rect.colliderect(particle_rect)


class Terrain:
    def __init__(self):
        self.platforms = []
        self.walls = []
        self.spikes = []
        self._load_terrain()
    
    def _load_terrain(self):
        for terrain in LEVEL_TERRAIN:
            if terrain["type"] in ["ground", "platform"]:
                self.platforms.append(terrain)
            elif terrain["type"] == "wall":
                self.walls.append(terrain)
        
        self.spikes = LEVEL_SPIKES
    
    def draw(self, surface, scroll_x):
        for platform in self.platforms:
            screen_x = platform["x"] - scroll_x
            if -platform["width"] <= screen_x <= SCREEN_WIDTH + platform["width"]:
                color = GROUND_COLOR if platform["type"] == "ground" else PLATFORM_COLOR
                pygame.draw.rect(surface, color, (screen_x, platform["y"], platform["width"], platform["height"]))
                pygame.draw.rect(surface, (color[0] + 20, color[1] + 20, color[2] + 20), 
                               (screen_x, platform["y"], platform["width"], platform["height"]), 2)
        
        for wall in self.walls:
            screen_x = wall["x"] - scroll_x
            if -wall["width"] <= screen_x <= SCREEN_WIDTH + wall["width"]:
                pygame.draw.rect(surface, (100, 100, 100), (screen_x, wall["y"], wall["width"], wall["height"]))
                pygame.draw.rect(surface, (150, 150, 150), (screen_x, wall["y"], wall["width"], wall["height"]), 2)
        
        for spike in self.spikes:
            screen_x = spike["x"] - scroll_x
            if -spike["width"] <= screen_x <= SCREEN_WIDTH + spike["width"]:
                self._draw_spike(surface, screen_x, spike["y"], spike["width"], spike["height"])
    
    def _draw_spike(self, surface, x, y, width, height):
        num_spikes = width // 20
        spike_width = width // num_spikes
        
        for i in range(num_spikes):
            points = [
                (x + i * spike_width, y + height),
                (x + i * spike_width + spike_width // 2, y),
                (x + (i + 1) * spike_width, y + height)
            ]
            pygame.draw.polygon(surface, RED, points)
            pygame.draw.polygon(surface, (200, 0, 0), points, 2)


class EnergyBar:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self, surface, energy):
        pygame.draw.rect(surface, (50, 50, 50), (self.x - 2, self.y - 2, self.width + 4, self.height + 4))
        pygame.draw.rect(surface, (30, 30, 30), (self.x, self.y, self.width, self.height))
        
        fill_width = int((energy / ENERGY_MAX) * self.width)
        if fill_width > 0:
            color = CYAN if energy >= ENERGY_MAX else YELLOW
            pygame.draw.rect(surface, color, (self.x, self.y, fill_width, self.height))
        
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height), 2)
        
        font = pygame.font.Font(None, 24)
        text = font.render("ENERGY", True, WHITE)
        surface.blit(text, (self.x, self.y - 20))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Stickman Runner")
        self.clock = pygame.time.Clock()
        
        self.physics_engine = PhysicsEngine()
        self.camera = Camera()
        self.background = Background(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.terrain = Terrain()
        self.energy_bar = EnergyBar(50, SCREEN_HEIGHT - 50, 200, 20)
        
        self.player = Player(200, 400)
        
        self.energy_particles = []
        self.particle_spawn_timer = 0
        
        self.game_over = False
        self.distance = 0
        
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
    
    def reset(self):
        self.player = Player(200, 400)
        self.camera.reset()
        self.energy_particles = []
        self.particle_spawn_timer = 0
        self.game_over = False
        self.distance = 0
    
    def spawn_energy_particle(self):
        spawn_x = self.camera.scroll_x + SCREEN_WIDTH + 100
        spawn_y = random.randint(250, 450)
        self.energy_particles.append(EnergyParticle(spawn_x, spawn_y))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    if not self.game_over:
                        self.player.jump(self.physics_engine)
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if not self.game_over:
                        self.player.activate_dash()
                elif event.key == pygame.K_r:
                    if self.game_over:
                        self.reset()
                elif event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def update(self):
        if self.game_over:
            return
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move_left()
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move_right()
        
        self.camera.update(self.player.distance_traveled)
        self.background.update(self.camera.current_speed)
        
        self.player.update(self.physics_engine, self.terrain.platforms, self.terrain.walls, self.camera.current_speed)
        
        self.particle_spawn_timer += 1
        if self.particle_spawn_timer >= ENERGY_PARTICLE_SPAWN_INTERVAL:
            self.spawn_energy_particle()
            self.particle_spawn_timer = 0
        
        player_rect = self.player.get_rect()
        for particle in self.energy_particles:
            particle.update()
            if particle.check_collision(player_rect, self.camera.scroll_x):
                particle.collected = True
                self.player.add_energy(ENERGY_FILL_AMOUNT)
        
        self.energy_particles = [p for p in self.energy_particles if not p.collected and p.x > self.camera.scroll_x - 100]
        
        for spike in self.terrain.spikes:
            spike_rect = pygame.Rect(spike["x"], spike["y"], spike["width"], spike["height"])
            if player_rect.colliderect(spike_rect) and not self.player.is_invincible:
                self.game_over = True
        
        if self.player.x < self.camera.scroll_x - 50:
            self.game_over = True
        
        self.distance = int(self.player.distance_traveled / 10)
    
    def draw(self):
        self.background.draw(self.screen)
        
        self.terrain.draw(self.screen, self.camera.scroll_x)
        
        for particle in self.energy_particles:
            particle.draw(self.screen, self.camera.scroll_x)
        
        self.player.draw(self.screen, self.camera.scroll_x)
        
        self.energy_bar.draw(self.screen, self.player.energy)
        
        distance_text = self.small_font.render(f"Distance: {self.distance}m", True, WHITE)
        self.screen.blit(distance_text, (SCREEN_WIDTH - 200, 20))
        
        speed_text = self.small_font.render(f"Speed: {self.camera.current_speed:.1f}", True, WHITE)
        self.screen.blit(speed_text, (SCREEN_WIDTH - 200, 50))
        
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        distance_text = self.font.render(f"Distance: {self.distance}m", True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(distance_text, distance_rect)
        
        restart_text = self.small_font.render("Press R to Restart", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
