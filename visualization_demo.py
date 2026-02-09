"""
Interactive Grid-based Visualization for Multi-Robot Path Planning
Based on DARP (Divide Areas Algorithm for Optimal Multi-Robot Coverage Path Planning)

This module provides an interactive pygame-based visualization for demonstrating
multi-robot path planning algorithms with real-time animation.
"""

import pygame
import numpy as np
import sys
from typing import List, Tuple, Optional

# Color definitions for a modern, professional look
COLORS = {
    'background': (15, 23, 42),      # Dark slate background
    'grid_line': (51, 65, 85),        # Subtle grid lines
    'obstacle': (239, 68, 68),        # Red for obstacles
    'free_cell': (248, 250, 252),     # Light gray for free cells
    'robot_colors': [
        (59, 130, 246),   # Blue
        (34, 197, 94),    # Green
        (168, 85, 247),   # Purple
        (251, 146, 60),   # Orange
        (236, 72, 153),   # Pink
    ],
    'path_colors': [
        (147, 197, 253),  # Light blue
        (134, 239, 172),  # Light green
        (216, 180, 254),  # Light purple
        (253, 186, 116),  # Light orange
        (249, 168, 212),  # Light pink
    ],
    'text': (248, 250, 252),
    'panel_bg': (30, 41, 59),
    'highlight': (250, 204, 21),
}


class InteractiveGrid:
    """
    Interactive grid visualization for multi-robot path planning.
    
    Features:
    - Real-time visualization of robot territories
    - Interactive obstacle placement (click to add/remove)
    - Animated robot movement
    - Coverage statistics display
    """
    
    def __init__(self, rows: int = 15, cols: int = 15, cell_size: int = 40):
        """
        Initialize the interactive grid visualization.
        
        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            cell_size: Size of each cell in pixels
        """
        pygame.init()
        
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        
        # Calculate window dimensions
        self.info_panel_width = 300
        self.grid_width = cols * cell_size
        self.grid_height = rows * cell_size
        self.window_width = self.grid_width + self.info_panel_width
        self.window_height = self.grid_height + 100  # Extra space for title
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Multi-Robot Path Planning Visualization")
        
        # Initialize fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        
        # Grid state
        self.grid = np.zeros((rows, cols), dtype=int)  # 0: free, -1: obstacle, >0: robot territory
        self.obstacles = set()
        self.robot_positions = []
        self.paths = []
        
        # Animation
        self.clock = pygame.time.Clock()
        self.running = True
        
    def add_robot(self, position: Tuple[int, int], color_idx: int = 0):
        """Add a robot at the specified position."""
        row, col = position
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.robot_positions.append({
                'position': (row, col),
                'color_idx': color_idx,
                'territory': set(),
                'path': []
            })
            self.grid[row, col] = len(self.robot_positions)
    
    def add_obstacle(self, position: Tuple[int, int]):
        """Add an obstacle at the specified position."""
        row, col = position
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if (row, col) not in [(r['position']) for r in self.robot_positions]:
                self.obstacles.add((row, col))
                self.grid[row, col] = -1
    
    def remove_obstacle(self, position: Tuple[int, int]):
        """Remove an obstacle at the specified position."""
        if position in self.obstacles:
            self.obstacles.remove(position)
            self.grid[position[0], position[1]] = 0
    
    def assign_territories_simple(self):
        """Simple territory assignment based on distance."""
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] != -1:  # Not an obstacle
                    min_dist = float('inf')
                    assigned_robot = 0
                    
                    for idx, robot in enumerate(self.robot_positions):
                        r_row, r_col = robot['position']
                        dist = abs(i - r_row) + abs(j - r_col)  # Manhattan distance
                        
                        if dist < min_dist:
                            min_dist = dist
                            assigned_robot = idx + 1
                    
                    if assigned_robot > 0:
                        self.grid[i, j] = assigned_robot
                        self.robot_positions[assigned_robot - 1]['territory'].add((i, j))
    
    def draw_grid(self):
        """Draw the grid with territories and obstacles."""
        # Draw cells
        for i in range(self.rows):
            for j in range(self.cols):
                x = j * self.cell_size
                y = i * self.cell_size + 80  # Offset for title
                
                # Determine cell color
                if (i, j) in self.obstacles:
                    color = COLORS['obstacle']
                elif self.grid[i, j] > 0:
                    robot_idx = self.grid[i, j] - 1
                    if robot_idx < len(COLORS['path_colors']):
                        color = COLORS['path_colors'][robot_idx]
                    else:
                        color = COLORS['free_cell']
                else:
                    color = COLORS['free_cell']
                
                # Draw cell
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, COLORS['grid_line'], (x, y, self.cell_size, self.cell_size), 1)
        
        # Draw robots
        for idx, robot in enumerate(self.robot_positions):
            row, col = robot['position']
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + 80 + self.cell_size // 2
            
            if idx < len(COLORS['robot_colors']):
                color = COLORS['robot_colors'][idx]
            else:
                color = COLORS['highlight']
            
            # Draw robot as circle
            pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 3)
            pygame.draw.circle(self.screen, COLORS['text'], (x, y), self.cell_size // 3, 2)
            
            # Draw robot number
            robot_text = self.font.render(str(idx + 1), True, COLORS['text'])
            text_rect = robot_text.get_rect(center=(x, y))
            self.screen.blit(robot_text, text_rect)
    
    def draw_info_panel(self):
        """Draw information panel on the right side."""
        panel_x = self.grid_width
        panel_y = 80
        
        # Draw panel background
        pygame.draw.rect(self.screen, COLORS['panel_bg'], 
                        (panel_x, panel_y, self.info_panel_width, self.grid_height))
        
        # Title
        y_offset = panel_y + 20
        title = self.font.render("Statistics", True, COLORS['text'])
        self.screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 50
        
        # Robot statistics
        for idx, robot in enumerate(self.robot_positions):
            if idx < len(COLORS['robot_colors']):
                color = COLORS['robot_colors'][idx]
            else:
                color = COLORS['highlight']
            
            # Draw colored indicator
            pygame.draw.circle(self.screen, color, 
                             (panel_x + 30, y_offset + 10), 8)
            
            # Robot info
            text = self.small_font.render(f"Robot {idx + 1}", True, COLORS['text'])
            self.screen.blit(text, (panel_x + 50, y_offset))
            y_offset += 25
            
            # Territory size
            territory_size = len(robot['territory'])
            text = self.small_font.render(f"  Territory: {territory_size} cells", 
                                         True, COLORS['text'])
            self.screen.blit(text, (panel_x + 50, y_offset))
            y_offset += 35
        
        # Instructions
        y_offset = self.window_height - 180
        instructions = [
            "Controls:",
            "Click: Add/Remove Obstacle",
            "R: Reset Grid",
            "A: Auto Assign",
            "ESC: Quit"
        ]
        
        for instruction in instructions:
            text = self.small_font.render(instruction, True, COLORS['text'])
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 25
    
    def draw_title(self):
        """Draw the title at the top."""
        title = self.title_font.render("Multi-Robot Path Planning", True, COLORS['text'])
        title_rect = title.get_rect(center=(self.window_width // 2, 40))
        self.screen.blit(title, title_rect)
    
    def handle_click(self, pos: Tuple[int, int]):
        """Handle mouse click events."""
        x, y = pos
        
        # Only handle clicks in grid area
        if x < self.grid_width and y >= 80:
            col = x // self.cell_size
            row = (y - 80) // self.cell_size
            
            if 0 <= row < self.rows and 0 <= col < self.cols:
                if (row, col) in self.obstacles:
                    self.remove_obstacle((row, col))
                elif (row, col) not in [r['position'] for r in self.robot_positions]:
                    self.add_obstacle((row, col))
    
    def run(self):
        """Main loop for the visualization."""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        # Reset grid
                        self.grid = np.zeros((self.rows, self.cols), dtype=int)
                        self.obstacles.clear()
                        for robot in self.robot_positions:
                            robot['territory'].clear()
                    elif event.key == pygame.K_a:
                        # Auto assign territories
                        for robot in self.robot_positions:
                            robot['territory'].clear()
                        self.assign_territories_simple()
            
            # Draw everything
            self.screen.fill(COLORS['background'])
            self.draw_title()
            self.draw_grid()
            self.draw_info_panel()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()


def demo():
    """Run a demo of the interactive grid visualization."""
    # Create a 15x15 grid
    grid = InteractiveGrid(rows=15, cols=15, cell_size=40)
    
    # Add 3 robots at different positions
    grid.add_robot((2, 2), color_idx=0)    # Robot 1 - Blue
    grid.add_robot((7, 12), color_idx=1)   # Robot 2 - Green
    grid.add_robot((12, 7), color_idx=2)   # Robot 3 - Purple
    
    # Add some initial obstacles to show the concept
    obstacles = [
        (5, 5), (5, 6), (5, 7),
        (6, 5), (6, 6), (6, 7),
        (10, 3), (10, 4), (10, 5),
        (3, 10), (4, 10), (5, 10),
    ]
    
    for obs in obstacles:
        grid.add_obstacle(obs)
    
    # Assign territories
    grid.assign_territories_simple()
    
    # Run the visualization
    grid.run()


if __name__ == "__main__":
    demo()
