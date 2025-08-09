#!/usr/bin/env python3
import curses
import random
import time
import os

global GAME_TITLE, INITIAL_LENGTH, SPEED, FOOD_SYMBOL, SNAKE_HEAD, SNAKE_BODY, BORDER, SPACE, SCORE_FILE, OBSTACLE_SYMBOL

# 游戏配置
GAME_TITLE = "Ubuntu 24.04 WSL 贪吃蛇"
INITIAL_LENGTH = 2
SPEED = 0.10  # 游戏速度，单位为秒
FOOD_SYMBOL = "🍎"
SNAKE_HEAD = "🐍"
SNAKE_BODY = "🟢"
BORDER = "+++"
SPACE = " "
SCORE_FILE = "snake_highscore.txt"
OBSTACLE_SYMBOL = "🟫"
DOUBLE_SCORE_SYMBOL = "🌟"  # 得分倍增球
INVINCIBLE_SYMBOL = "💊"   # 无敌球

class SnakeGame:
    def __init__(self, stdscr, difficulty=0):
        self.stdscr = stdscr
        self.high_score = self.load_high_score()
        self.difficulty = difficulty  # 存储难度级别
        self.initialize_game()
        
    def load_high_score(self):
        try:
            if os.path.exists(SCORE_FILE):
                with open(SCORE_FILE, 'r') as f:
                    return int(f.read().strip())
        except:
            pass
        return 0
        
    def save_high_score(self):
        try:
            with open(SCORE_FILE, 'w') as f:
                f.write(str(self.high_score))
        except:
            pass
        
    def initialize_game(self):
        # 获取窗口尺寸
        self.height, self.width = self.stdscr.getmaxyx()
        self.game_height = self.height - 3
        self.game_width = self.width - 2
        
        # 随机生成蛇的初始位置和初始方向
        self.snake = []
        start_y = random.randint(2, self.game_height - 2)
        start_x = random.randint(2, self.game_width - 2)
        for i in range(INITIAL_LENGTH):
            self.snake.append([start_y, start_x - i])
        
        self.direction = random.choice([
            curses.KEY_LEFT,
            curses.KEY_RIGHT,
        ])
        
        # 初始化障碍物 - 先创建空列表
        self.obstacles = []
        if self.difficulty > 0:  # 中等或困难难度
            self.generate_obstacles()
        
        # 初始化道具
        self.double_score_item = None  # 得分倍增球
        self.invincible_item = None    # 无敌球
        self.double_score_active = False  # 是否激活得分倍增
        self.double_score_counter = 0    # 得分倍增计数器
        self.invincible_active = False   # 是否激活无敌状态
        self.invincible_counter = 0      # 无敌状态计数器
        
        # 食物位置 - 现在障碍物已经初始化
        self.food = self.generate_food()
        
        # 游戏状态
        self.score = 0
        self.game_over = False
        self.paused = False
        self.last_score_for_double = 0  # 上次生成得分倍增球的分数
        self.last_score_for_invincible = 0  # 上次生成无敌球的分数
        
    def generate_food(self):
        while True:
            food = [
                random.randint(3, self.game_height - 3),
                random.randint(3, self.game_width - 3)
            ]
            # 确保食物不在蛇身上或障碍物上
            if (food not in self.snake and 
                food not in self.obstacles and
                food != self.double_score_item and
                food != self.invincible_item):
                return food
    
    def generate_obstacles(self):
        """根据难度生成障碍物"""
        # 定义五个区域的中心点
        regions = [
            # 左上
            (self.game_height // 4, self.game_width // 4),
            # 右上
            (self.game_height // 4, 3 * self.game_width // 4),
            # 左下
            (3 * self.game_height // 4, self.game_width // 4),
            # 右下
            (3 * self.game_height // 4, 3 * self.game_width // 4),
            # 中心
            (self.game_height // 2, self.game_width // 2)
        ]
        
        for center_y, center_x in regions:
            if self.difficulty == 1:  # 中等难度 - 正方形
                for y_offset in [-1, 0, 1]:
                    for x_offset in [-1, 0, 1]:
                        obstacle_y = center_y + y_offset
                        obstacle_x = center_x + x_offset
                        # 确保障碍物在游戏区域内且不在边界上
                        if (1 < obstacle_y < self.game_height - 1 and 
                            0 < obstacle_x < self.game_width - 1):
                            self.obstacles.append([obstacle_y, obstacle_x])
            elif self.difficulty == 2:  # 困难难度 - 菱形
                offsets = [
                    (0, 0),    # 中心
                    (-1, 0),   # 上
                    (1, 0),    # 下
                    (0, -1),   # 左
                    (0, 1)     # 右
                ]
                for y_offset, x_offset in offsets:
                    obstacle_y = center_y + y_offset
                    obstacle_x = center_x + x_offset
                    # 确保障碍物在游戏区域内且不在边界上
                    if (1 < obstacle_y < self.game_height - 1 and 
                        0 < obstacle_x < self.game_width - 1):
                        self.obstacles.append([obstacle_y, obstacle_x])
    
    def generate_double_score_item(self):
        """生成得分倍增球"""
        while True:
            item = [
                random.randint(3, self.game_height - 3),
                random.randint(3, self.game_width - 3)
            ]
            # 确保位置不冲突
            if (item not in self.snake and 
                item not in self.obstacles and
                item != self.food and
                item != self.invincible_item):
                return item
    
    def generate_invincible_item(self):
        """生成无敌球"""
        while True:
            item = [
                random.randint(3, self.game_height - 3),
                random.randint(3, self.game_width - 3)
            ]
            # 确保位置不冲突
            if (item not in self.snake and 
                item not in self.obstacles and
                item != self.food and
                item != self.double_score_item):
                return item
    
    # 边界绘制函数
    def draw_border(self):
        # 绘制顶部和底部边框,其中第0行用于绘制标题，此处空出第一行
        for x in range(1, self.game_width - 1):
            if x < self.width:
                self.stdscr.addstr(1, x, BORDER)
                self.stdscr.addstr(self.game_height - 1, x, BORDER)

        # 绘制左右边框（从第2行到倒数第二行）
        for y in range(2, self.game_height - 1):
            self.stdscr.addstr(y, 0, BORDER)
            if self.game_width - 1 < self.width:  # 防止越界
                self.stdscr.addstr(y, self.game_width - 1, BORDER)
    
    def draw_game(self):
        # 清屏
        self.stdscr.clear()
        
        # 绘制标题
        difficulty_names = ["简单", "中等", "困难"]
        title = f"{GAME_TITLE} | 难度: {difficulty_names[self.difficulty]} | 得分: {self.score} | 最高分: {self.high_score}"
        
        # 添加道具状态信息
        if self.double_score_active:
            title += f" | 得分倍增: {self.double_score_counter}"
        if self.invincible_active:
            title += f" | 无敌状态: {self.invincible_counter}"
            
        self.stdscr.addstr(0, (self.width - len(title)) // 2, title)
        
        # 绘制游戏区域
        self.draw_border()
        
        # 绘制食物
        if self.food:
            self.stdscr.addstr(self.food[0], self.food[1], FOOD_SYMBOL)
        
        # 绘制蛇
        snake_color = curses.A_BOLD | curses.color_pair(2) if self.invincible_active else curses.A_NORMAL
        for i, segment in enumerate(self.snake):
            if i == 0:
                self.stdscr.addstr(segment[0], segment[1], SNAKE_HEAD, snake_color)
            else:
                self.stdscr.addstr(segment[0], segment[1], SNAKE_BODY, snake_color)
        
        # 绘制障碍物
        for obstacle in self.obstacles:
            self.stdscr.addstr(obstacle[0], obstacle[1], OBSTACLE_SYMBOL)
        
        # 绘制得分倍增球
        if self.double_score_item:
            self.stdscr.addstr(self.double_score_item[0], self.double_score_item[1], DOUBLE_SCORE_SYMBOL, curses.color_pair(3))
        
        # 绘制无敌球
        if self.invincible_item:
            self.stdscr.addstr(self.invincible_item[0], self.invincible_item[1], INVINCIBLE_SYMBOL, curses.color_pair(1))
        
        # 绘制控制说明
        controls = "方向键: 移动 | P: 暂停 | R: 重新开始 | Q: 退出"
        self.stdscr.addstr(self.height - 2, (self.width - len(controls)) // 2, controls)
        
        # 如果游戏结束，显示游戏结束信息
        if self.game_over:
            game_over_msg = "游戏结束! 按R重新开始或按Q退出"
            self.stdscr.addstr(self.game_height // 2, (self.width - len(game_over_msg)) // 2, game_over_msg)
        
        # 如果游戏暂停，显示暂停信息
        if self.paused:
            pause_msg = "游戏暂停 - 按P继续"
            self.stdscr.addstr(self.game_height // 2 - 1, (self.width - len(pause_msg)) // 2, pause_msg)
        
        # 刷新屏幕
        self.stdscr.refresh()
    
    def update_game(self):
        # 获取蛇头
        head = self.snake[0].copy()
        
        # 根据方向更新蛇头位置
        if self.direction == curses.KEY_RIGHT:
            head[1] += 1
        elif self.direction == curses.KEY_LEFT:
            head[1] -= 1
        elif self.direction == curses.KEY_UP:
            head[0] -= 1
        elif self.direction == curses.KEY_DOWN:
            head[0] += 1
        
        # 碰撞检测：使用实际边界位置
        hit_obstacle = head in self.obstacles
        
        if (head[0] <= 1 or head[0] >= self.game_height -1 or 
            head[1] <= 0 or head[1] >= self.game_width - 1 or 
            head in self.snake[1:] or
            (hit_obstacle and not self.invincible_active)):  # 如果碰到障碍物且无敌状态未激活
            
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            return
        
        # 如果碰到障碍物但处于无敌状态
        if hit_obstacle and self.invincible_active:
            # 消耗一次无敌机会
            self.invincible_counter -= 1
            if self.invincible_counter <= 0:
                self.invincible_active = False
        
        # 添加新的蛇头
        self.snake.insert(0, head)
        
        # 检查是否吃到食物
        if head == self.food:
            # 根据是否激活得分倍增计算得分
            points = 20 if self.double_score_active else 10
            self.score += points
            
            # 更新得分倍增计数器
            if self.double_score_active:
                self.double_score_counter -= 1
                if self.double_score_counter <= 0:
                    self.double_score_active = False
            
            self.food = self.generate_food()
            
            # 每累计30分生成一个得分倍增球
            if self.score >= self.last_score_for_double + 30 and not self.double_score_item:
                self.double_score_item = self.generate_double_score_item()
                self.last_score_for_double = self.score
                
            # 每累计50分生成一个无敌球
            if self.score >= self.last_score_for_invincible + 50 and not self.invincible_item:
                self.invincible_item = self.generate_invincible_item()
                self.last_score_for_invincible = self.score
        else:
            # 如果没有吃到食物，移除蛇尾
            self.snake.pop()
        
        # 检查是否吃到得分倍增球
        if self.double_score_item and head == self.double_score_item:
            self.double_score_active = True
            self.double_score_counter = 5  # 可以连续使用5次
            self.double_score_item = None  # 移除道具
        
        # 检查是否吃到无敌球
        if self.invincible_item and head == self.invincible_item:
            self.invincible_active = True
            self.invincible_counter = 1  # 一次机会
            self.invincible_item = None  # 移除道具
    
    def run(self):
        # 设置curses
        curses.curs_set(0)  # 隐藏光标
        self.stdscr.nodelay(1)  # 非阻塞输入
        self.stdscr.timeout(100)  # 设置超时
        
        while True:
            # 绘制游戏
            self.draw_game()
            
            # 处理输入
            key = self.stdscr.getch()
            
            # 退出游戏
            if key in [ord('q'), ord('Q')]:
                break
            
            # 重新开始游戏
            if key in [ord('r'), ord('R')]:
                self.initialize_game()
                continue
            
            # 暂停/继续游戏
            if key in [ord('p'), ord('P')]:
                self.paused = not self.paused
            
            if self.game_over or self.paused:
                continue
            
            # 处理方向键
            if key in [curses.KEY_RIGHT, curses.KEY_LEFT, curses.KEY_UP, curses.KEY_DOWN]:
                # 防止直接反向移动
                if (key == curses.KEY_RIGHT and self.direction != curses.KEY_LEFT or
                    key == curses.KEY_LEFT and self.direction != curses.KEY_RIGHT or
                    key == curses.KEY_UP and self.direction != curses.KEY_DOWN or
                    key == curses.KEY_DOWN and self.direction != curses.KEY_UP):
                    self.direction = key
            
            # 更新游戏状态
            self.update_game()
            
            # 控制游戏速度
            time.sleep(SPEED)

def select_difficulty(stdscr):
    """显示难度选择菜单并返回用户选择"""
    stdscr.clear()
    stdscr.addstr(0, 0, "请选择难度：")
    stdscr.addstr(2, 0, "0: 简单 - 无额外障碍")
    stdscr.addstr(3, 0, "1: 中等 - 五个正方形障碍")
    stdscr.addstr(4, 0, "2: 困难 - 五个菱形障碍")
    stdscr.addstr(6, 0, "按数字键选择 (0, 1, 2):")
    
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        if key in [ord('0'), ord('1'), ord('2')]:
            return int(chr(key))

def main(stdscr):
    # 初始化颜色
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)      # 无敌球 - 红色
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)    # 无敌状态蛇 - 绿色
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # 得分倍增球 - 黄色
    
    # 选择难度
    difficulty = select_difficulty(stdscr)
    
    # 创建游戏实例并运行
    game = SnakeGame(stdscr, difficulty)
    game.run()

if __name__ == "__main__":
    # 检查是否在WSL环境中
    if "microsoft" not in os.uname().release.lower():
        print("警告：此游戏设计在WSL环境中运行。")
        print("按Enter键继续...", end="")
        input()
    
    # 启动游戏
    curses.wrapper(main)