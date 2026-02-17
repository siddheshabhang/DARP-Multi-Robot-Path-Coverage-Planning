import pygame
import numpy as np
import sys
from typing import List, Tuple, Optional
from darp_algorithm import DARPPartitioner

COLORS = {
    'background': (15, 23, 42),
    'grid_line': (51, 65, 85),
    'obstacle': (239, 68, 68),
    'free_cell': (248, 250, 252),
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
    def __init__(self, rows: int = 15, cols: int = 15, cell_size: int = 40):
        pygame.init()

        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

        self.info_panel_width = 300
        self.grid_width = cols * cell_size
        self.grid_height = rows * cell_size
        self.window_width = self.grid_width + self.info_panel_width
        self.window_height = self.grid_height + 100

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Multi-Robot Path Planning Visualization")

        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        # Grid state
        self.grid = np.zeros((rows, cols), dtype=int)
        self.obstacles = set()
        self.robot_positions = []
        self.paths = []

        self.clock = pygame.time.Clock()
        self.running = True

        # DARP animation state
        self.darp: Optional[DARPPartitioner] = None
        self.darp_running = False         # True while optimizing
        self.darp_done = False            # True after optimization finished
        self.darp_phase = ""              # "voronoi" or "balancing"
        self.iteration_count = 0
        self.stall_count = 0
        self.converged = False
        self.anim_delay_ms = 80           # ms between balance steps

    # ---- robots / obstacles ----
    def add_robot(self, position: Tuple[int, int], color_idx: int = 0):
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
        row, col = position
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if (row, col) not in [r['position'] for r in self.robot_positions]:
                self.obstacles.add((row, col))
                self.grid[row, col] = -1

    def remove_obstacle(self, position: Tuple[int, int]):
        if position in self.obstacles:
            self.obstacles.remove(position)
            self.grid[position[0], position[1]] = 0

    # ---- DARP helpers ----
    def _sync_territories_from_darp(self):
        """Copy grid from partitioner into self.grid and update territory sets."""
        self.grid = self.darp.grid.copy()
        for idx, robot in enumerate(self.robot_positions):
            robot['territory'] = set()
            rid = idx + 1
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.grid[i, j] == rid:
                        robot['territory'].add((i, j))

    def start_darp(self):
        """Kick off an animated DARP run."""
        # Reset the grid keeping obstacles
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] > 0:
                    self.grid[i, j] = 0
        # Re-place robot IDs
        for idx, r in enumerate(self.robot_positions):
            self.grid[r['position'][0], r['position'][1]] = idx + 1

        robot_pos_list = [r['position'] for r in self.robot_positions]
        self.darp = DARPPartitioner(
            grid=self.grid,
            robot_positions=robot_pos_list,
            max_iterations=500,
            balance_tolerance=0.05,
            connectivity=4
        )

        # Phase 1: Voronoi
        self.darp.initial_voronoi_partition()
        self._sync_territories_from_darp()

        print("\n🤖 DARP started — Voronoi partition applied")
        print(f"   Sizes: {self.darp.get_territory_sizes()}")

        self.darp_running = True
        self.darp_done = False
        self.darp_phase = "balancing"
        self.iteration_count = 0
        self.stall_count = 0
        self.converged = False
        self._last_step_time = pygame.time.get_ticks()

    def darp_tick(self):
        """Called every frame while DARP is running. Does one balance step
        if enough time has passed, so the user can watch the process."""
        now = pygame.time.get_ticks()
        if now - self._last_step_time < self.anim_delay_ms:
            return

        self._last_step_time = now

        # Check convergence
        if self.darp.is_converged():
            self._finish_darp("✓ Converged")
            return

        if self.iteration_count >= self.darp.max_iterations:
            self._finish_darp("✓ Max iterations reached")
            return

        changed = self.darp.balance_step()
        self.iteration_count += 1

        if changed:
            self.stall_count = 0
            self._sync_territories_from_darp()
        else:
            self.stall_count += 1
            if self.stall_count > 30:
                self._finish_darp("✓ Stalled (no more moves)")
                return

        if self.iteration_count % 10 == 0:
            print(f"  Iter {self.iteration_count}: "
                  f"sizes = {self.darp.get_territory_sizes()}")

    def _finish_darp(self, reason: str):
        self.darp.iteration_count = self.iteration_count
        self.converged = self.darp.is_converged()
        self.darp_running = False
        self.darp_done = True
        self._sync_territories_from_darp()
        sizes = self.darp.get_territory_sizes()
        print(f"\n{reason} after {self.iteration_count} iterations")
        print(f"   Final sizes: {sizes}")
        # Print matrices to terminal
        self.darp.print_matrices()

    # ---- drawing ----
    def draw_grid(self):
        for i in range(self.rows):
            for j in range(self.cols):
                x = j * self.cell_size
                y = i * self.cell_size + 80

                if (i, j) in self.obstacles:
                    color = COLORS['obstacle']
                elif self.grid[i, j] > 0:
                    ridx = self.grid[i, j] - 1
                    color = COLORS['path_colors'][ridx % len(COLORS['path_colors'])]
                else:
                    color = COLORS['free_cell']

                pygame.draw.rect(self.screen, color,
                                 (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, COLORS['grid_line'],
                                 (x, y, self.cell_size, self.cell_size), 1)

        # Robots
        for idx, robot in enumerate(self.robot_positions):
            row, col = robot['position']
            cx = col * self.cell_size + self.cell_size // 2
            cy = row * self.cell_size + 80 + self.cell_size // 2
            c = COLORS['robot_colors'][idx % len(COLORS['robot_colors'])]
            pygame.draw.circle(self.screen, c, (cx, cy), self.cell_size // 3)
            pygame.draw.circle(self.screen, COLORS['text'], (cx, cy),
                               self.cell_size // 3, 2)
            txt = self.font.render(str(idx + 1), True, COLORS['text'])
            self.screen.blit(txt, txt.get_rect(center=(cx, cy)))

    def draw_info_panel(self):
        px = self.grid_width
        py = 80
        pygame.draw.rect(self.screen, COLORS['panel_bg'],
                         (px, py, self.info_panel_width, self.grid_height))

        y = py + 20
        self.screen.blit(self.font.render("Statistics", True, COLORS['text']),
                         (px + 20, y))
        y += 50

        # DARP status
        if self.darp_running:
            self.screen.blit(
                self.small_font.render("DARP: running...", True, COLORS['highlight']),
                (px + 20, y))
            y += 22
            self.screen.blit(
                self.small_font.render(f"  Iteration: {self.iteration_count}",
                                       True, COLORS['text']),
                (px + 30, y))
            y += 30
        elif self.darp_done:
            self.screen.blit(
                self.small_font.render("DARP: done", True, COLORS['highlight']),
                (px + 20, y))
            y += 22
            self.screen.blit(
                self.small_font.render(f"  Iterations: {self.iteration_count}",
                                       True, COLORS['text']),
                (px + 30, y))
            y += 20
            tag = "Yes ✓" if self.converged else "No"
            self.screen.blit(
                self.small_font.render(f"  Converged: {tag}",
                                       True, COLORS['text']),
                (px + 30, y))
            y += 30

        # Per-robot
        for idx, robot in enumerate(self.robot_positions):
            c = COLORS['robot_colors'][idx % len(COLORS['robot_colors'])]
            pygame.draw.circle(self.screen, c, (px + 30, y + 10), 8)
            self.screen.blit(
                self.small_font.render(f"Robot {idx+1}", True, COLORS['text']),
                (px + 50, y))
            y += 25
            n = len(robot['territory'])
            self.screen.blit(
                self.small_font.render(f"  Cells: {n}", True, COLORS['text']),
                (px + 50, y))
            y += 30

        # Controls
        y = self.window_height - 180
        for line in ["Controls:",
                      "Click: Add/Remove Obstacle",
                      "R: Reset Grid",
                      "D: Run DARP (animated)",
                      "A: Simple Voronoi",
                      "ESC: Quit"]:
            self.screen.blit(
                self.small_font.render(line, True, COLORS['text']),
                (px + 20, y))
            y += 25

    def draw_title(self):
        t = self.title_font.render("Multi-Robot Path Planning", True, COLORS['text'])
        self.screen.blit(t, t.get_rect(center=(self.window_width // 2, 40)))

    # ---- events ----
    def handle_click(self, pos):
        x, y = pos
        if x < self.grid_width and y >= 80:
            col = x // self.cell_size
            row = (y - 80) // self.cell_size
            if 0 <= row < self.rows and 0 <= col < self.cols:
                if (row, col) in self.obstacles:
                    self.remove_obstacle((row, col))
                elif (row, col) not in [r['position'] for r in self.robot_positions]:
                    self.add_obstacle((row, col))

    # ---- main loop ----
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.darp_running:
                        self.handle_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.grid = np.zeros((self.rows, self.cols), dtype=int)
                        self.obstacles.clear()
                        for r in self.robot_positions:
                            r['territory'].clear()
                        self.darp_running = False
                        self.darp_done = False
                        self.iteration_count = 0
                    elif event.key == pygame.K_d and not self.darp_running:
                        self.start_darp()
                    elif event.key == pygame.K_a and not self.darp_running:
                        for r in self.robot_positions:
                            r['territory'].clear()
                        self._simple_voronoi()
                        self.darp_done = False

            # Animated DARP step
            if self.darp_running:
                self.darp_tick()

            # Draw
            self.screen.fill(COLORS['background'])
            self.draw_title()
            self.draw_grid()
            self.draw_info_panel()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def _simple_voronoi(self):
        """Quick Voronoi for the A key (no DARP)."""
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] == -1:
                    continue
                best, bd = 0, float('inf')
                for idx, r in enumerate(self.robot_positions):
                    rr, rc = r['position']
                    d = np.sqrt((i - rr)**2 + (j - rc)**2)
                    if d < bd:
                        bd = d
                        best = idx + 1
                self.grid[i, j] = best
                self.robot_positions[best - 1]['territory'].add((i, j))


def demo():
    grid = InteractiveGrid(rows=15, cols=15, cell_size=40)

    grid.add_robot((0, 0), color_idx=0)   # Robot 1 - Blue
    grid.add_robot((7, 12), color_idx=1)   # Robot 2 - Green
    grid.add_robot((12, 7), color_idx=2)   # Robot 3 - Purple

    obstacles = [
        (5, 5), (5, 6), (5, 7),
        (6, 5), (6, 6), (6, 7),
        (10, 3), (10, 4), (10, 5),
        (3, 10), (4, 10), (5, 10),
    ]
    for obs in obstacles:
        grid.add_obstacle(obs)

    # Auto-start DARP so the process is visible immediately
    grid.start_darp()

    grid.run()


if __name__ == "__main__":
    demo()
