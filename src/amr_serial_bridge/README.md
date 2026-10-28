# AMR serial bridge

This ROS 2 node connects `/cmd_vel` to STM32 USART1 at 115200 baud. It sends `ARM\n` before the first velocity command, sends `CMD,v,w\n` every 50 ms while `/cmd_vel` is fresh, and publishes STM32 `ENC,left,right\n` frames on `/serial/encoder` as `std_msgs/Int32MultiArray`.

When `/cmd_vel` is older than `cmd_timeout` (default 500 ms), the node sends `DISARM\n`. If the link or node fails, the STM32 watchdog stops the motors after 500 ms without a valid command. The bridge reconnects to the serial port every two seconds after a connection failure.

Run with:

```bash
colcon build --packages-select amr_serial_bridge --symlink-install
source install/setup.bash
ros2 launch amr_serial_bridge serial_bridge.launch.py
```

Test with the wheels raised clear of the floor:

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.03}, angular: {z: 0.0}}"
```

Stop the publisher with Ctrl+C. Observe `/serial/encoder` for cumulative counts from the two wheels.
