import numpy as np
import cv2
from typing import List, Tuple, Dict


class DARPPartitioner:

    def __init__(
        self,
        grid: np.ndarray,
        robot_positions: List[Tuple[int, int]],
        max_iterations: int = 2000,
        balance_tolerance: float = 0.05,
        connectivity: int = 8,
    ):
        self.grid = grid.copy()
        self.rows, self.cols = grid.shape
        self.robot_positions = robot_positions
        self.num_robots = len(robot_positions)
        self.max_iterations = max_iterations
        self.balance_tolerance = balance_tolerance
        self.connectivity = connectivity

        self.initial_grid = None
        self.iteration_count = 0
        self.stall_count = 0

        # Precompute distance matrices
        self.distance_matrices = []
        for rpos in robot_positions:
            dm = np.zeros((self.rows, self.cols))
            for i in range(self.rows):
                for j in range(self.cols):
                    dm[i, j] = np.sqrt((i - rpos[0]) ** 2 + (j - rpos[1]) ** 2)
            self.distance_matrices.append(dm)

    # ----------------------------------------------------------
    # ORIGINAL VORONOI — produces connected territories
    # ----------------------------------------------------------

    def initial_voronoi_partition(self):
        """
        Standard nearest-robot Voronoi partition.
        Each free cell is assigned to the closest robot (Euclidean distance).
        Guarantees every territory is connected.
        Obstacles (grid == -1) are preserved.
        """
        # First stamp robot home cells so they're never reassigned
        for idx, rpos in enumerate(self.robot_positions):
            self.grid[rpos[0], rpos[1]] = idx + 1

        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] != 0:   # skip obstacles (-1) and robot cells
                    continue
                best, best_d = 0, float("inf")
                for r in range(self.num_robots):
                    d = self.distance_matrices[r][i, j]
                    if d < best_d:
                        best_d, best = d, r + 1
                self.grid[i, j] = best

        self.initial_grid = self.grid.copy()

    # ----------------------------------------------------------

    def get_territory_sizes(self):
        return [int(np.sum(self.grid == (r + 1))) for r in range(self.num_robots)]

    def _free_cells(self):
        return int(np.sum(self.grid != -1))

    def _is_robot_cell(self, i, j):
        return (i, j) in self.robot_positions

    def check_connectivity(self, robot_idx):
        mask = (self.grid == robot_idx + 1).astype(np.uint8)
        if np.sum(mask) == 0:
            return True
        n, _ = cv2.connectedComponents(mask, connectivity=self.connectivity)
        return n == 2   # 1 background + 1 foreground

    # ----------------------------------------------------------
    # BALANCE STEP — handles any robot placement including clustered
    # ----------------------------------------------------------

    def balance_step(self):
        """
        Transfer one border cell from a larger region to a smaller region.

        Works correctly even when robots are clustered (e.g. all in the same
        corner) by:

        1. Trying EVERY under-sized robot as a potential receiver, smallest
           first.  This avoids deadlock when the globally-smallest robot
           cannot receive directly (no border with a donor).

        2. For each receiver, trying donors in descending size order (largest
           first).  This steers the "relay" chain  R_large → R_middle → R_small
           rather than letting middle robots steal from each other.

        3. Sorting candidates by distance to the receiver's robot home so
           that territory grows toward the robot rather than drifting away.

        4. No random shuffle — deterministic, monotonic progress.
        """
        sizes   = self.get_territory_sizes()
        if max(sizes) - min(sizes) <= 1:
            return False

        nb8 = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

        # Try receivers from smallest to largest
        recv_order = sorted(range(self.num_robots), key=lambda i: sizes[i])

        for recv_idx in recv_order:
            recv_id  = recv_idx + 1

            # Donors must be strictly larger than this receiver
            donors = sorted(
                [i for i in range(self.num_robots) if sizes[i] > sizes[recv_idx]],
                key=lambda i: -sizes[i]   # largest donor first
            )

            for donor_idx in donors:
                donor_id = donor_idx + 1

                # Border cells of donor that touch the receiver's territory
                candidates = []
                for i in range(self.rows):
                    for j in range(self.cols):
                        if self.grid[i, j] != donor_id:
                            continue
                        if self._is_robot_cell(i, j):
                            continue
                        for dr, dc in nb8:
                            ni, nj = i + dr, j + dc
                            if (0 <= ni < self.rows and 0 <= nj < self.cols
                                    and self.grid[ni, nj] == recv_id):
                                d = self.distance_matrices[recv_idx][i, j]
                                candidates.append((d, i, j))
                                break

                # Closest to receiver's robot home first
                candidates.sort(key=lambda x: x[0])

                for _, ci, cj in candidates:
                    self.grid[ci, cj] = recv_id
                    if (self.check_connectivity(donor_idx)
                            and self.check_connectivity(recv_idx)):
                        return True          # committed transfer
                    self.grid[ci, cj] = donor_id   # revert

        return False

    # ----------------------------------------------------------

    def is_converged(self):
        sizes = self.get_territory_sizes()
        if min(sizes) == 0:
            return False
        return (max(sizes) - min(sizes)) <= 1

    # ----------------------------------------------------------

    def optimize_partition(self, verbose=True):
        self.initial_voronoi_partition()
        self.iteration_count = 0
        self.stall_count     = 0

        while self.iteration_count < self.max_iterations:
            if self.is_converged():
                break
            changed = self.balance_step()
            self.iteration_count += 1
            if not changed:
                self.stall_count += 1
                if self.stall_count > 200:
                    break
            else:
                self.stall_count = 0

        return {
            "grid":            self.grid.copy(),
            "iterations":      self.iteration_count,
            "territory_sizes": self.get_territory_sizes(),
            "converged":       self.is_converged(),
        }

    # ----------------------------------------------------------

    def print_matrices(self):
        sizes = self.get_territory_sizes()
        print("\n=== DARP RESULT ===")
        print("Sizes:", sizes)
        mx, mn = max(sizes), min(sizes)
        avg      = np.mean(sizes)
        imbalance = ((mx - mn) / avg * 100) if avg else 0
        print("Imbalance:", round(imbalance, 2), "%")
