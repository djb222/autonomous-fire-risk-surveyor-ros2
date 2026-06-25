# Autonomous Fire-Risk Surveyor — ROS2 Perception Pipeline

## Overview

This repository presents the perception and object-mapping component of a university robotics project involving an autonomous fire-risk surveyor.

The project simulated a UAV/UGV system where a drone could observe possible fire-risk hotspots and a ground robot could respond to mapped detections. My contribution focused on the perception pipeline: detecting hotspot-like objects from camera data, using depth information to estimate their 3D position, and publishing mapped detections for use by the wider robotic system.

## My Contribution

This was a group university project. My main contribution focused on the perception and object-mapping side of the system.

I contributed to:

- Developing the object-mapping logic for detected hotspots.
- Processing camera image data using OpenCV.
- Using HSV thresholding and contour detection to identify hotspot regions.
- Reading 3D position data from an organized depth point cloud.
- Transforming detected hotspot coordinates from the camera frame into `map` or `odom` using TF2.
- Publishing detected object positions and RViz markers.
- Testing and debugging ROS2 topics, transforms, camera feeds, and depth data.

## Technologies Used

- ROS2
- Python
- OpenCV
- TF2
- RViz
- Gazebo / Ignition simulation
- Camera and depth point cloud data
- UAV/UGV robotics simulation

## Key Files

```text
auto_frs_perception/
├── auto_frs_perception/
│   ├── object_mapper.py       # Main perception-to-map pipeline
│   ├── hotspot_detector.py    # Camera-based hotspot detection experiment
│   ├── rgbd_probe.py          # RGB-D point cloud probing/debugging
│   └── test_sub.py            # ROS2 subscription test node
├── models/                    # Model/test assets used during perception development
├── package.xml
└── setup.py

random_hotspots.py             # Generates random simulated hotspots in the world file
hotspot_cooldown.py            # Removes hotspots when the ground robot reaches them
gui.py                         # Simple GUI for launching/generating hotspot scenarios
