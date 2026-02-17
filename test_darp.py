#!/usr/bin/env python3
"""
Test script to demonstrate DARP algorithm without GUI.
Prints distance matrices to terminal.
"""

import numpy as np
from darp_algorithm import DARPPartitioner


def test_darp_algorithm():
    print("\n" + "="*70)
    print("DARP ALGORITHM TEST")
    print("="*70)

    rows, cols = 10, 10
    grid = np.zeros((rows, cols), dtype=int)

    obstacles = [
        (4, 4), (4, 5), (5, 4), (5, 5),
        (2, 7), (3, 7), (4, 7),
    ]
    for r, c in obstacles:
        grid[r, c] = -1

    robot_positions = [
        (1, 1),
        (8, 8),
        (1, 8),
    ]

    print(f"\nGrid: {rows}x{cols}  |  Robots: {len(robot_positions)}  "
          f"|  Obstacles: {len(obstacles)}")

    part = DARPPartitioner(
        grid=grid,
        robot_positions=robot_positions,
        max_iterations=500,
        balance_tolerance=0.05,
        connectivity=4
    )

    results = part.optimize_partition(verbose=True)
    part.print_matrices()

    sizes = results['territory_sizes']
    print(f"\nFinal sizes : {sizes}")
    print(f"Converged   : {'Yes' if results['converged'] else 'No'}")
    print(f"Iterations  : {results['iterations']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_darp_algorithm()
