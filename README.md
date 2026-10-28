# AMR ROS 2 workspace

Workspace này dùng ROS 2 Humble để nối Raspberry Pi 4 với bộ điều khiển động cơ
STM32. Các thông số cơ khí đang dùng chung với firmware:

- Bán kính bánh xe: `0.0325 m`
- Khoảng cách hai bánh: `0.215 m`
- Encoder: `1320 CPR`
- Giới hạn vận tốc: `0.10 m/s` và `0.50 rad/s`

## Luồng dữ liệu

`/cmd_vel` -> serial bridge -> STM32 -> motor

`STM32 encoder` -> `/serial/encoder` -> odometry -> `/odom` và TF
`odom -> base_link`

LiDAR xuất `/scan`. `robot_state_publisher` xuất TF cố định
`base_link -> laser_frame`. SLAM Toolbox tạo TF `map -> odom`.

## Build trên Raspberry Pi

```bash
cd ~/amr_ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Khởi động phần cứng, encoder, odometry và TF:

```bash
ros2 launch amr_bringup bringup.launch.py
```

Tạo bản đồ:

```bash
ros2 launch amr_slam slam.launch.py
```

Chạy Nav2 với bản đồ đã lưu:

```bash
ros2 launch amr_navigation navigation.launch.py map:=/duong/dan/map.yaml
```

LiDAR được cấu hình cho RPLIDAR A1M8 ở `115200 baud`, chế độ quét `Standard`,
cổng mặc định `/dev/ttyUSB0`. Trước khi chạy robot trên sàn, cần đo lại kích
thước khung và vị trí thật của LiDAR.

Có thể đổi cổng khi chạy riêng LiDAR:

```bash
ros2 launch amr_lidar lidar.launch.py port:=/dev/ttyUSB1
```
