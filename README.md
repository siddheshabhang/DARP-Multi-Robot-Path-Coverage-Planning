# Multi-Robot Path Planning - Semester Project

## 🤖 Project Overview

This project extends the DARP (Divide Areas Algorithm for Optimal Multi-Robot Coverage Path Planning) algorithm with interactive visualization and real-time simulation capabilities. Built for a semester-long robotics research project.

## ✨ Features

- **Interactive Grid Visualization**: Real-time pygame-based visualization with smooth animations
- **Multi-Robot Territory Assignment**: Automatic territory division based on proximity
- **Dynamic Obstacle Placement**: Click to add/remove obstacles in real-time
- **Statistics Dashboard**: Live coverage metrics and robot performance data
- **Professional UI**: Modern color scheme with intuitive controls

## 🚀 Quick Start

### Installation

1. **Clone or navigate to the project**:
```bash
cd ~/Desktop/DARP-Semester-Project
```

2. **Dependencies are already installed!** The virtual environment is ready to use.

### Running the Visualization Demo

```bash
./run.sh visualization_demo.py
```

This will launch an interactive window showing 3 robots dividing a 15x15 grid territory.

## 🎮 Interactive Controls

| Key | Action |
|-----|--------|
| **Click** | Add or remove obstacles |
| **A** | Auto-assign territories to robots |
| **R** | Reset the grid |
| **ESC** | Quit the application |

## 📊 Demo Features

The visualization demo includes:
- 3 robots positioned at strategic locations
- Pre-placed obstacle patterns to demonstrate avoidance
- Color-coded territories (Blue, Green, Purple)
- Real-time statistics panel showing coverage data

## 🛠️ Project Structure

```
DARP-Semester-Project/
├── visualization_demo.py    # Main interactive visualization
├── requirements.txt          # Python dependencies
├── run.sh                   # Execution script
├── venv/                    # Virtual environment
└── README.md               # This file
```

## 📦 Dependencies

- Python 3.12+
- NumPy 2.3+ (for numerical computations)
- Pygame 2.5+ (for interactive visualization)
- OpenCV 4.8+ (for image processing)
- SciPy 1.11+ (for optimization)
- Matplotlib 3.7+ (for plotting)
- Jupyter (for notebooks)
- Numba (for JIT compilation)
- scikit-learn (for ML algorithms)

## 🎯 Semester Project Roadmap

This is the **initial setup** for the semester project. Future extensions will include:

### Phase 1: Foundation (Weeks 1-3) ✅
- [x] Project setup and environment configuration
- [x] Interactive grid visualization
- [x] Basic territory assignment

### Phase 2: Algorithm Enhancement (Weeks 4-8)
- [x] Implement Voronoi-based initial partitioning (Euclidean distance)
- [ ] Implement complete DARP iterative refinement
- [ ] Add dynamic obstacle detection
- [ ] Optimize territory reallocation
- [ ] Path planning with turn minimization

### Phase 3: Advanced Features (Weeks 9-12)
- [ ] Multi-objective optimization
- [ ] Battery/energy constraints
- [ ] Communication range limitations
- [ ] Cooperative behavior strategies

### Phase 4: Validation (Weeks 13-15)
- [ ] Performance benchmarking
- [ ] Comparison with existing algorithms
- [ ] Simulation in complex environments
- [ ] Documentation and final report

## 💡 Usage Examples

### Basic Run
```bash
./run.sh visualization_demo.py
```

### Future: Run with Custom Configuration
```bash
# Coming soon: parameterized runs
./run.sh main.py --robots 4 --grid 20x20 --obstacles random
```

## 🎓 Academic Context

This project demonstrates:
- Multi-agent coordination
- Coverage path planning
- Real-time visualization
- Algorithm optimization
- Interactive simulation

Perfect for presenting to professors and demonstrating understanding of robotics concepts!

## 📝 Notes

> **For Professor Demo**: Run `./run.sh visualization_demo.py` to see the interactive simulation. Click to place obstacles, press 'A' to auto-assign territories, and watch the robots divide the workspace!

## 🔧 Troubleshooting

If you encounter any issues:

```bash
# Reinstall dependencies
./venv/bin/pip install -r requirements.txt

# Check Python version
python3 --version  # Should be 3.12+
```

## 📚 References

Based on:
- DARP Algorithm: [Kapoutsis et al., "DARP: Divide Areas Algorithm for Optimal Multi-Robot Coverage Path Planning"](https://zenodo.org/record/2591050)
- Spanning Tree Coverage: [Gabriely & Rimon](https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.479.5125&rep=rep1&type=pdf)

## 📄 License

Educational project for semester coursework.

---

**Ready to impress!** 🌟 Run the demo and show your professor an interactive multi-robot path planning simulation!
