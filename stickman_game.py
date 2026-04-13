# -*- coding: utf-8 -*-
import pygame
import sys
import math
import random

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.6
FRICTION = 0.85
GROUND_Y = SCREEN_HEIGHT - 80
PLAYER_SPEED = 5
JUMP_FORCE = -14
DOUBLE_JUMP_FORCE = -12
WALL_SLIDE_SPEED = 2
DASH_DURATION = 60
DASH_SPEED = 15
ENERGY_MAX = 100
ENERGY_PER_PARTICLE = 20

LEVEL_DATA = [
    {"x": 0, "width": 500, "height": 80, "type": "ground"},
    {"x": 600, "width": 200, "height": 80, "type": "ground"},
    {"x": 900, "width": 150, "height": 120, "type": "ground"},
    {"x": 1150, "width": 100, "height": 80, "type": "ground"},
    {"x": 1350, "width": 300, "height": 80, "type": "ground"},
    {"x": 1750, "width": 150, "height": 160, "type": "ground"},
    {"x": 2000, "width": 200, "height": 80, "type": "ground"},
    {"x": 2300, "width": 100, "height": 200, "type": "wall"},
    {"x": 2500, "width": 250, "height": 80, "type": "ground"},
    {"x": 2850, "width": 100, "height": 80, "type": "ground"},
    {"x": 3050, "width": 200, "height": 80, "type": "ground"},
    {"x": 3350, "width": 150, "height": 180, "type": "wall"},
    {"x": 3600, "width": 300, "height": 80, "type": "ground"},
    {"x": 4000, "width": 200, "height": 80, "type": "ground"},
]

SPIKE_DATA = [
    {"x": 550, "width": 40, "height": 30},
    {"x": 1100, "width": 40, "height": 30},
    {"x": 1700, "width": 40, "height": 30},
    {"x": 2450, "width": 40, "height": 30},
    {"x": 3000, "width": 40, "height": 30},
    {"x": 3550, "width": 40, "height": 30},
]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("火柴人跑酷")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Microsoft YaHei", 36)
font_large = pygame.font.SysFont("Microsoft YaHei", 72)


class PhysicsEngine:
    def __init__(self):
        self.gravity = GRAVITY
        self.friction = FRICTION

    def apply_gravity(self, velocity_y):
        return velocity_y + self.gravity

    def apply_friction(self, velocity_x):
        return velocity_x * self.friction

    def calculate_jump_velocity(self, jump_force, time_in_air=0):
        return jump_force + (self.gravity * time_in_air * 0.5)

    def calculate_wall_slide(self, velocity_y):
        return min(velocity_y, WALL_SLIDE_SPEED)

    def check_collision(self, rect1, rect2):
        return rect1.colliderect(rect2)

    def resolve_collision(self, player_rect, platform_rect, velocity_x, velocity_y):
        overlap_x = min(player_rect.right - platform_rect.left, platform_rect.right - player_rect.left)
        overlap_y = min(player_rect.bottom - platform_rect.top, platform_rect.bottom - player_rect.top)

        if overlap_x < overlap_y:
            if velocity_x > 0:
                player_rect.right = platform_rect.left
                collision_side = "right"
            else:
                player_rect.left = platform_rect.right
                collision_side = "left"
            velocity_x = 0
        else:
            if velocity_y > 0:
                player_rect.bottom = platform_rect.top
                collision_side = "bottom"
            else:
                player_rect.top = platform_rect.bottom
                collision_side = "top"
            velocity_y = 0

        return velocity_x, velocity_y, collision_side


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.collected = False
        self.glow_phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.glow_phase += 0.1

    def draw(self, surface, scroll_x):
        if not self.collected:
            glow = int(150 + 100 * math.sin(self.glow_phase))
            draw_x = self.x - scroll_x
            pygame.draw.circle(surface, (glow, glow, 0), (draw_x, self.y), self.radius + 4)
            pygame.draw.circle(surface, (255, 255, 0), (draw_x, self.y), self.radius)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 60
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_cooldown = 0
        self.cooldown_max = 15
        self.on_wall = False
        self.wall_side = None
        self.wall_slide = False
        self.energy = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_direction = 1
        self.invincible = False
        self.animation_frame = 0
        self.joints = self._init_joints()

    def _init_joints(self):
        return {
            "head": (0, -25),
            "shoulders": (0, -10),
            "elbow_left": (-15, 0),
            "elbow_right": (15, 0),
            "hand_left": (-20, 10),
            "hand_right": (20, 10),
            "hip": (0, 10),
            "knee_left": (-10, 30),
            "knee_right": (10, 30),
            "foot_left": (-15, 50),
            "foot_right": (15, 50),
        }

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height, self.width, self.height)

    def update_animation(self):
        self.animation_frame += 0.15
        run_cycle = math.sin(self.animation_frame)

        if self.on_ground and abs(self.velocity_x) > 0.5:
            self.joints["knee_left"] = (-10 + run_cycle * 8, 25 + abs(run_cycle) * 10)
            self.joints["knee_right"] = (10 - run_cycle * 8, 25 + abs(run_cycle) * 10)
            self.joints["foot_left"] = (-15 + run_cycle * 12, 50 + run_cycle * 5)
            self.joints["foot_right"] = (15 - run_cycle * 12, 50 - run_cycle * 5)
            self.joints["elbow_left"] = (-15 - run_cycle * 5, 0)
            self.joints["elbow_right"] = (15 + run_cycle * 5, 0)
        elif self.wall_slide:
            self.joints["knee_left"] = (-5, 25)
            self.joints["knee_right"] = (5, 35)
            self.joints["foot_left"] = (-20, 45)
            self.joints["foot_right"] = (0, 55)
        elif not self.on_ground:
            jump_phase = min(1, abs(self.velocity_y) / 10)
            self.joints["knee_left"] = (-15, 20 + jump_phase * 10)
            self.joints["knee_right"] = (15, 20 + jump_phase * 10)
            self.joints["foot_left"] = (-20, 40 - jump_phase * 5)
            self.joints["foot_right"] = (20, 40 - jump_phase * 5)
            self.joints["elbow_left"] = (-20, -5)
            self.joints["elbow_right"] = (20, -5)
        else:
            self.joints = self._init_joints()

    def jump(self):
        if self.jump_cooldown > 0:
            return

        if self.wall_slide:
            self.velocity_y = DOUBLE_JUMP_FORCE
            self.velocity_x = DASH_SPEED * (-1 if self.wall_side == "right" else 1)
            self.wall_slide = False
            self.on_wall = False
            self.jump_count = 1
            self.jump_cooldown = self.cooldown_max
        elif self.on_ground:
            self.velocity_y = JUMP_FORCE
            self.jump_count = 1
            self.on_ground = False
            self.jump_cooldown = self.cooldown_max
        elif self.jump_count < self.max_jumps:
            self.velocity_y = DOUBLE_JUMP_FORCE
            self.jump_count += 1
            self.jump_cooldown = self.cooldown_max

    def dash(self):
        if self.energy >= ENERGY_MAX and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = DASH_DURATION
            self.energy = 0
            self.invincible = True
            self.dash_direction = 1

    def update(self, physics_engine, platforms, spikes, particles, scroll_x):
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        if self.is_dashing:
            self.dash_timer -= 1
            self.velocity_x = self.dash_direction * DASH_SPEED
            self.velocity_y = 0
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.invincible = False
        else:
            self.velocity_x = physics_engine.apply_friction(self.velocity_x)
            self.velocity_y = physics_engine.apply_gravity(self.velocity_y)

            if self.wall_slide:
                self.velocity_y = physics_engine.calculate_wall_slide(self.velocity_y)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity_x = max(self.velocity_x - 0.8, -PLAYER_SPEED)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity_x = min(self.velocity_x + 0.8, PLAYER_SPEED)

        self.x += self.velocity_x
        self.y += self.velocity_y

        self.on_ground = False
        self.on_wall = False
        self.wall_slide = False

        player_rect = self.get_rect()

        for platform in platforms:
            if physics_engine.check_collision(player_rect, platform["rect"]):
                self.velocity_x, self.velocity_y, side = physics_engine.resolve_collision(
                    player_rect, platform["rect"], self.velocity_x, self.velocity_y
                )
                self.x = player_rect.centerx
                self.y = player_rect.bottom

                if side == "bottom":
                    self.on_ground = True
                    self.jump_count = 0
                elif side in ["left", "right"] and not self.on_ground and self.velocity_y > 0:
                    self.on_wall = True
                    self.wall_side = side
                    self.wall_slide = True
                    self.jump_count = 0

        if not self.invincible:
            for spike in spikes:
                spike_rect = pygame.Rect(spike["x"], spike["y"], spike["width"], spike["height"])
                if player_rect.colliderect(spike_rect):
                    return "death"

        for particle in particles:
            if not particle.collected:
                dist = math.hypot(self.x - particle.x, self.y - particle.y)
                if dist < 30:
                    particle.collected = True
                    self.energy = min(self.energy + ENERGY_PER_PARTICLE, ENERGY_MAX)

        if self.x - scroll_x < -50 or self.y > SCREEN_HEIGHT + 100:
            return "death"

        self.update_animation()
        return "alive"

    def draw(self, surface, scroll_x):
        draw_x = self.x - scroll_x
        base_y = self.y

        if self.invincible:
            color = (255, 215, 0)
            glow_radius = 40
            pygame.draw.circle(surface, (255, 255, 200, 100), (draw_x, base_y - 25), glow_radius)
        else:
            color = (0, 0, 0)

        joint_pos = {}
        for joint, (offset_x, offset_y) in self.joints.items():
            joint_pos[joint] = (draw_x + offset_x, base_y + offset_y - 30)

        head_center = joint_pos["head"]
        pygame.draw.circle(surface, color, head_center, 12, 2)

        pygame.draw.line(surface, color, joint_pos["shoulders"], joint_pos["hip"], 3)

        pygame.draw.line(surface, color, joint_pos["shoulders"], joint_pos["elbow_left"], 2)
        pygame.draw.line(surface, color, joint_pos["elbow_left"], joint_pos["hand_left"], 2)
        pygame.draw.line(surface, color, joint_pos["shoulders"], joint_pos["elbow_right"], 2)
        pygame.draw.line(surface, color, joint_pos["elbow_right"], joint_pos["hand_right"], 2)

        pygame.draw.line(surface, color, joint_pos["hip"], joint_pos["knee_left"], 2)
        pygame.draw.line(surface, color, joint_pos["knee_left"], joint_pos["foot_left"], 2)
        pygame.draw.line(surface, color, joint_pos["hip"], joint_pos["knee_right"], 2)
        pygame.draw.line(surface, color, joint_pos["knee_right"], joint_pos["foot_right"], 2)


class Game:
    def __init__(self):
        self.physics_engine = PhysicsEngine()
        self.player = Player(200, GROUND_Y)
        self.scroll_x = 0
        self.scroll_speed = 2
        self.base_scroll_speed = 2
        self.max_scroll_speed = 6
        self.distance = 0
        self.game_over = False
        self.platforms = []
        self.spikes = []
        self.particles = []
        self.bg_surface1 = self._create_background()
        self.bg_surface2 = self._create_background()
        self.bg_x1 = 0
        self.bg_x2 = SCREEN_WIDTH

        self._generate_level()
        self._generate_particles()

    def _create_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill((135, 206, 235))
        for i in range(5):
            cloud_x = random.randint(0, SCREEN_WIDTH)
            cloud_y = random.randint(50, 200)
            pygame.draw.circle(bg, (255, 255, 255), (cloud_x, cloud_y), 30)
            pygame.draw.circle(bg, (255, 255, 255), (cloud_x + 30, cloud_y), 35)
            pygame.draw.circle(bg, (255, 255, 255), (cloud_x - 20, cloud_y + 10), 25)
        pygame.draw.rect(bg, (34, 139, 34), (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        return bg

    def _generate_level(self):
        self.platforms = []
        for data in LEVEL_DATA:
            rect = pygame.Rect(data["x"], SCREEN_HEIGHT - data["height"], data["width"], data["height"])
            self.platforms.append({"rect": rect, "type": data["type"]})

        self.spikes = []
        for data in SPIKE_DATA:
            self.spikes.append({
                "x": data["x"],
                "y": SCREEN_HEIGHT - 80 - data["height"],
                "width": data["width"],
                "height": data["height"]
            })

    def _generate_particles(self):
        self.particles = []
        for i in range(20):
            x = 400 + i * 250
            y = random.randint(SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 120)
            self.particles.append(Particle(x, y))

    def update_dynamic_difficulty(self):
        self.scroll_speed = min(
            self.base_scroll_speed + (self.distance / 5000) * (self.max_scroll_speed - self.base_scroll_speed),
            self.max_scroll_speed
        )

    def update(self):
        if self.game_over:
            return

        self.scroll_x += self.scroll_speed
        self.distance = int(self.scroll_x / 10)
        self.update_dynamic_difficulty()

        self.bg_x1 -= self.scroll_speed * 0.5
        self.bg_x2 -= self.scroll_speed * 0.5

        if self.bg_x1 <= -SCREEN_WIDTH:
            self.bg_x1 = self.bg_x2 + SCREEN_WIDTH
        if self.bg_x2 <= -SCREEN_WIDTH:
            self.bg_x2 = self.bg_x1 + SCREEN_WIDTH

        result = self.player.update(self.physics_engine, self.platforms, self.spikes, self.particles, self.scroll_x)

        if result == "death":
            self.game_over = True

        for particle in self.particles:
            particle.update()

        for platform in self.platforms:
            if platform["rect"].x + platform["rect"].width < self.scroll_x - 200:
                new_x = platform["rect"].x + 5000
                new_height = random.choice([80, 100, 120, 150, 180])
                platform["rect"].x = new_x
                platform["rect"].y = SCREEN_HEIGHT - new_height
                platform["rect"].height = new_height

        for spike in self.spikes:
            if spike["x"] + spike["width"] < self.scroll_x - 200:
                spike["x"] = spike["x"] + 5000

        for particle in self.particles:
            if particle.x < self.scroll_x - 200 or particle.collected:
                particle.x = particle.x + 5500
                particle.y = random.randint(SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 120)
                particle.collected = False

    def draw_spike(self, surface, spike, scroll_x):
        x = spike["x"] - scroll_x
        y = spike["y"]
        points = [(x, y + spike["height"]), (x + spike["width"] // 2, y), (x + spike["width"], y + spike["height"])]
        pygame.draw.polygon(surface, (200, 0, 0), points)
        pygame.draw.polygon(surface, (100, 0, 0), points, 2)

    def draw_energy_bar(self, surface):
        bar_width = 200
        bar_height = 20
        bar_x = 50
        bar_y = SCREEN_HEIGHT - 40

        pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height), 2)

        energy_width = int((self.player.energy / ENERGY_MAX) * (bar_width - 4))
        if self.player.energy >= ENERGY_MAX:
            color = (0, 255, 255)
        else:
            color = (0, 200, 255)
        pygame.draw.rect(surface, color, (bar_x + 2, bar_y + 2, energy_width, bar_height - 4))

        text = font.render("能量", True, (255, 255, 255))
        surface.blit(text, (bar_x + bar_width + 10, bar_y - 5))

        if self.player.energy >= ENERGY_MAX:
            hint = font.render("按 Shift 冲刺!", True, (0, 255, 255))
            surface.blit(hint, (bar_x + bar_width + 80, bar_y - 5))

    def draw(self, surface):
        surface.blit(self.bg_surface1, (self.bg_x1, 0))
        surface.blit(self.bg_surface2, (self.bg_x2, 0))

        for platform in self.platforms:
            draw_rect = platform["rect"].copy()
            draw_rect.x -= self.scroll_x
            if draw_rect.right > 0 and draw_rect.left < SCREEN_WIDTH:
                pygame.draw.rect(surface, (139, 69, 19), draw_rect)
                pygame.draw.rect(surface, (100, 50, 10), draw_rect, 2)

        for spike in self.spikes:
            if spike["x"] - self.scroll_x > -50 and spike["x"] - self.scroll_x < SCREEN_WIDTH + 50:
                self.draw_spike(surface, spike, self.scroll_x)

        for particle in self.particles:
            particle.draw(surface, self.scroll_x)

        self.player.draw(surface, self.scroll_x)

        distance_text = font.render(f"距离: {self.distance} 米", True, (255, 255, 255))
        surface.blit(distance_text, (SCREEN_WIDTH - 200, 20))

        speed_text = font.render(f"速度: {self.scroll_speed:.1f}", True, (255, 255, 255))
        surface.blit(speed_text, (SCREEN_WIDTH - 200, 60))

        self.draw_energy_bar(surface)

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            game_over_text = font_large.render("游戏结束!", True, (255, 50, 50))
            surface.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100))

            final_text = font_large.render(f"总距离: {self.distance} 米", True, (255, 255, 255))
            surface.blit(final_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))

            restart_text = font.render("按 R 键重新开始", True, (200, 200, 200))
            surface.blit(restart_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 80))

    def reset(self):
        self.player = Player(200, GROUND_Y)
        self.scroll_x = 0
        self.scroll_speed = self.base_scroll_speed
        self.distance = 0
        self.game_over = False
        self.platforms = []
        self.spikes = []
        self.particles = []
        self._generate_level()
        self._generate_particles()


def main():
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                    game.player.jump()
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    game.player.dash()
                if event.key == pygame.K_r and game.game_over:
                    game.reset()
                if event.key == pygame.K_ESCAPE:
                    running = False

        game.update()

        screen.fill((135, 206, 235))
        game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
