# Ctrl-P 2.0: Python Control Interface
The top-level control interface for controlling a Ctrl-P pressure control system.

## Dependencies
All dependencies are managed in the reqirements file.
`pip install -r requirements.txt`

## Usage
[Instructions in the documentation](https://ctrl-p.cbteeple.com/latest/top-level)

## About Ctrl-P
The Ctrl-P project is a full-stack pneumatic control system featuring smooth control of pressure at a high bandwidth.

Ctrl-P has three parts:
- [Arduino-Based Firmware](https://github.com/cbteeple/pressure_controller): Contains the low-level control
- [Python Control Interface](https://github.com/cbteeple/pressure_control_interface): Controls pressure via serial comms
- [ROS Driver](https://github.com/cbteeple/pressure_control_cbt): Controls pressure via serial or RawUSB

Related Packages:
- [Pressure Controller Skills](https://github.com/cbteeple/pressure_controller_skills): Build complex parametric skills using straightforward definition files.
- [Visual Servoing](https://github.com/cbteeple/ihm_servoing): Example of setting up a realtime feedback controller.
