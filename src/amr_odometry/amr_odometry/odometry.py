#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from tf2_ros import TransformBroadcaster


INT32_MIN = -2147483648
INT32_MAX = 2147483647
INT32_RANGE = 4294967296


def encoder_difference(current_count, previous_count):
    difference = current_count - previous_count

    if difference > INT32_MAX:
        difference -= INT32_RANGE
    elif difference < INT32_MIN:
        difference += INT32_RANGE

    return difference


class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry')

        self.declare_parameter('encoder_cpr', 1320.0)
        self.declare_parameter('wheel_radius', 0.0325)
        self.declare_parameter('wheel_base', 0.215)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.encoder_cpr = float(self.get_parameter('encoder_cpr').value)
        self.wheel_radius = float(self.get_parameter('wheel_radius').value)
        self.wheel_base = float(self.get_parameter('wheel_base').value)
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        if self.encoder_cpr <= 0 or self.wheel_radius <= 0 or self.wheel_base <= 0:
            raise ValueError('Robot dimensions and encoder CPR must be positive')

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_left_count = None
        self.last_right_count = None
        self.last_time = None

        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.encoder_sub = self.create_subscription(
            Int32MultiArray, 'serial/encoder', self.encoder_callback, 10)

    def encoder_callback(self, msg):
        if len(msg.data) != 2:
            self.get_logger().warning('Encoder message must contain two values')
            return

        now = self.get_clock().now()
        left_count = int(msg.data[0])
        right_count = int(msg.data[1])

        if self.last_time is None:
            self.last_left_count = left_count
            self.last_right_count = right_count
            self.last_time = now
            return

        dt = (now - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        left_ticks = encoder_difference(left_count, self.last_left_count)
        right_ticks = encoder_difference(right_count, self.last_right_count)

        self.last_left_count = left_count
        self.last_right_count = right_count
        self.last_time = now

        meters_per_tick = 2.0 * math.pi * self.wheel_radius / self.encoder_cpr
        left_distance = left_ticks * meters_per_tick
        right_distance = right_ticks * meters_per_tick
        center_distance = (left_distance + right_distance) / 2.0
        delta_yaw = (right_distance - left_distance) / self.wheel_base

        middle_yaw = self.yaw + delta_yaw / 2.0
        self.x += center_distance * math.cos(middle_yaw)
        self.y += center_distance * math.sin(middle_yaw)
        self.yaw += delta_yaw

        half_yaw = self.yaw / 2.0
        quaternion_z = math.sin(half_yaw)
        quaternion_w = math.cos(half_yaw)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = quaternion_z
        odom.pose.pose.orientation.w = quaternion_w
        odom.twist.twist.linear.x = center_distance / dt
        odom.twist.twist.angular.z = delta_yaw / dt
        self.odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header = odom.header
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation = odom.pose.pose.orientation
        self.tf_broadcaster.sendTransform(transform)


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
