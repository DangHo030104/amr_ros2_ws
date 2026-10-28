# Codex Instructions — ROS 2 Humble Autonomous Robot

## Project context
- Target: ROS 2 Humble on Raspberry Pi 4, Ubuntu Linux.
- Scope: integration of sensors, LiDAR, motor control, odometry, TF, SLAM, navigation, launch and diagnostics.
- Hardware interfaces, installed packages, motor controller, safety circuitry, and topic names are **unknown until inspected**. Never invent them.
- Follow the existing package language: `rclpy` for Python, `rclcpp` for C++.

## Primary rule: Keep it simple
- Make the smallest correct, maintainable change that solves the stated task.
- Preserve existing workspace layout, packages, nodes, topics, frames, launch files, and parameters unless a change is explicitly required.
- Reuse existing ROS 2 packages and APIs; do not reimplement working drivers, SLAM, or Nav2.
- Avoid unnecessary packages, files, abstractions, manager classes, design patterns, threads, callback groups, and dependencies.
- Prefer clear functions, descriptive names, straightforward control flow, and short explanations.
- Do not refactor unrelated working code or add speculative features.
- Simplicity must not compromise safety, correctness, or ROS 2 executor responsiveness.

## ROS 2 conventions
- Inspect `package.xml`, `setup.py`/`setup.cfg` or `CMakeLists.txt`, launch files, parameter YAML, and relevant nodes before editing.
- Respect topic types, QoS compatibility, namespaces, remappings, frame IDs, timestamps, and units.
- Use ROS 2 timers and callbacks appropriately; avoid blocking executor callbacks and busy loops.
- Use ROS logging with throttling where appropriate; do not flood logs at sensor rates.
- Prefer parameters for values already parameterized; do not introduce configuration systems without need.
- Preserve the established TF tree; check `map -> odom -> base_link` ownership and avoid duplicate TF publishers.
- For Nav2 and SLAM, prefer supported configuration and packages over custom navigation algorithms.
- Respect Raspberry Pi 4 CPU, memory, I/O and power constraints; avoid unnecessary high-frequency processing.

## Motion and hardware safety
- Never disable or bypass an existing emergency stop, watchdog, motor enable interlock, or safety limit.
- Never increase speed, acceleration, or motor power limits without explicit approval.
- For motion command paths, verify timeout behavior: stale or missing commands should result in a safe stop through the appropriate control layer.
- Handle missing, stale, NaN, infinite, and out-of-range sensor data as applicable; do not silently treat invalid readings as free space.
- Never issue live motor commands merely to test code without explicit user approval and appropriate physical precautions.
- Prefer simulation, static checks, and non-actuating diagnostics before hardware tests.
- Clearly distinguish successful build/tests from validation on the physical robot.

## Workflow
1. Inspect the relevant workspace files and explain the current data flow before changes.
2. State a minimal plan and the exact files to modify.
3. Ask for clarification when hardware details, interface contracts, or safety-critical assumptions are missing.
4. For architectural or safety-impacting changes, obtain approval before editing.
5. Implement only the requested change, keeping the diff small.
6. Run available focused checks; use `colcon build --packages-select <package>` for affected packages when the ROS environment is configured.
7. Report files changed, reasons, tests performed, test failures, and what remains unverified on real hardware.

## Do not
- Do not rename topics, TF frames, parameters, packages, or GPIO assignments without a demonstrated need and approval.
- Do not add ROS nodes, executors, threads, libraries, or layers for hypothetical future requirements.
- Do not modify generated `build/`, `install/`, or `log/` outputs as source files.
- Do not claim a hardware behavior is verified solely because code compiles.

## Preferred response format
- **Current understanding:** one or two sentences.
- **Minimal change:** affected files and short rationale.
- **Validation:** commands run and actual results.
- **Remaining risks:** only concrete uncertainties, especially safety or hardware dependencies.
