# -*- coding: utf-8 -*-
"""
火柴人画线游戏
使用 Python 3.9 和 Pygame 2.5.2 开发
"""

import pygame
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ==================== 游戏常量 ====================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 颜色定义
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_ORANGE = (255, 165, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_LIGHT_GRAY = (200, 200, 200)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_SKIN = (255, 220, 177)

# 墨水设置
MAX_INK = 1000  # 最大墨水量
INK_PER_PIXEL = 1  # 每像素消耗的墨水

# 火柴人设置
STICKMAN_SIZE = 20
STICKMAN_SPEED = 3
STICKMAN_ATTACH_DISTANCE = 15  # 附着距离阈值

# 游戏状态
class GameState(Enum):
    DRAWING = 1      # 画线阶段
    RUNNING = 2      # 火柴人移动阶段
    LEVEL_COMPLETE = 3  # 关卡完成
    GAME_OVER = 4    # 游戏结束

# 火柴人状态
class StickmanState(Enum):
    STOPPING = 1     # 静止状态
    RUNNING = 2      # 移动状态

# ==================== 关卡数据（硬编码） ====================
# 每个关卡包含：起点、终点、障碍物列表、时间限制
# 障碍物格式: (x, y, width, height, type)  type: 'wall' 或 'platform'

LEVELS = [
    # 关卡 1 - 简单
    {
        'name': '关卡 1',
        'start': (100, 400),
        'end': (1000, 400),
        'end_radius': 30,
        'time_limit': 30,
        'obstacles': [
            # 中间一个矮墙
            (500, 350, 50, 100, 'wall'),
        ],
        'platforms': [
            # 起点平台
            (50, 420, 100, 20, 'platform'),
            # 终点平台
            (950, 420, 100, 20, 'platform'),
        ]
    },
    # 关卡 2 - 中等
    {
        'name': '关卡 2',
        'start': (100, 600),
        'end': (1000, 200),
        'end_radius': 30,
        'time_limit': 45,
        'obstacles': [
            # 左侧高墙
            (300, 400, 50, 200, 'wall'),
            # 右侧高墙
            (700, 200, 50, 200, 'wall'),
            # 中间障碍
            (500, 450, 100, 50, 'wall'),
        ],
        'platforms': [
            # 起点平台
            (50, 620, 100, 20, 'platform'),
            # 中间平台1
            (350, 350, 100, 20, 'platform'),
            # 中间平台2
            (600, 400, 100, 20, 'platform'),
            # 终点平台
            (950, 220, 100, 20, 'platform'),
        ]
    },
    # 关卡 3 - 困难
    {
        'name': '关卡 3',
        'start': (100, 700),
        'end': (1000, 100),
        'end_radius': 25,
        'time_limit': 60,
        'obstacles': [
            # 复杂迷宫式障碍
            (200, 500, 80, 200, 'wall'),
            (400, 300, 80, 300, 'wall'),
            (600, 400, 80, 200, 'wall'),
            (800, 200, 80, 300, 'wall'),
            # 顶部障碍
            (300, 150, 400, 50, 'wall'),
            # 尖刺状障碍
            (500, 600, 100, 30, 'wall'),
            (350, 250, 80, 30, 'wall'),
            (750, 350, 80, 30, 'wall'),
        ],
        'platforms': [
            # 起点平台
            (50, 720, 80, 20, 'platform'),
            # 小平台序列
            (150, 550, 60, 15, 'platform'),
            (320, 450, 60, 15, 'platform'),
            (500, 350, 60, 15, 'platform'),
            (700, 300, 60, 15, 'platform'),
            (900, 200, 60, 15, 'platform'),
            # 终点平台
            (970, 120, 80, 20, 'platform'),
        ]
    }
]

# ==================== 线条类 ====================
@dataclass
class LineSegment:
    """线段类"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    
    def length(self) -> float:
        """计算线段长度"""
        return math.sqrt((self.end[0] - self.start[0])**2 + 
                        (self.end[1] - self.start[1])**2)
    
    def get_slope(self) -> float:
        """获取线段斜率"""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        if dx == 0:
            return float('inf')
        return dy / dx
    
    def get_angle(self) -> float:
        """获取线段角度（弧度）"""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.atan2(dy, dx)
    
    def distance_to_point(self, point: Tuple[float, float]) -> float:
        """计算点到线段的距离"""
        x, y = point
        x1, y1 = self.start
        x2, y2 = self.end
        
        # 线段长度的平方
        line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        
        if line_len_sq == 0:
            return math.sqrt((x - x1)**2 + (y - y1)**2)
        
        # 计算投影参数 t
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_len_sq))
        
        # 投影点坐标
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return math.sqrt((x - proj_x)**2 + (y - proj_y)**2)
    
    def get_closest_point(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """获取线段上距离点最近的点"""
        x, y = point
        x1, y1 = self.start
        x2, y2 = self.end
        
        line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        
        if line_len_sq == 0:
            return self.start
        
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_len_sq))
        
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return (proj_x, proj_y)


class DrawnLine:
    """玩家画出的线"""
    def __init__(self):
        self.segments: List[LineSegment] = []
        self.current_points: List[Tuple[float, float]] = []
        self.total_ink_used = 0
    
    def add_point(self, point: Tuple[float, float]):
        """添加点"""
        self.current_points.append(point)
        
        # 如果至少有两个点，创建线段
        if len(self.current_points) >= 2:
            start = self.current_points[-2]
            end = self.current_points[-1]
            segment = LineSegment(start, end)
            self.segments.append(segment)
            self.total_ink_used += segment.length() * INK_PER_PIXEL
    
    def finish_drawing(self):
        """完成当前绘制"""
        self.current_points = []
    
    def get_all_segments(self) -> List[LineSegment]:
        """获取所有线段"""
        return self.segments
    
    def clear(self):
        """清除所有线条"""
        self.segments = []
        self.current_points = []
        self.total_ink_used = 0
    
    def draw(self, screen: pygame.Surface, color: Tuple[int, int, int] = COLOR_BLACK):
        """绘制线条"""
        # 绘制已完成的线段
        for segment in self.segments:
            pygame.draw.line(screen, color, 
                           (int(segment.start[0]), int(segment.start[1])),
                           (int(segment.end[0]), int(segment.end[1])), 3)
        
        # 绘制当前正在画的线
        if len(self.current_points) >= 2:
            pygame.draw.lines(screen, color, False, 
                            [(int(p[0]), int(p[1])) for p in self.current_points], 3)


# ==================== 火柴人类 ====================
class Stickman:
    """火柴人类"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.start_pos = (x, y)
        self.state = StickmanState.STOPPING
        self.velocity = [0.0, 0.0]
        self.size = STICKMAN_SIZE
        self.on_line = False
        self.current_line_segment: Optional[LineSegment] = None
        self.segment_progress = 0.0  # 在当前线段上的进度
        self.facing_right = True
        self.animation_frame = 0
        
        # 身体各部分相对位置
        self.head_radius = 6
        self.body_length = 12
        self.leg_length = 8
        self.arm_length = 8
    
    def get_foot_position(self) -> Tuple[float, float]:
        """获取脚底坐标"""
        # 火柴人y坐标是底部（脚的位置）
        return (self.x, self.y)
    
    def reset(self):
        """重置位置"""
        self.x, self.y = self.start_pos
        self.state = StickmanState.STOPPING
        self.velocity = [0.0, 0.0]
        self.on_line = False
        self.current_line_segment = None
        self.segment_progress = 0.0
        self.facing_right = True
        self.animation_frame = 0
    
    def find_nearest_line_segment(self, lines: DrawnLine) -> Optional[Tuple[LineSegment, float]]:
        """找到距离脚底最近的线段及其距离"""
        foot_pos = self.get_foot_position()
        segments = lines.get_all_segments()
        
        if not segments:
            return None
        
        nearest_segment = None
        min_distance = float('inf')
        
        for segment in segments:
            distance = segment.distance_to_point(foot_pos)
            if distance < min_distance:
                min_distance = distance
                nearest_segment = segment
        
        if nearest_segment and min_distance <= STICKMAN_ATTACH_DISTANCE:
            return (nearest_segment, min_distance)
        
        return None
    
    def update(self, lines: DrawnLine, obstacles: List, platforms: List):
        """更新火柴人状态"""
        if self.state == StickmanState.STOPPING:
            return
        
        self.animation_frame += 1
        
        # 查找最近的线条
        nearest = self.find_nearest_line_segment(lines)
        
        if nearest:
            segment, distance = nearest
            self.on_line = True
            self.current_line_segment = segment
            
            # 计算线条角度和方向
            angle = segment.get_angle()
            
            # 确定移动方向：根据当前位置在线条上的投影决定向哪个端点移动
            # 计算到线段两个端点的距离
            dist_to_start = math.sqrt((self.x - segment.start[0])**2 + (self.y - segment.start[1])**2)
            dist_to_end = math.sqrt((self.x - segment.end[0])**2 + (self.y - segment.end[1])**2)
            
            # 向较远的端点移动（这样火柴人会沿着线条向前移动）
            if dist_to_end > dist_to_start:
                # 向 end 点移动
                self.velocity[0] = STICKMAN_SPEED * math.cos(angle)
                self.velocity[1] = STICKMAN_SPEED * math.sin(angle)
                self.facing_right = self.velocity[0] >= 0
            else:
                # 向 start 点移动（反向）
                self.velocity[0] = -STICKMAN_SPEED * math.cos(angle)
                self.velocity[1] = -STICKMAN_SPEED * math.sin(angle)
                self.facing_right = self.velocity[0] >= 0
            
            # 更新位置
            self.x += self.velocity[0]
            self.y += self.velocity[1]
            
            # 将脚底对齐到线条（保持在线条上）
            closest_point = segment.get_closest_point((self.x, self.y))
            self.x = closest_point[0]
            self.y = closest_point[1]
            
        else:
            # 不在线上，停止移动
            self.on_line = False
            self.current_line_segment = None
            self.state = StickmanState.STOPPING
            self.velocity = [0.0, 0.0]
        
        # 检查障碍物碰撞
        self.check_obstacle_collision(obstacles)
    
    def check_obstacle_collision(self, obstacles: List):
        """检查与障碍物的碰撞"""
        # 简化的碰撞检测 - 检查火柴人身体中心点
        # self.y 是脚底位置，身体中心在上方
        body_center_y = self.y - self.leg_length - self.body_length / 2
        for obs in obstacles:
            x, y, w, h, _ = obs
            if (x <= self.x <= x + w and 
                y <= body_center_y <= y + h):
                # 碰到障碍物，停止
                self.state = StickmanState.STOPPING
                self.velocity = [0.0, 0.0]
                break
    
    def start_running(self):
        """开始移动"""
        if self.state == StickmanState.STOPPING:
            self.state = StickmanState.RUNNING
            self.velocity = [STICKMAN_SPEED, 0]
    
    def draw(self, screen: pygame.Surface):
        """绘制火柴人"""
        # 计算动画偏移
        leg_offset = 0
        arm_offset = 0
        if self.state == StickmanState.RUNNING:
            leg_offset = math.sin(self.animation_frame * 0.3) * 4
            arm_offset = math.sin(self.animation_frame * 0.3 + math.pi) * 3
        
        # self.y 是脚底位置，向上绘制
        # 腿部终点（臀部）
        hip_y = self.y - self.leg_length
        
        # 身体顶部（肩部）
        shoulder_y = hip_y - self.body_length
        
        # 头部中心
        head_center_y = shoulder_y - self.head_radius
        
        # 绘制头部
        pygame.draw.circle(screen, COLOR_BLACK, 
                          (int(self.x), int(head_center_y)), 
                          self.head_radius, 2)
        
        # 绘制身体
        pygame.draw.line(screen, COLOR_BLACK,
                        (int(self.x), int(shoulder_y)),
                        (int(self.x), int(hip_y)), 2)
        
        # 绘制手臂
        arm_y = shoulder_y + 4
        if self.facing_right:
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(arm_y)),
                            (int(self.x) + self.arm_length - arm_offset, int(arm_y) + 4), 2)
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(arm_y)),
                            (int(self.x) - self.arm_length//2, int(arm_y) + 2), 2)
        else:
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(arm_y)),
                            (int(self.x) - self.arm_length + arm_offset, int(arm_y) + 4), 2)
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(arm_y)),
                            (int(self.x) + self.arm_length//2, int(arm_y) + 2), 2)
        
        # 绘制腿
        if self.state == StickmanState.RUNNING:
            # 左腿
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(hip_y)),
                            (int(self.x) - 3 + leg_offset, int(self.y)), 2)
            # 右腿
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(hip_y)),
                            (int(self.x) + 3 - leg_offset, int(self.y)), 2)
        else:
            # 静止状态
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(hip_y)),
                            (int(self.x) - 4, int(self.y)), 2)
            pygame.draw.line(screen, COLOR_BLACK,
                            (int(self.x), int(hip_y)),
                            (int(self.x) + 4, int(self.y)), 2)


# ==================== 按钮类 ====================
class Button:
    """按钮类"""
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, color: Tuple[int, int, int], 
                 hover_color: Tuple[int, int, int], text_color: Tuple[int, int, int] = COLOR_WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.SysFont("simhei", 24)
    
    def draw(self, screen: pygame.Surface):
        """绘制按钮"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BLACK, self.rect, 2, border_radius=8)
        
        # 绘制文字
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def update(self, mouse_pos: Tuple[int, int]):
        """更新按钮状态"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """检查是否被点击"""
        return self.rect.collidepoint(mouse_pos)


# ==================== HUD类 ====================
class HUD:
    """抬头显示器"""
    def __init__(self):
        self.font_large = pygame.font.SysFont("simhei", 32)
        self.font_medium = pygame.font.SysFont("simhei", 24)
        self.font_small = pygame.font.SysFont("simhei", 18)
    
    def draw(self, screen: pygame.Surface, ink_remaining: float, time_remaining: float, 
             level_name: str, game_state: GameState):
        """绘制HUD"""
        # 背景条
        pygame.draw.rect(screen, COLOR_DARK_GRAY, (0, 0, SCREEN_WIDTH, 80))
        
        # 关卡名称
        level_text = self.font_large.render(level_name, True, COLOR_WHITE)
        screen.blit(level_text, (20, 10))
        
        # 墨水进度条
        ink_bar_x = 300
        ink_bar_y = 20
        ink_bar_width = 300
        ink_bar_height = 20
        
        ink_text = self.font_medium.render("墨水剩余:", True, COLOR_WHITE)
        screen.blit(ink_text, (ink_bar_x - 100, ink_bar_y))
        
        # 进度条背景
        pygame.draw.rect(screen, COLOR_GRAY, (ink_bar_x, ink_bar_y, ink_bar_width, ink_bar_height))
        # 进度条填充
        ink_percentage = max(0, ink_remaining / MAX_INK)
        ink_color = COLOR_GREEN if ink_percentage > 0.5 else (COLOR_YELLOW if ink_percentage > 0.2 else COLOR_RED)
        pygame.draw.rect(screen, ink_color, 
                        (ink_bar_x, ink_bar_y, int(ink_bar_width * ink_percentage), ink_bar_height))
        # 进度条边框
        pygame.draw.rect(screen, COLOR_WHITE, (ink_bar_x, ink_bar_y, ink_bar_width, ink_bar_height), 2)
        
        # 百分比文字
        percentage_text = self.font_small.render(f"{int(ink_percentage * 100)}%", True, COLOR_WHITE)
        screen.blit(percentage_text, (ink_bar_x + ink_bar_width // 2 - 15, ink_bar_y + 25))
        
        # 倒计时
        time_bar_x = 700
        time_bar_y = 20
        time_bar_width = 200
        time_bar_height = 20
        
        time_text = self.font_medium.render("剩余时间:", True, COLOR_WHITE)
        screen.blit(time_text, (time_bar_x - 100, time_bar_y))
        
        # 时间显示
        time_color = COLOR_GREEN if time_remaining > 10 else COLOR_RED
        time_value_text = self.font_large.render(f"{int(time_remaining)}s", True, time_color)
        screen.blit(time_value_text, (time_bar_x + time_bar_width // 2 - 30, time_bar_y - 5))
        
        # 游戏状态提示
        if game_state == GameState.DRAWING:
            hint_text = self.font_medium.render("画线模式 - 点击并拖动鼠标画线", True, COLOR_YELLOW)
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - 150, 50))
        elif game_state == GameState.RUNNING:
            hint_text = self.font_medium.render("移动模式 - 火柴人正在移动", True, COLOR_GREEN)
            screen.blit(hint_text, (SCREEN_WIDTH // 2 - 120, 50))


# ==================== 游戏主类 ====================
class Game:
    """游戏主类"""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("火柴人画线游戏")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 游戏状态
        self.game_state = GameState.DRAWING
        self.current_level_idx = 0
        self.current_level = LEVELS[0]
        
        # 游戏对象
        self.stickman = Stickman(*self.current_level['start'])
        self.drawn_line = DrawnLine()
        self.hud = HUD()
        
        # 墨水系统
        self.ink_remaining = MAX_INK
        
        # 时间系统
        self.time_remaining = self.current_level['time_limit']
        self.start_time = None
        
        # 按钮
        self.start_button = Button(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 80, 
                                   120, 50, "开始", COLOR_GREEN, (0, 200, 0))
        self.reset_button = Button(SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT - 80, 
                                   120, 50, "重置", COLOR_ORANGE, (200, 150, 0))
        self.clear_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 80, 
                                   120, 50, "清除线条", COLOR_RED, (200, 0, 0))
        
        # 鼠标状态
        self.is_drawing = False
        self.last_mouse_pos = None
        
        # 关卡完成信息
        self.level_complete_data = None
        
        # 字体
        self.font_large = pygame.font.SysFont("simhei", 48)
        self.font_medium = pygame.font.SysFont("simhei", 32)
        self.font_small = pygame.font.SysFont("simhei", 24)
    
    def reset_level(self):
        """重置当前关卡"""
        self.game_state = GameState.DRAWING
        self.stickman.reset()
        self.drawn_line.clear()
        self.ink_remaining = MAX_INK
        self.time_remaining = self.current_level['time_limit']
        self.start_time = None
        self.is_drawing = False
        self.level_complete_data = None
    
    def next_level(self):
        """进入下一关"""
        self.current_level_idx += 1
        if self.current_level_idx >= len(LEVELS):
            # 所有关卡完成，回到第一关
            self.current_level_idx = 0
        
        self.current_level = LEVELS[self.current_level_idx]
        self.stickman = Stickman(*self.current_level['start'])
        self.reset_level()
    
    def check_level_complete(self) -> bool:
        """检查是否完成关卡"""
        end_x, end_y = self.current_level['end']
        end_radius = self.current_level['end_radius']
        
        distance = math.sqrt((self.stickman.x - end_x)**2 + 
                           (self.stickman.y - end_y)**2)
        
        return distance <= end_radius
    
    def calculate_ink_efficiency(self) -> float:
        """计算墨水利用率评分"""
        ink_used = self.drawn_line.total_ink_used
        if ink_used == 0:
            return 0.0
        
        # 计算起点到终点的直线距离
        start = self.current_level['start']
        end = self.current_level['end']
        optimal_distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        # 效率 = 最优距离 / 实际墨水使用量 * 100
        efficiency = (optimal_distance / ink_used) * 100
        return min(100.0, efficiency)
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 检查按钮点击
                    if self.game_state != GameState.LEVEL_COMPLETE:
                        if self.start_button.is_clicked(mouse_pos):
                            if self.game_state == GameState.DRAWING:
                                self.game_state = GameState.RUNNING
                                self.stickman.start_running()
                                self.start_time = pygame.time.get_ticks()
                            return
                        
                        if self.reset_button.is_clicked(mouse_pos):
                            self.reset_level()
                            return
                        
                        if self.clear_button.is_clicked(mouse_pos):
                            self.drawn_line.clear()
                            self.ink_remaining = MAX_INK
                            self.stickman.reset()
                            self.game_state = GameState.DRAWING
                            return
                    
                    # 画线模式
                    if self.game_state == GameState.DRAWING:
                        # 检查是否在按钮区域外
                        if mouse_pos[1] < SCREEN_HEIGHT - 100:
                            self.is_drawing = True
                            self.last_mouse_pos = mouse_pos
                            self.drawn_line.current_points = [mouse_pos]
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.is_drawing:
                        self.is_drawing = False
                        self.drawn_line.finish_drawing()
                        self.last_mouse_pos = None
            
            elif event.type == pygame.MOUSEMOTION:
                if self.is_drawing and self.game_state == GameState.DRAWING:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 检查墨水是否足够
                    if self.last_mouse_pos:
                        distance = math.sqrt((mouse_pos[0] - self.last_mouse_pos[0])**2 + 
                                           (mouse_pos[1] - self.last_mouse_pos[1])**2)
                        ink_needed = distance * INK_PER_PIXEL
                        
                        if self.ink_remaining >= ink_needed and mouse_pos[1] < SCREEN_HEIGHT - 100:
                            self.drawn_line.add_point(mouse_pos)
                            self.ink_remaining -= ink_needed
                            self.last_mouse_pos = mouse_pos
                        else:
                            self.is_drawing = False
                            self.drawn_line.finish_drawing()
    
    def update(self):
        """更新游戏状态"""
        if self.game_state == GameState.LEVEL_COMPLETE:
            return
        
        # 更新按钮悬停状态
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        self.reset_button.update(mouse_pos)
        self.clear_button.update(mouse_pos)
        
        if self.game_state == GameState.RUNNING:
            # 更新火柴人
            self.stickman.update(self.drawn_line, 
                               self.current_level['obstacles'],
                               self.current_level['platforms'])
            
            # 更新倒计时
            if self.start_time:
                elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
                self.time_remaining = max(0, self.current_level['time_limit'] - elapsed)
            
            # 检查关卡完成
            if self.check_level_complete():
                self.game_state = GameState.LEVEL_COMPLETE
                efficiency = self.calculate_ink_efficiency()
                self.level_complete_data = {
                    'efficiency': efficiency,
                    'ink_used': self.drawn_line.total_ink_used,
                    'time_used': self.current_level['time_limit'] - self.time_remaining
                }
            
            # 检查时间耗尽
            elif self.time_remaining <= 0:
                self.game_state = GameState.GAME_OVER
                self.stickman.state = StickmanState.STOPPING
    
    def draw(self):
        """绘制游戏画面"""
        # 清空屏幕
        self.screen.fill(COLOR_WHITE)
        
        # 绘制游戏区域背景
        pygame.draw.rect(self.screen, (240, 240, 255), (0, 80, SCREEN_WIDTH, SCREEN_HEIGHT - 160))
        
        # 绘制起点
        start_x, start_y = self.current_level['start']
        pygame.draw.circle(self.screen, COLOR_GREEN, (int(start_x), int(start_y)), 15)
        pygame.draw.circle(self.screen, COLOR_BLACK, (int(start_x), int(start_y)), 15, 2)
        start_text = self.font_small.render("起点", True, COLOR_BLACK)
        self.screen.blit(start_text, (int(start_x) - 15, int(start_y) - 35))
        
        # 绘制终点
        end_x, end_y = self.current_level['end']
        end_radius = self.current_level['end_radius']
        pygame.draw.circle(self.screen, COLOR_RED, (int(end_x), int(end_y)), end_radius)
        pygame.draw.circle(self.screen, COLOR_BLACK, (int(end_x), int(end_y)), end_radius, 2)
        end_text = self.font_small.render("终点", True, COLOR_BLACK)
        self.screen.blit(end_text, (int(end_x) - 15, int(end_y) - end_radius - 20))
        
        # 绘制障碍物
        for obs in self.current_level['obstacles']:
            x, y, w, h, obs_type = obs
            pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (x, y, w, h))
            pygame.draw.rect(self.screen, COLOR_BLACK, (x, y, w, h), 2)
        
        # 绘制平台
        for plat in self.current_level['platforms']:
            x, y, w, h, _ = plat
            pygame.draw.rect(self.screen, COLOR_BROWN if 'COLOR_BROWN' in dir() else (139, 69, 19), (x, y, w, h))
            pygame.draw.rect(self.screen, COLOR_BLACK, (x, y, w, h), 2)
        
        # 绘制画出的线
        self.drawn_line.draw(self.screen)
        
        # 绘制火柴人
        self.stickman.draw(self.screen)
        
        # 绘制HUD
        self.hud.draw(self.screen, self.ink_remaining, self.time_remaining,
                     self.current_level['name'], self.game_state)
        
        # 绘制按钮
        if self.game_state != GameState.LEVEL_COMPLETE:
            self.start_button.draw(self.screen)
            self.reset_button.draw(self.screen)
            self.clear_button.draw(self.screen)
        
        # 绘制关卡完成界面
        if self.game_state == GameState.LEVEL_COMPLETE and self.level_complete_data:
            self.draw_level_complete()
        
        # 绘制游戏结束界面
        if self.game_state == GameState.GAME_OVER:
            self.draw_game_over()
        
        # 更新显示
        pygame.display.flip()
    
    def draw_level_complete(self):
        """绘制关卡完成界面"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLOR_BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 完成标题
        complete_text = self.font_large.render("关卡完成!", True, COLOR_GREEN)
        text_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(complete_text, text_rect)
        
        # 墨水利用率
        efficiency = self.level_complete_data['efficiency']
        efficiency_color = COLOR_GREEN if efficiency >= 80 else (COLOR_YELLOW if efficiency >= 50 else COLOR_RED)
        efficiency_text = self.font_medium.render(f"墨水利用率评分: {efficiency:.1f}%", True, efficiency_color)
        text_rect = efficiency_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(efficiency_text, text_rect)
        
        # 使用墨水
        ink_text = self.font_medium.render(f"使用墨水: {self.level_complete_data['ink_used']:.0f}/{MAX_INK}", 
                                          True, COLOR_WHITE)
        text_rect = ink_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(ink_text, text_rect)
        
        # 使用时间
        time_text = self.font_medium.render(f"使用时间: {self.level_complete_data['time_used']:.1f}秒", 
                                           True, COLOR_WHITE)
        text_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(time_text, text_rect)
        
        # 提示下一关
        if self.current_level_idx < len(LEVELS) - 1:
            next_text = self.font_small.render("点击任意处进入下一关", True, COLOR_YELLOW)
        else:
            next_text = self.font_small.render("恭喜通关所有关卡! 点击任意处重新开始", True, COLOR_YELLOW)
        text_rect = next_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        self.screen.blit(next_text, text_rect)
        
        # 检查点击
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            self.next_level()
    
    def draw_game_over(self):
        """绘制游戏结束界面"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLOR_BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束标题
        over_text = self.font_large.render("时间到!", True, COLOR_RED)
        text_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(over_text, text_rect)
        
        # 提示重试
        retry_text = self.font_medium.render("点击任意处重试", True, COLOR_WHITE)
        text_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(retry_text, text_rect)
        
        # 检查点击
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            self.reset_level()
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


# ==================== 主程序入口 ====================
if __name__ == "__main__":
    # 定义棕色（用于平台）
    COLOR_BROWN = (139, 69, 19)
    
    game = Game()
    game.run()
