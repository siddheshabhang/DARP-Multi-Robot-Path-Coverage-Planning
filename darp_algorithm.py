"""
DARP (Divide Areas Algorithm for Optimal Multi-Robot Coverage Path Planning)

This module implements the complete DARP algorithm with iterative territory
refinement based on Euclidean distance matrix convergence.

Author: DARP Semester Project
Date: February 2026
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional


class DARPPartitioner:
    """
    DARP Algorithm for optimal multi-robot territory partitioning.

    Uses iterative refinement with Euclidean distance matrices to converge
    to balanced territories (equal cell counts) across all robots.
    """

    def __init__(self,
                 grid: np.ndarray,
                 robot_positions: List[Tuple[int, int]],
                 max_iterations: int = 500,
                 balance_tolerance: float = 0.05,
                 connectivity: int = 4):
        self.grid = grid.copy()
        self.rows, self.cols = grid.shape
        self.robot_positions = robot_positions
        self.num_robots = len(robot_positions)
        self.max_iterations = max_iterations
        self.balance_tolerance = balance_tolerance
        self.connectivity = connectivity

        # Precompute distance matrices (these never change)
        self.distance_matrices = []
        for idx, rpos in enumerate(robot_positions):
            dm = np.zeros((self.rows, self.cols), dtype=float)
            for i in range(self.rows):
                for j in range(self.cols):
                    dm[i, j] = np.sqrt((i - rpos[0])**2 + (j - rpos[1])**2)
            self.distance_matrices.append(dm)

        # Metrics
        self.initial_grid = None
        self.iteration_count = 0
        self.stall_count = 0

    def initial_voronoi_partition(self):
        """Assign each free cell to its nearest robot."""
        # Lock robot positions first
        for idx, rpos in enumerate(self.robot_positions):
            self.grid[rpos[0], rpos[1]] = idx + 1

        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] != 0:       # obstacle (-1) or robot cell
                    continue
                best_r = 0
                best_d = float('inf')
                for idx in range(self.num_robots):
                    d = self.distance_matrices[idx][i, j]
                    if d < best_d:
                        best_d = d
                        best_r = idx + 1
                self.grid[i, j] = best_r

        self.initial_grid = self.grid.copy()

    # ------------------------------------------------------------------
    def get_territory_sizes(self) -> List[int]:
        return [int(np.sum(self.grid == (r + 1))) for r in range(self.num_robots)]

    def _is_robot_cell(self, i: int, j: int) -> bool:
        for rpos in self.robot_positions:
            if (i, j) == rpos:
                return True
        return False

    def check_connectivity(self, robot_idx: int) -> bool:
        mask = (self.grid == robot_idx + 1).astype(np.uint8)
        if np.sum(mask) == 0:
            return True
        n, _ = cv2.connectedComponents(mask, connectivity=self.connectivity)
        return n == 2   # background + one component

    # ------------------------------------------------------------------
    def balance_step(self) -> bool:
        """
        One iteration: move a boundary cell from the largest territory to the
        smallest territory so that sizes converge.  Tries multiple candidates
        so it doesn't get stuck on one failed connectivity check.
        """
        sizes = self.get_territory_sizes()
        max_idx = int(np.argmax(sizes))
        min_idx = int(np.argmin(sizes))

        if sizes[max_idx] - sizes[min_idx] <= 1:
            return False  # already as equal as possible

        # Collect boundary cells of the largest territory that border
        # the smallest territory
        big_id = max_idx + 1
        small_id = min_idx + 1
        candidates = []

        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] != big_id:
                    continue
                if self._is_robot_cell(i, j):
                    continue
                # must be adjacent to the small territory
                for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < self.rows and 0 <= nj < self.cols:
                        if self.grid[ni, nj] == small_id:
                            # distance to the small robot (lower is better)
                            d = self.distance_matrices[min_idx][i, j]
                            candidates.append((d, i, j))
                            break

        if not candidates:
            # No direct border between big and small.
            # Fall back: take any boundary cell of big territory
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.grid[i, j] != big_id:
                        continue
                    if self._is_robot_cell(i, j):
                        continue
                    for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.rows and 0 <= nj < self.cols:
                            nv = self.grid[ni, nj]
                            if nv > 0 and nv != big_id:
                                d = self.distance_matrices[min_idx][i, j]
                                candidates.append((d, i, j))
                                break

        # Sort by distance to small-robot (closest first)
        candidates.sort()

        for _, ci, cj in candidates:
            old = self.grid[ci, cj]
            self.grid[ci, cj] = small_id

            if self.check_connectivity(max_idx) and self.check_connectivity(min_idx):
                return True          # success

            self.grid[ci, cj] = old  # revert

        return False                 # every candidate broke connectivity

    # ------------------------------------------------------------------
    def is_converged(self) -> bool:
        sizes = self.get_territory_sizes()
        if min(sizes) == 0:
            return False
        return (max(sizes) - min(sizes)) <= 1

    # ------------------------------------------------------------------
    def optimize_partition(self, verbose: bool = True) -> Dict:
        """Run full optimisation (blocking).  Used by test_darp.py."""
        self.initial_voronoi_partition()

        if verbose:
            print("\n" + "="*60)
            print("DARP OPTIMIZATION STARTED")
            print("="*60)
            print(f"Robots: {self.num_robots}  Grid: {self.rows}x{self.cols}")
            print(f"Free cells: {int(np.sum(self.grid > 0))}  "
                  f"Obstacles: {int(np.sum(self.grid == -1))}")

        self.iteration_count = 0
        self.stall_count = 0
        while self.iteration_count < self.max_iterations:
            if self.is_converged():
                if verbose:
                    print(f"\n✓ Converged after {self.iteration_count} iterations")
                break

            changed = self.balance_step()
            self.iteration_count += 1

            if not changed:
                self.stall_count += 1
                if self.stall_count > 20:
                    if verbose:
                        print(f"\n✓ Stalled after {self.iteration_count} iterations")
                    break
            else:
                self.stall_count = 0

            if verbose and self.iteration_count % 10 == 0:
                print(f"  Iter {self.iteration_count}: sizes = "
                      f"{self.get_territory_sizes()}")

        return {
            'grid': self.grid.copy(),
            'iterations': self.iteration_count,
            'territory_sizes': self.get_territory_sizes(),
            'converged': self.is_converged(),
        }

    # ------------------------------------------------------------------
    def print_matrices(self):
        """Print initial and optimised distance matrices to terminal."""
        sizes = self.get_territory_sizes()

        print("\n" + "="*60)
        print("EUCLIDEAN DISTANCE MATRICES")
        print("="*60)

        for label, grid_snap in [("INITIAL PARTITION", self.initial_grid),
                                  ("OPTIMIZED PARTITION", self.grid)]:
            print("\n" + "-"*60)
            print(f"{label}")
            print("-"*60)
            for r in range(self.num_robots):
                rid = r + 1
                cells = [(i, j) for i in range(self.rows)
                         for j in range(self.cols) if grid_snap[i, j] == rid]
                dists = [self.distance_matrices[r][i, j] for i, j in cells]
                n = len(cells)
                mean_d = np.mean(dists) if dists else 0
                std_d = np.std(dists) if dists else 0
                print(f"\n📍 Robot {rid} @ {self.robot_positions[r]}")
                print(f"   Cells: {n}  |  Dist mean: {mean_d:.2f}  "
                      f"std: {std_d:.2f}")

        print("\n" + "="*60)
        print("CONVERGENCE SUMMARY")
        print("="*60)
        print(f"Iterations : {self.iteration_count}")
        print(f"Sizes      : {sizes}")
        mx, mn = max(sizes), min(sizes)
        avg = np.mean(sizes)
        print(f"Range      : {mn} – {mx}  (avg {avg:.1f})")
        pct = ((mx - mn) / avg * 100) if avg else 0
        print(f"Imbalance  : {pct:.1f}%")
        print(f"Converged  : {'✓ Yes' if self.is_converged() else '✗ No'}")
        print("="*60 + "\n")
