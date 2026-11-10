#!/usr/bin/env python3

import math

import rclpy
from nav_msgs.msg import Odometry                   # msg chứa vị trí, hướng và vận tốc robot trong hệ tọa độ odom
from rclpy.node import Node
from sensor_msgs.msg import JointState              # msg chứa thông tin góc quay của các joint (bánh xe) để robot_state_publisher cập nhật TF
from std_msgs.msg import Int32MultiArray

 
INT32_MIN = -2147483648
INT32_MAX = 2147483647
INT32_RANGE = 4294967296


# Tính số xung encoder giữa hai lần nhận
def encoder_difference(current_count, previous_count):
    delta = current_count - previous_count

    # Xử lý tràn số 32-bit
    if delta > INT32_MAX:
        delta -= INT32_RANGE
    elif delta < INT32_MIN:
        delta += INT32_RANGE

    return delta


class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry')

        self.declare_parameter('encoder_cpr', 1320.0)
        self.declare_parameter('wheel_radius', 0.0325)
        self.declare_parameter('wheel_base', 0.215)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('odom_topic', 'wheel/odom')
        self.declare_parameter('linear_velocity_variance', 0.04)
        self.declare_parameter('angular_velocity_variance', 0.64)

        self.encoder_cpr = float(self.get_parameter('encoder_cpr').value)
        self.wheel_radius = float(self.get_parameter('wheel_radius').value)
        self.wheel_base = float(self.get_parameter('wheel_base').value)
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.linear_velocity_variance = float(self.get_parameter('linear_velocity_variance').value)
        self.angular_velocity_variance = float(self.get_parameter('angular_velocity_variance').value)

        if self.encoder_cpr <= 0 or self.wheel_radius <= 0 or self.wheel_base <= 0:
            raise ValueError('Robot dimensions and encoder CPR must be positive')
        if not isinstance(self.odom_topic, str) or not self.odom_topic:
            raise ValueError('Odometry topic must not be empty')
        if self.linear_velocity_variance <= 0 or self.angular_velocity_variance <= 0:
            raise ValueError('Odometry variances must be positive')

        # Khởi tạo trạng thái của robot
        self.x = 0.0
        self.y = 0.0
        self.thelta = 0.0                  

        # Lưu số xung và thời điểm nhận dữ liệu trước đó
        self.last_left_count = None
        self.last_right_count = None
        self.last_time = None

        # Góc quay tích lũy của hai bánh (radian)
        self.left_wheel_position = 0.0
        self.right_wheel_position = 0.0

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.joint_state_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.encoder_sub = self.create_subscription(Int32MultiArray, 'serial/encoder', self.encoder_callback, 10)

    # Gửi góc quay hai bánh để robot_state_publisher cập nhật TF của bánh xe
    def publish_joint_states(self, stamp):
        joint_state = JointState()
        joint_state.header.stamp = stamp.to_msg()
        joint_state.name = ['left_wheel_joint', 'right_wheel_joint']                    # Tên joint khớp với Xacro
        joint_state.position = [self.left_wheel_position, self.right_wheel_position]
        self.joint_state_pub.publish(joint_state)

    def encoder_callback(self, msg):
        if len(msg.data) != 2:
            self.get_logger().warning('Encoder message must contain two values')
            return

        now = self.get_clock().now()    # Lấy tg hiện tại theo clock của Node ROS 2
        left_count = int(msg.data[0])
        right_count = int(msg.data[1])

        # Lần đầu nhận dữ liệu encoder
        if self.last_time is None:
            self.last_left_count = left_count
            self.last_right_count = right_count
            self.last_time = now
            self.publish_joint_states(now)
            return

        dt = (now - self.last_time).nanoseconds / 1e9   # Đổi ns sang s
        if dt <= 0.0:
            return

        # Tính số xung encoder giữa 2 lần nhận
        delta_left = encoder_difference(left_count, self.last_left_count)
        delta_right = encoder_difference(right_count, self.last_right_count)
   
        self.last_left_count = left_count
        self.last_right_count = right_count
        self.last_time = now

        # Chuyển số xung encoder thành quãng đường 
        meters_per_tick = 2.0 * math.pi * self.wheel_radius / self.encoder_cpr  

        # Cập nhật góc quay của bánh xe từ số xung encoder
        radians_per_tick = 2.0 * math.pi / self.encoder_cpr
        self.left_wheel_position += delta_left * radians_per_tick
        self.right_wheel_position += delta_right * radians_per_tick
        self.publish_joint_states(now)

        # Tính toán odometry của robot 2 bánh (Differential drive)
        # 1. Tính quãng đường đi được của mỗi bánh xe 
        ds_left = delta_left * meters_per_tick
        ds_right = delta_right * meters_per_tick

        # 2. Tính quãng đường đi được trung bình và góc quay của robot
        ds = (ds_left + ds_right) / 2.0
        dtheta = (ds_right - ds_left) / self.wheel_base

        # 3. Cập nhật vị trí và hướng của robot (x,y,theta)
        theta_mid = self.thelta + dtheta / 2.0

        self.x += ds * math.cos(theta_mid)          # Tích phân rời rạc
        self.y += ds * math.sin(theta_mid)
        
        self.thelta += dtheta

        # Chuyển góc θ sang Quaternion
        # Vì robot đang di chuyển trong MP 2D, chỉ xét góc quay quanh trục Z (yaw)
        q_z = math.sin(self.thelta / 2.0)
        q_w = math.cos(self.thelta / 2.0)

        # Cập nhật thông tin header và frame_id
        odom = Odometry()                           
        odom.header.stamp = now.to_msg()            # Thời điểm tính odometry
        odom.header.frame_id = self.odom_frame      # Hệ toạ độ gốc của robot dùng để tham chiếu
        odom.child_frame_id = self.base_frame       # Hệ toạ độ gắn với thân robot (đặt tại tâm robot)

        # Gán vị trí, hướng và vận tốc vào msg Odometry
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y

        odom.pose.pose.orientation.z = q_z
        odom.pose.pose.orientation.w = q_w

        odom.twist.twist.linear.x = ds / dt
        odom.twist.twist.angular.z = dtheta / dt
        odom.twist.covariance[0] = self.linear_velocity_variance        # Độ tin cậy vx
        odom.twist.covariance[35] = self.angular_velocity_variance      # Độ tin cậy vyaw

        self.odom_pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
