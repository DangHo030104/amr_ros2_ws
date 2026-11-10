# AMR ROS 2 workspace

Workspace này dùng ROS 2 Humble để nối Raspberry Pi 4 với bộ điều khiển động cơ
STM32. Các thông số cơ khí đang dùng chung với firmware:

- Bán kính bánh xe: `0.0325 m`
- Khoảng cách hai bánh: `0.215 m`
- Encoder: `1320 CPR`
- Giới hạn đang cấu hình trong serial bridge và Nav2: `0.20 m/s` và `0.80 rad/s`.
  Hãy xác nhận các giới hạn này khớp với firmware STM32 trước khi cho robot chạy.

## Luồng dữ liệu

`/cmd_vel` -> serial bridge -> STM32 -> motor

`STM32 encoder` -> `/serial/encoder` -> wheel odometry -> `/wheel/odom`

`STM32 MPU6050` -> `/imu/data_raw`

`/wheel/odom` + gyro Z từ `/imu/data_raw` -> EKF -> `/odom` và TF `odom -> base_link`

LiDAR xuất `/scan`. `robot_state_publisher` xuất TF cố định
`base_link -> laser`. SLAM Toolbox tạo TF `map -> odom`.

## Build trên Raspberry Pi

```bash
cd ~/amr_ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Chạy SLAM rồi Nav2

Trước khi chạy, xác nhận LiDAR và cổng UART của STM32 đang nối đúng. Các cổng
mặc định lần lượt là `/dev/ttyUSB0` và `/dev/serial0`; cấu hình nằm trong
`src/amr_lidar/config/lidar.yaml` và `src/amr_serial_bridge/config/serial_bridge.yaml`.
Đặt robot ở khu vực thử nghiệm an toàn, có thể dừng khẩn cấp. Không chạy SLAM
và Nav2 cùng lúc: cả hai có thể phát TF `map -> odom`.

### 1. Build workspace

Chạy một lần sau khi lấy workspace hoặc khi có thay đổi mã nguồn:

```bash
cd ~/amr_ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

Mỗi terminal mới bên dưới cần nạp môi trường:

```bash
source /opt/ros/humble/setup.bash
source ~/amr_ros2_ws/install/setup.bash
```

### 2. Khởi động phần cứng

Trong **Terminal 1**, nạp môi trường rồi chạy:

```bash
ros2 launch amr_bringup bringup.launch.py
```

Giữ terminal này chạy. Launch này khởi động robot description, serial bridge,
odometry và LiDAR. Mở terminal khác và kiểm tra có dữ liệu `/scan` và `/odom`
trước khi tiếp tục:

```bash
ros2 topic echo /scan --once
ros2 topic echo /odom --once
```

### 3. Dựng và lưu bản đồ bằng SLAM

Trong **Terminal 2**, nạp môi trường rồi chạy:

```bash
ros2 launch amr_slam slam.launch.py
```

Dùng phương thức điều khiển robot hiện có để di chuyển chậm, quét đủ khu vực
cần lập bản đồ và theo dõi bản đồ trong RViz. Khi bản đồ đã ổn định, mở
**Terminal 3**, nạp môi trường và lưu bản đồ:

```bash
mkdir -p ~/amr_maps
ros2 run nav2_map_server map_saver_cli -f ~/amr_maps/lab
```

Lệnh tạo `~/amr_maps/lab.yaml` và `~/amr_maps/lab.pgm`. Sau khi lưu xong, quay
lại Terminal 2 và nhấn `Ctrl+C` để dừng SLAM. **Giữ Terminal 1 chạy**.

### 4. Chuẩn bị trước khi chạy Nav2

Nav2 dùng bản đồ đã lưu và AMCL để định vị nên phải dừng SLAM trước. Tại terminal
đang chạy SLAM, nhấn `Ctrl+C`. Không dùng `Ctrl+Z` vì lệnh này chỉ tạm dừng tiến
trình và có thể để lại các node ROS 2 đang chiếm tài nguyên. Nếu đã dùng
`Ctrl+Z`, chạy `jobs`, đưa tiến trình trở lại bằng `fg`, sau đó nhấn `Ctrl+C`.

Giữ `amr_bringup` ở Terminal 1 tiếp tục chạy. Kiểm tra hai file bản đồ tồn tại:

```bash
ls -l ~/amr_maps/lab.yaml
ls -l ~/amr_maps/lab.pgm
```

Nếu dùng bản đồ nằm trong workspace:

```bash
ls -l ~/amr_ros2_ws/src/amr_navigation/maps/map01.yaml
ls -l ~/amr_ros2_ws/src/amr_navigation/maps/map01.pgm
```

Trước khi khởi động Nav2, kiểm tra các dữ liệu đầu vào quan trọng:

```bash
ros2 topic hz /scan
ros2 topic hz /imu/data_raw
ros2 topic hz /wheel/odom
ros2 topic hz /odom
ros2 topic echo /serial/encoder
ros2 topic echo /joint_states
ros2 run tf2_ros tf2_echo odom base_link
```

Các lệnh theo dõi liên tục có thể dừng bằng `Ctrl+C`. Chỉ tiếp tục khi LiDAR,
encoder, odometry và TF `odom -> base_link` đều hoạt động.

### 5. Khởi động Nav2

Trong **Terminal 2**, nạp môi trường rồi chạy với bản đồ vừa lưu:

```bash
source /opt/ros/humble/setup.bash
source ~/amr_ros2_ws/install/setup.bash
ros2 launch amr_navigation navigation.launch.py \
  map:=$HOME/amr_maps/lab.yaml
```

Hoặc dùng bản đồ `map01` trong workspace:

```bash
ros2 launch amr_navigation navigation.launch.py \
  map:=$HOME/amr_ros2_ws/src/amr_navigation/maps/map01.yaml
```

Launch này chạy map server, AMCL, A* planner, DWB controller, behavior server,
BT Navigator và velocity smoother. Nó dùng localization trên bản đồ đã lưu,
không chạy SLAM. Cấu hình hiện tại bật A* bằng `use_astar: true`.

Trong log, các lifecycle node cần chuyển sang trạng thái active. Có thể kiểm tra
từ một terminal khác:

```bash
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
```

Kết quả mong đợi cho mỗi node là `active [3]`.

### 6. Khởi động RViz cho Nav2

Trong **Terminal 3**:

```bash
source /opt/ros/humble/setup.bash
source ~/amr_ros2_ws/install/setup.bash
ros2 launch nav2_bringup rviz_launch.py
```

Trong RViz, đặt **Fixed Frame** là `map`. Xác nhận các display Map, LaserScan,
RobotModel, TF, Global Costmap, Local Costmap và đường đi đã được bật. Nếu chạy
`rviz2` trực tiếp thay vì launch trên thì phải tự thêm các display này.

### 7. Đặt vị trí ban đầu cho AMCL

Khi vừa khởi động, AMCL chưa biết vị trí thực tế của robot trên bản đồ:

1. Chọn **2D Pose Estimate** trong RViz.
2. Nhấn vào đúng vị trí thực tế của robot trên bản đồ.
3. Giữ và kéo chuột theo hướng đầu robot, sau đó thả chuột.
4. Chờ các hạt AMCL tập trung quanh robot và LaserScan khớp tương đối với tường
   trên bản đồ.

Kiểm tra TF do AMCL tạo và pose ước lượng:

```bash
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /amcl_pose
```

Nếu không có TF `map -> odom`, hoặc LaserScan còn lệch nhiều so với bản đồ, hãy
đặt lại **2D Pose Estimate** và chưa gửi mục tiêu cho robot.

### 8. Gửi mục tiêu điều hướng

Đặt robot trên sàn bằng phẳng, dọn vật cản sát robot và chuẩn bị phương án ngắt
nguồn động cơ. Lần thử đầu chỉ nên chọn mục tiêu gần khoảng 0.5 đến 1 m.

Trong RViz, chọn **Nav2 Goal** hoặc **2D Goal Pose**, nhấn vào vùng trống trên
bản đồ rồi kéo mũi tên theo hướng robot cần quay khi tới đích. Nav2 sẽ dùng A*
tạo đường toàn cục, DWB bám đường và velocity smoother xuất lệnh `/cmd_vel` tới
serial bridge.

Theo dõi lệnh vận tốc và kết nối topic:

```bash
ros2 topic echo /cmd_vel
ros2 topic info /cmd_vel -v
```

`/cmd_vel` phải có publisher từ Nav2/velocity smoother và subscriber từ
`serial_bridge`. Có thể kiểm tra action điều hướng bằng:

```bash
ros2 action list | grep navigate
```

Danh sách cần có `/navigate_to_pose`.

### 9. Dừng robot và dấu hiệu chạy đúng

Hủy goal trong RViz để dừng nhiệm vụ. Khi cần dừng Nav2, nhấn `Ctrl+C` tại
Terminal 2. Khi không còn lệnh `/cmd_vel` mới, timeout của serial bridge sẽ gửi
`DISARM` xuống STM32. Nếu robot phản ứng bất thường, ưu tiên ngắt nguồn động cơ
trực tiếp.

Hệ thống Nav2 được xem là hoạt động đúng khi:

- `/scan`, `/imu/data_raw`, `/wheel/odom`, `/odom`, `/serial/encoder` và `/joint_states` có dữ liệu.
- TF `odom -> base_link` tồn tại.
- Sau khi đặt initial pose, TF `map -> odom` tồn tại.
- Map hiển thị và LaserScan khớp tương đối với tường trong RViz.
- Các lifecycle node Nav2 ở trạng thái `active`.
- Sau khi gửi goal, RViz hiển thị đường đi và `/cmd_vel` có dữ liệu.
- Robot di chuyển về mục tiêu và dừng trong giới hạn sai số đã cấu hình.

Nếu một node báo không mở được cổng nối tiếp, dừng launch và kiểm tra lại thiết
bị/cổng trong các file cấu hình nêu trên; không khởi chạy thêm một serial bridge
hoặc LiDAR thứ hai khi bringup đang chạy.

LiDAR được cấu hình cho RPLIDAR A1M8 ở `115200 baud`, chế độ quét `Standard`,
cổng mặc định `/dev/ttyUSB0`. Trước khi chạy robot trên sàn, cần đo lại kích
thước khung và vị trí thật của LiDAR.

Có thể đổi cổng khi chạy riêng LiDAR:

```bash
ros2 launch amr_lidar lidar.launch.py port:=/dev/ttyUSB1
```
