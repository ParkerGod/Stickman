#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火柴人跑酷游戏
使用 Python 3.9 和 Pygame 2.5.2
"""

import pygame
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# 初始化 Pygame
pygame.init()

# ==================== 常量定义 ====================

# 窗口设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
SKIN_COLOR = (255, 220, 177)

# 物理常量
GRAVITY = 0.6
FRICTION = 0.85
AIR_RESISTANCE = 0.98
JUMP_STRENGTH = -14
DOUBLE_JUMP_STRENGTH = -12
WALL_SLIDE_SPEED = 2
WALL_JUMP_STRENGTH_X = 10
WALL_JUMP_STRENGTH_Y = -12

# 玩家常量
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 60
PLAYER_SPEED = 5
DASH_SPEED = 15
DASH_DURATION = 30  # 帧数
DASH_COOLDOWN = 60

# 能量系统
MAX_ENERGY = 100
ENERGY_PER_PARTICLE = 20
DASH_ENERGY_COST = 100

# 摄像机滚动
INITIAL_SCROLL_SPEED = 3
MAX_SCROLL_SPEED = 8
SCROLL_ACCELERATION = 0.001

# 关卡地形数据 (高度、长度、障碍物类型)
# 格式: [(地面高度, 长度, 障碍物类型), ...]
LEVEL_DATA: List[Tuple[int, int, Optional[str]]] = [
    (500, 800, None),           # 起始平地
    (500, 400, "spike"),        # 尖刺地带
    (450, 600, None),           # 上坡
    (400, 500, "platform"),     # 平台跳跃
    (400, 300, "spike"),        # 尖刺
    (350, 700, None),           # 更高平台
    (450, 400, "wall"),         # 墙
    (500, 600, None),           # 下坡
    (550, 500, "spike"),        # 尖刺
    (500, 1000, None),          # 长平地
    (450, 500, "platform"),     # 平台
    (400, 600, "wall"),         # 墙
    (500, 800, "spike"),        # 尖刺地带
    (550, 1000, None),          # 结束区域
]

# ==================== 枚举类 ====================

class PlayerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    JUMPING = "jumping"
    FALLING = "falling"
    WALL_SLIDING = "wall_sliding"
    DASHING = "dashing"

class ObstacleType(Enum):
    SPIKE = "spike"
    PLATFORM = "platform"
    WALL = "wall"

# ==================== 物理引擎类 ====================

class PhysicsEngine:
    """物理引擎 - 负责重力、摩擦力及跳跃弧线的数学计算"""
    
    def __init__(self):
        self.gravity = GRAVITY
        self.friction = FRICTION
        self.air_resistance = AIR_RESISTANCE
    
    def apply_gravity(self, velocity_y: float) -> float:
        """应用重力"""
        return velocity_y + self.gravity
    
    def apply_friction(self, velocity_x: float, on_ground: bool) -> float:
        """应用摩擦力/空气阻力"""
        if on_ground:
            return velocity_x * self.friction
        else:
            return velocity_x * self.air_resistance
    
    def calculate_jump_velocity(self, jump_strength: float) -> float:
        """计算跳跃初速度"""
        return jump_strength
    
    def calculate_wall_slide_velocity(self, velocity_y: float) -> float:
        """计算滑墙下落速度"""
        return min(velocity_y + self.gravity * 0.3, WALL_SLIDE_SPEED)
    
    def calculate_wall_jump_velocity(self, direction: int) -> Tuple[float, float]:
        """计算蹬墙跳速度 (vx, vy)"""
        return (direction * WALL_JUMP_STRENGTH_X, WALL_JUMP_STRENGTH_Y)
    
    def check_collision(self, rect: pygame.Rect, obstacles: List[pygame.Rect]) -> Optional[pygame.Rect]:
        """检测碰撞"""
        for obstacle in obstacles:
            if rect.colliderect(obstacle):
                return obstacle
        return None
    
    def resolve_collision(self, rect: pygame.Rect, obstacle: pygame.Rect, 
                         velocity_x: float, velocity_y: float) -> Tuple[pygame.Rect, bool, bool]:
        """
        解决碰撞，返回新的位置、是否在地面上、是否撞墙
        """
        on_ground = False
        on_wall = False
        
        # 计算重叠
        overlap_left = (rect.right - obstacle.left) if velocity_x > 0 else 0
        overlap_right = (obstacle.right - rect.left) if velocity_x < 0 else 0
        overlap_top = (rect.bottom - obstacle.top) if velocity_y > 0 else 0
        overlap_bottom = (obstacle.bottom - rect.top) if velocity_y < 0 else 0
        
        # 找出最小重叠
        overlaps = []
        if overlap_left > 0:
            overlaps.append((overlap_left, 'left'))
        if overlap_right > 0:
            overlaps.append((overlap_right, 'right'))
        if overlap_top > 0:
            overlaps.append((overlap_top, 'top'))
        if overlap_bottom > 0:
            overlaps.append((overlap_bottom, 'bottom'))
        
        if overlaps:
            min_overlap, direction = min(overlaps, key=lambda x: x[0])
            
            if direction == 'top':
                rect.bottom = obstacle.top
                on_ground = True
            elif direction == 'bottom':
                rect.top = obstacle.bottom
            elif direction == 'left':
                rect.right = obstacle.left
                on_wall = True
            elif direction == 'right':
                rect.left = obstacle.right
                on_wall = True
        
        return rect, on_ground, on_wall

# ==================== 火柴人类 ====================

class StickMan:
    """火柴人绘制类 - 基于坐标点的绘制逻辑"""
    
    def __init__(self):
        self.joints = {
            'head': (0, -25),
            'neck': (0, -15),
            'shoulder': (0, -10),
            'elbow_l': (-8, -5),
            'hand_l': (-12, 5),
            'elbow_r': (8, -5),
            'hand_r': (12, 5),
            'hip': (0, 5),
            'knee_l': (-6, 20),
            'foot_l': (-8, 35),
            'knee_r': (6, 20),
            'foot_r': (8, 35),
        }
        self.animation_frame = 0
        self.facing_right = True
    
    def update_animation(self, state: PlayerState, frame: int):
        """更新关节位置以创建动画"""
        self.animation_frame = frame
        
        # 重置关节位置
        base_joints = {
            'head': (0, -25),
            'neck': (0, -15),
            'shoulder': (0, -10),
            'elbow_l': (-8, -5),
            'hand_l': (-12, 5),
            'elbow_r': (8, -5),
            'hand_r': (12, 5),
            'hip': (0, 5),
            'knee_l': (-6, 20),
            'foot_l': (-8, 35),
            'knee_r': (6, 20),
            'foot_r': (8, 35),
        }
        
        if state == PlayerState.RUNNING:
            # 跑步动画
            cycle = frame % 20
            phase = math.sin(cycle * math.pi / 10)
            
            base_joints['knee_l'] = (-6 + phase * 4, 20)
            base_joints['foot_l'] = (-8 + phase * 6, 35 - abs(phase) * 5)
            base_joints['knee_r'] = (6 - phase * 4, 20)
            base_joints['foot_r'] = (8 - phase * 6, 35 - abs(phase) * 5)
            
            base_joints['elbow_l'] = (-8, -5 + phase * 3)
            base_joints['hand_l'] = (-12, 5 + phase * 4)
            base_joints['elbow_r'] = (8, -5 - phase * 3)
            base_joints['hand_r'] = (12, 5 - phase * 4)
            
        elif state == PlayerState.JUMPING:
            # 跳跃动画
            base_joints['knee_l'] = (-8, 15)
            base_joints['foot_l'] = (-10, 25)
            base_joints['knee_r'] = (8, 18)
            base_joints['foot_r'] = (12, 28)
            
            base_joints['elbow_l'] = (-10, -8)
            base_joints['hand_l'] = (-15, -15)
            base_joints['elbow_r'] = (10, -2)
            base_joints['hand_r'] = (15, 5)
            
        elif state == PlayerState.FALLING:
            # 下落动画
            base_joints['knee_l'] = (-6, 22)
            base_joints['foot_l'] = (-8, 32)
            base_joints['knee_r'] = (6, 22)
            base_joints['foot_r'] = (8, 32)
            
            base_joints['elbow_l'] = (-8, -2)
            base_joints['hand_l'] = (-12, 8)
            base_joints['elbow_r'] = (8, -8)
            base_joints['hand_r'] = (12, -15)
            
        elif state == PlayerState.WALL_SLIDING:
            # 滑墙动画
            base_joints['knee_l'] = (-10, 18)
            base_joints['foot_l'] = (-12, 32)
            base_joints['knee_r'] = (4, 20)
            base_joints['foot_r'] = (6, 35)
            
            base_joints['elbow_l'] = (-12, -8)
            base_joints['hand_l'] = (-16, 0)
            base_joints['elbow_r'] = (6, -5)
            base_joints['hand_r'] = (10, 5)
            
        elif state == PlayerState.DASHING:
            # 冲刺动画
            base_joints['knee_l'] = (-4, 20)
            base_joints['foot_l'] = (-6, 35)
            base_joints['knee_r'] = (4, 20)
            base_joints['foot_r'] = (6, 35)
            
            base_joints['elbow_l'] = (-6, -8)
            base_joints['hand_l'] = (-10, -15)
            base_joints['elbow_r'] = (6, -8)
            base_joints['hand_r'] = (10, -15)
        
        self.joints = base_joints
    
    def draw(self, surface: pygame.Surface, x: int, y: int, facing_right: bool = True):
        """绘制火柴人"""
        self.facing_right = facing_right
        
        # 计算翻转
        flip = 1 if facing_right else -1
        
        def transform_point(point):
            px, py = point
            return (int(x + px * flip), int(y + py))
        
        # 获取变换后的关节位置
        head = transform_point(self.joints['head'])
        neck = transform_point(self.joints['neck'])
        shoulder = transform_point(self.joints['shoulder'])
        elbow_l = transform_point(self.joints['elbow_l'])
        hand_l = transform_point(self.joints['hand_l'])
        elbow_r = transform_point(self.joints['elbow_r'])
        hand_r = transform_point(self.joints['hand_r'])
        hip = transform_point(self.joints['hip'])
        knee_l = transform_point(self.joints['knee_l'])
        foot_l = transform_point(self.joints['foot_l'])
        knee_r = transform_point(self.joints['knee_r'])
        foot_r = transform_point(self.joints['foot_r'])
        
        # 绘制线条 (身体)
        line_width = 3
        
        # 头
        pygame.draw.circle(surface, SKIN_COLOR, head, 8)
        pygame.draw.circle(surface, BLACK, head, 8, 2)
        
        # 躯干
        pygame.draw.line(surface, BLACK, neck, hip, line_width)
        
        # 左臂
        pygame.draw.line(surface, BLACK, shoulder, elbow_l, line_width)
        pygame.draw.line(surface, BLACK, elbow_l, hand_l, line_width)
        
        # 右臂
        pygame.draw.line(surface, BLACK, shoulder, elbow_r, line_width)
        pygame.draw.line(surface, BLACK, elbow_r, hand_r, line_width)
        
        # 左腿
        pygame.draw.line(surface, BLACK, hip, knee_l, line_width)
        pygame.draw.line(surface, BLACK, knee_l, foot_l, line_width)
        
        # 右腿
        pygame.draw.line(surface, BLACK, hip, knee_r, line_width)
        pygame.draw.line(surface, BLACK, knee_r, foot_r, line_width)

# ==================== 玩家类 ====================

class Player:
    """玩家类 - 处理输入和状态管理"""
    
    def __init__(self, x: int, y: int, physics: PhysicsEngine):
        self.physics = physics
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vx = 0
        self.vy = 0
        self.state = PlayerState.IDLE
        self.stickman = StickMan()
        self.animation_frame = 0
        
        # 跳跃相关
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_cooldown = 0
        self.jump_cooldown_max = 10
        
        # 滑墙相关
        self.wall_slide_timer = 0
        self.wall_direction = 0  # -1 左, 1 右
        
        # 冲刺相关
        self.energy = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = 1
        
        # 无敌状态
        self.invincible = False
        self.invincible_timer = 0
        
        # 地面状态
        self.on_ground = False
        self.on_wall = False
    
    def update(self, keys, obstacles: List[pygame.Rect]):
        """更新玩家状态"""
        # 更新冷却
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # 处理输入
        self._handle_input(keys)
        
        # 应用物理
        self._apply_physics()
        
        # 移动和碰撞检测
        self._move_and_collide(obstacles)
        
        # 更新动画
        self._update_animation()
    
    def _handle_input(self, keys):
        """处理键盘输入"""
        # 左右移动
        if not self.is_dashing:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -PLAYER_SPEED
                self.dash_direction = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = PLAYER_SPEED
                self.dash_direction = 1
            else:
                self.vx = 0
        
        # 跳跃
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.jump_cooldown == 0:
            self._try_jump()
        
        # 冲刺
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self._try_dash()
    
    def _try_jump(self):
        """尝试跳跃"""
        if self.jump_count < self.max_jumps and self.jump_cooldown == 0:
            if self.on_wall and not self.on_ground:
                # 蹬墙跳
                self.vx, self.vy = self.physics.calculate_wall_jump_velocity(-self.wall_direction)
                self.wall_direction = 0
            else:
                # 普通跳跃或二段跳
                jump_strength = JUMP_STRENGTH if self.jump_count == 0 else DOUBLE_JUMP_STRENGTH
                self.vy = self.physics.calculate_jump_velocity(jump_strength)
            
            self.jump_count += 1
            self.jump_cooldown = self.jump_cooldown_max
            self.on_ground = False
            self.on_wall = False
    
    def _try_dash(self):
        """尝试冲刺"""
        if (self.energy >= DASH_ENERGY_COST and 
            self.dash_cooldown_timer == 0 and 
            not self.is_dashing):
            
            self.is_dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            self.energy -= DASH_ENERGY_COST
            self.invincible = True
            self.invincible_timer = DASH_DURATION
            self.vx = self.dash_direction * DASH_SPEED
            self.vy = 0
    
    def _apply_physics(self):
        """应用物理效果"""
        if self.is_dashing:
            # 冲刺状态
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vx = self.dash_direction * PLAYER_SPEED
        else:
            # 正常物理
            if self.on_wall and self.vy > 0 and not self.on_ground:
                # 滑墙状态
                self.vy = self.physics.calculate_wall_slide_velocity(self.vy)
                self.state = PlayerState.WALL_SLIDING
            else:
                # 正常重力
                self.vy = self.physics.apply_gravity(self.vy)
            
            # 应用摩擦力/空气阻力
            if self.on_ground:
                self.vx = self.physics.apply_friction(self.vx, True)
            else:
                self.vx = self.physics.apply_friction(self.vx, False)
    
    def _move_and_collide(self, obstacles: List[pygame.Rect]):
        """移动并处理碰撞"""
        # 水平移动
        self.rect.x += int(self.vx)
        collision = self.physics.check_collision(self.rect, obstacles)
        if collision:
            self.rect, on_ground, on_wall = self.physics.resolve_collision(
                self.rect, collision, self.vx, 0)
            if on_wall:
                self.on_wall = True
                self.wall_direction = 1 if self.vx > 0 else -1
                self.jump_count = 0  # 重置跳跃次数
        else:
            self.on_wall = False
        
        # 垂直移动
        self.rect.y += int(self.vy)
        collision = self.physics.check_collision(self.rect, obstacles)
        if collision:
            self.rect, on_ground, on_wall = self.physics.resolve_collision(
                self.rect, collision, 0, self.vy)
            if on_ground:
                self.on_ground = True
                self.jump_count = 0
                self.vy = 0
            else:
                self.on_ground = False
        else:
            self.on_ground = False
    
    def _update_animation(self):
        """更新动画状态"""
        self.animation_frame += 1
        
        if self.is_dashing:
            self.state = PlayerState.DASHING
        elif self.on_wall:
            self.state = PlayerState.WALL_SLIDING
        elif self.vy < 0:
            self.state = PlayerState.JUMPING
        elif self.vy > 0:
            self.state = PlayerState.FALLING
        elif abs(self.vx) > 0.5:
            self.state = PlayerState.RUNNING
        else:
            self.state = PlayerState.IDLE
        
        self.stickman.update_animation(self.state, self.animation_frame)
    
    def draw(self, surface: pygame.Surface, camera_x: int):
        """绘制玩家"""
        screen_x = self.rect.centerx - camera_x
        screen_y = self.rect.centery
        
        facing_right = self.dash_direction > 0 or self.vx >= 0
        
        # 无敌状态闪烁效果
        if self.invincible and self.animation_frame % 4 < 2:
            return
        
        self.stickman.draw(surface, screen_x, screen_y, facing_right)
    
    def add_energy(self, amount: int):
        """增加能量"""
        self.energy = min(self.energy + amount, MAX_ENERGY)
    
    def get_distance(self) -> float:
        """获取奔跑距离（米）"""
        return self.rect.x / 100.0

# ==================== 能量粒子类 ====================

class EnergyParticle:
    """能量粒子"""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.radius = 8
        self.collected = False
        self.animation_offset = 0
    
    def update(self):
        """更新动画"""
        self.animation_offset += 0.1
    
    def draw(self, surface: pygame.Surface, camera_x: int):
        """绘制粒子"""
        if self.collected:
            return
        
        screen_x = self.x - camera_x
        screen_y = self.y + int(math.sin(self.animation_offset) * 3)
        
        # 发光效果
        pygame.draw.circle(surface, YELLOW, (screen_x, screen_y), self.radius + 4)
        pygame.draw.circle(surface, ORANGE, (screen_x, screen_y), self.radius)
        pygame.draw.circle(surface, WHITE, (screen_x - 2, screen_y - 2), 3)
    
    def get_rect(self) -> pygame.Rect:
        """获取碰撞框"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius, 
                          self.radius * 2, self.radius * 2)

# ==================== 障碍物类 ====================

class Obstacle:
    """障碍物类"""
    
    def __init__(self, x: int, y: int, width: int, height: int, obs_type: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = obs_type
    
    def draw(self, surface: pygame.Surface, camera_x: int):
        """绘制障碍物"""
        screen_x = self.rect.x - camera_x
        
        if self.type == "spike":
            # 绘制尖刺
            points = [
                (screen_x, self.rect.bottom),
                (screen_x + self.rect.width // 2, self.rect.top),
                (screen_x + self.rect.width, self.rect.bottom),
            ]
            pygame.draw.polygon(surface, RED, points)
            pygame.draw.polygon(surface, DARK_GRAY, points, 2)
        elif self.type == "wall":
            # 绘制墙
            pygame.draw.rect(surface, GRAY, (screen_x, self.rect.y, self.rect.width, self.rect.height))
            pygame.draw.rect(surface, DARK_GRAY, (screen_x, self.rect.y, self.rect.width, self.rect.height), 3)
        elif self.type == "platform":
            # 绘制平台
            pygame.draw.rect(surface, GREEN, (screen_x, self.rect.y, self.rect.width, self.rect.height))
            pygame.draw.rect(surface, DARK_GRAY, (screen_x, self.rect.y, self.rect.width, self.rect.height), 2)
        else:
            # 普通地面
            pygame.draw.rect(surface, DARK_GRAY, (screen_x, self.rect.y, self.rect.width, self.rect.height))
            pygame.draw.rect(surface, BLACK, (screen_x, self.rect.y, self.rect.width, self.rect.height), 2)

# ==================== 背景类 ====================

class Background:
    """循环背景系统"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.bg1 = self._create_background()
        self.bg2 = self._create_background()
        self.x1 = 0
        self.x2 = width
    
    def _create_background(self) -> pygame.Surface:
        """创建背景 Surface"""
        bg = pygame.Surface((self.width, self.height))
        
        # 渐变天空
        for y in range(self.height):
            color_value = int(135 - y * 0.1)
            pygame.draw.line(bg, (color_value, 206, 235), (0, y), (self.width, y))
        
        # 绘制远山
        mountain_color = (100, 120, 140)
        for i in range(5):
            x_offset = i * 300
            points = [
                (x_offset, self.height),
                (x_offset + 150, self.height - 200),
                (x_offset + 300, self.height),
            ]
            pygame.draw.polygon(bg, mountain_color, points)
        
        # 绘制云朵
        cloud_color = (255, 255, 255)
        for i in range(8):
            x = i * 200 + 50
            y = 100 + (i % 3) * 50
            self._draw_cloud(bg, x, y, cloud_color)
        
        return bg
    
    def _draw_cloud(self, surface: pygame.Surface, x: int, y: int, color: Tuple[int, int, int]):
        """绘制云朵"""
        pygame.draw.circle(surface, color, (x, y), 25)
        pygame.draw.circle(surface, color, (x + 25, y - 10), 30)
        pygame.draw.circle(surface, color, (x + 50, y), 25)
        pygame.draw.circle(surface, color, (x + 25, y + 10), 20)
    
    def update(self, scroll_speed: float):
        """更新背景位置"""
        self.x1 -= scroll_speed * 0.3  # 背景移动较慢，创造视差效果
        self.x2 -= scroll_speed * 0.3
        
        # 循环重置
        if self.x1 <= -self.width:
            self.x1 = self.x2 + self.width
        if self.x2 <= -self.width:
            self.x2 = self.x1 + self.width
    
    def draw(self, surface: pygame.Surface):
        """绘制背景"""
        surface.blit(self.bg1, (int(self.x1), 0))
        surface.blit(self.bg2, (int(self.x2), 0))

# ==================== 游戏主类 ====================

class Game:
    """游戏主类"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("火柴人跑酷")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 36)
        self.font_small = pygame.font.SysFont("simhei", 24)
        
        self.physics = PhysicsEngine()
        self.background = Background(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        self.reset_game()
    
    def reset_game(self):
        """重置游戏状态"""
        self.player = Player(200, 400, self.physics)
        self.scroll_x = 0
        self.scroll_speed = INITIAL_SCROLL_SPEED
        self.distance = 0
        self.game_over = False
        self.game_over_reason = ""
        
        # 生成关卡
        self.obstacles: List[Obstacle] = []
        self.particles: List[EnergyParticle] = []
        self._generate_level()
    
    def _generate_level(self):
        """根据 LEVEL_DATA 生成关卡"""
        current_x = 0
        
        for height, length, obs_type in LEVEL_DATA:
            # 地面
            ground_y = height
            self.obstacles.append(Obstacle(current_x, ground_y, length, 
                                          SCREEN_HEIGHT - ground_y, "ground"))
            
            # 障碍物
            if obs_type == "spike":
                # 在地面放置尖刺
                for i in range(0, length, 60):
                    if i % 120 == 0:
                        spike = Obstacle(current_x + i + 20, ground_y - 30, 20, 30, "spike")
                        self.obstacles.append(spike)
            
            elif obs_type == "platform":
                # 创建平台
                for i in range(100, length, 200):
                    platform = Obstacle(current_x + i, ground_y - 100, 80, 20, "platform")
                    self.obstacles.append(platform)
                    # 在平台上放置能量粒子
                    self.particles.append(EnergyParticle(current_x + i + 40, ground_y - 140))
            
            elif obs_type == "wall":
                # 创建墙
                wall = Obstacle(current_x + length // 2, ground_y - 120, 30, 120, "wall")
                self.obstacles.append(wall)
            
            # 随机放置能量粒子
            if obs_type is None and length > 300:
                for i in range(200, length, 400):
                    self.particles.append(EnergyParticle(current_x + i, ground_y - 50))
            
            current_x += length
    
    def run(self):
        """主游戏循环"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()
            
            if not self.game_over:
                self._update()
            
            self._draw()
        
        pygame.quit()
    
    def _update(self):
        """更新游戏逻辑"""
        keys = pygame.key.get_pressed()
        
        # 动态难度 - 增加滚动速度
        self.scroll_speed = min(
            INITIAL_SCROLL_SPEED + self.distance * SCROLL_ACCELERATION,
            MAX_SCROLL_SPEED
        )
        
        # 更新摄像机
        self.scroll_x += int(self.scroll_speed)
        self.distance = self.scroll_x / 100.0
        
        # 更新背景
        self.background.update(self.scroll_speed)
        
        # 获取当前可见的障碍物
        visible_obstacles = [obs.rect for obs in self.obstacles 
                           if obs.rect.right > self.scroll_x and 
                           obs.rect.left < self.scroll_x + SCREEN_WIDTH]
        
        # 更新玩家
        self.player.update(keys, visible_obstacles)
        
        # 强制玩家向右移动（摄像机滚动）
        self.player.rect.x += int(self.scroll_speed)
        
        # 检查玩家是否掉出屏幕左侧
        if self.player.rect.right < self.scroll_x:
            self._game_over("你被甩出了屏幕！")
            return
        
        # 检查玩家是否掉出屏幕底部
        if self.player.rect.top > SCREEN_HEIGHT:
            self._game_over("你掉入了深渊！")
            return
        
        # 检查与尖刺的碰撞
        for obs in self.obstacles:
            if obs.type == "spike" and self.player.rect.colliderect(obs.rect):
                if not self.player.invincible:
                    self._game_over("你撞到了尖刺！")
                    return
        
        # 更新和收集能量粒子
        for particle in self.particles:
            particle.update()
            if not particle.collected and self.player.rect.colliderect(particle.get_rect()):
                particle.collected = True
                self.player.add_energy(ENERGY_PER_PARTICLE)
        
        # 清理已收集的粒子
        self.particles = [p for p in self.particles if not p.collected]
    
    def _game_over(self, reason: str):
        """游戏结束"""
        self.game_over = True
        self.game_over_reason = reason
    
    def _draw(self):
        """绘制画面"""
        # 绘制背景
        self.background.draw(self.screen)
        
        # 绘制障碍物
        for obs in self.obstacles:
            if obs.rect.right > self.scroll_x and obs.rect.left < self.scroll_x + SCREEN_WIDTH:
                obs.draw(self.screen, self.scroll_x)
        
        # 绘制能量粒子
        for particle in self.particles:
            if particle.x > self.scroll_x - 50 and particle.x < self.scroll_x + SCREEN_WIDTH + 50:
                particle.draw(self.screen, self.scroll_x)
        
        # 绘制玩家
        self.player.draw(self.screen, self.scroll_x)
        
        # 绘制 UI
        self._draw_ui()
        
        # 绘制游戏结束画面
        if self.game_over:
            self._draw_game_over()
        
        pygame.display.flip()
    
    def _draw_ui(self):
        """绘制用户界面"""
        # 距离显示
        distance_text = self.font.render(f"距离: {self.distance:.1f} 米", True, WHITE)
        self.screen.blit(distance_text, (20, 20))
        
        # 速度显示
        speed_text = self.font_small.render(f"速度: {self.scroll_speed:.1f}", True, WHITE)
        self.screen.blit(speed_text, (20, 60))
        
        # 能量槽背景
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 60
        bar_width = 200
        bar_height = 30
        
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # 能量填充
        energy_width = int((self.player.energy / MAX_ENERGY) * (bar_width - 4))
        energy_color = YELLOW if self.player.energy >= DASH_ENERGY_COST else GRAY
        pygame.draw.rect(self.screen, energy_color, (bar_x + 2, bar_y + 2, energy_width, bar_height - 4))
        
        # 能量文字
        energy_text = self.font_small.render(f"能量: {self.player.energy}/{MAX_ENERGY}", True, WHITE)
        self.screen.blit(energy_text, (bar_x, bar_y - 25))
        
        # 冲刺提示
        if self.player.energy >= DASH_ENERGY_COST:
            dash_text = self.font_small.render("按 Shift 冲刺！", True, CYAN)
            self.screen.blit(dash_text, (bar_x + 220, bar_y + 2))
        
        # 跳跃提示
        jump_text = self.font_small.render("空格/↑ 跳跃 (可二段跳)", True, WHITE)
        self.screen.blit(jump_text, (SCREEN_WIDTH - 280, 20))
        
        # 滑墙提示
        wall_text = self.font_small.render("贴墙下滑可蹬墙跳", True, WHITE)
        self.screen.blit(wall_text, (SCREEN_WIDTH - 280, 50))
    
    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束文字
        game_over_text = self.font.render("游戏结束", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(game_over_text, text_rect)
        
        # 原因
        reason_text = self.font_small.render(self.game_over_reason, True, WHITE)
        reason_rect = reason_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(reason_text, reason_rect)
        
        # 距离
        distance_text = self.font.render(f"奔跑距离: {self.distance:.1f} 米", True, YELLOW)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(distance_text, distance_rect)
        
        # 重启提示
        restart_text = self.font_small.render("按 R 键重新开始", True, GREEN)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(restart_text, restart_rect)

# ==================== 主入口 ====================

def main():
    """主函数"""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
