# Dogzilla Simulation Setup

This repository contains the simulation configuration for the **Dogzilla** robot (based on Yahboom XGO) using **Champ** and **Ignition Gazebo (Gazebo Sim)**. It is adapted from the Unitree Go2 ROS2 integration.

## Packages

*   `dogzilla_description`: Contains the URDF/Xacro robot description, meshes, and basic visualization launch files.
*   `dogzilla_config`: Contains the Champ configuration (gait, joints, links), ROS 2 Control parameters, and launch files for simulation, navigation, and SLAM.

## Prerequisites

*   ROS 2 Humble (or compatible)
*   Ignition Fortress (Gazebo Sim)
*   `champ_bringup`, `champ_navigation`, `champ_gazebo` (from Champ framework)
*   `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control`

## Installation

Ensure you have the Champ packages installed or in your workspace. You can clone the Champ repository if not installed via apt.

```bash
sudo apt install ros-humble-champ-bringup ros-humble-champ-navigation ros-humble-ros-gz-sim ros-humble-gz-ros2-control
```

Build the workspace:

```bash
colcon build --packages-select dogzilla_description dogzilla_config
source install/setup.bash
```

## Usage

### 1. Launch Simulation

To launch the Dogzilla robot in Ignition Gazebo with Champ controllers:

```bash
ros2 launch dogzilla_config gazebo.launch.py
```

Optional arguments:
*   `rviz`: Set to `true` to launch RViz (default: `false`).
*   `gui`: Set to `false` for headless mode (default: `true`).

### 2. Autonomous Navigation

To launch the navigation stack (Nav2) with a pre-built map:

```bash
ros2 launch dogzilla_config navigate.launch.py
```

### 3. SLAM (Mapping)

To generate a new map using SLAM:

```bash
ros2 launch dogzilla_config slam.launch.py
```

## Configuration Details

*   **Robot Description**: The Xacro file in `dogzilla_description` has been adapted to include necessary inertia values and collision geometries (spheres for feet) required for stable simulation. It uses the `gz_ros2_control` plugin.
*   **Controllers**: The robot uses a `JointTrajectoryController` (`joint_group_effort_controller`) for effort-based control, which Champ sends commands to.
*   **Gait**: Gait parameters in `config/gait/gait.yaml` have been tuned for the smaller Dogzilla form factor (nominal height: 0.10m).

## Troubleshooting

*   **Robot not moving**: Ensure `gz_ros2_control` is installed and the controllers are successfully loaded. Check the terminal output for `spawner` successes.
*   **Missing meshes**: Ensure the `dogzilla_description` package is built and sourced correctly so `package://` URIs resolve.
