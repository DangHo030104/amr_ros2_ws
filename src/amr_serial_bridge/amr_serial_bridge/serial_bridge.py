#!/usr/bin/env python3

import math
import time
import serial   # Package PySerial để RPi4 giao tiếp với STM32 qua UART

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray

from serial_protocol import encode_command, parse_frame


class SerialBridge(Node):
    def __init__(self):
        super().__init__('serial_bridge')

        # Khai báo ROS2 Parametes: Cac tham so co the thay doi trong file YAML.
        self.declare_parameter('port', '/dev/serial0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('max_linear', 0.10)
        self.declare_parameter('max_angular', 0.50)
        self.declare_parameter('cmd_timeout', 0.5)
        self.declare_parameter('update_period', 0.05)

        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.max_linear = self.get_parameter('max_linear').value
        self.max_angular = self.get_parameter('max_angular').value
        self.cmd_timeout = self.get_parameter('cmd_timeout').value
        self.update_period = self.get_parameter('update_period').value

        # raise ValueError(...): Python phát sinh ngoại lệ và dừng quá trình khởi tạo Node.
        if self.update_period <= 0 or self.cmd_timeout <= 0:
            raise ValueError('Timeout and update period must be positive')
        if self.max_linear <= 0 or self.max_angular <= 0:
            raise ValueError('Speed limits must be positive')

        # Khởi tạo các biến quản lý trạng thái
        self.serial_conn = None             # Object kết nối UART
        self.last_connect_attempt = 0.0     # Tg thử kết nối UART gần nhất
        self.rx_buffer = bytearray()
        self.discard_rx_line = False        # Cờ đánh dấu dòng UART cần loại bỏ
        self.last_cmd_time = None
        self.command_v = 0.0
        self.command_w = 0.0
        self.armed = False                  # Status ARM do Pi tự quản lý
        self.stop_sent = True               

        self.encoder_pub = self.create_publisher(Int32MultiArray, 'serial/encoder', 10)
        self.cmd_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        self.open_serial()
        self.timer = self.create_timer(self.update_period, self.timer_callback) 

    # Kết nối UART với STM32
    def open_serial(self):
        self.last_connect_attempt = time.monotonic()
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0,
                write_timeout=0.1,
            )

            self.rx_buffer.clear()
            self.discard_rx_line = False
            self.armed = False
            self.stop_sent = True
            self.last_cmd_time = None   # Xóa thời điểm nhận lệnh vận tốc gần nhất.

            self.get_logger().info(f'Serial connected: {self.port}, {self.baudrate} baud')

        except (OSError, ValueError) as exc:
            self.serial_conn = None
            self.get_logger().error(f'Serial open failed: {exc}')

    # Đóng kết nối UART 
    def close_serial(self, send_disarm=False):
        connection = self.serial_conn   # Lưu kết nối UART hiện tại để đóng sau khi gửi lệnh DISARM
        self.serial_conn = None       

        if connection is not None:
            try:
                if send_disarm:
                    connection.write(b'DISARM\n')       # Gửi lệnh DISARM để STM32 dừng động cơ
            except (OSError, ValueError):
                pass
            finally:
                try:
                    connection.close()
                except OSError:
                    pass

        self.rx_buffer.clear()
        self.discard_rx_line = False
        self.armed = False
        self.stop_sent = True

    # Nhận vận tốc ROS2 từ topic /cmd_vel 
    def cmd_vel_callback(self, msg):
        v = float(msg.linear.x)
        w = float(msg.angular.z)

        if (not math.isfinite(v) or not math.isfinite(w) or abs(v) > self.max_linear or abs(w) > self.max_angular):
            self.last_cmd_time = None
            self.get_logger().warning('Rejected invalid /cmd_vel')
            return

        self.command_v = v
        self.command_w = w
        self.last_cmd_time = time.monotonic()   # Cập nhật thời điểm nhận lệnh vận tốc gần nhất.

    # Ghi dữ liệu dạng byte xuống cổng UART
    def write_payload(self, payload):
        if self.serial_conn is None:
            return False
        try:
            if self.serial_conn.write(payload) != len(payload):
                raise OSError('short serial write')
            return True
        except (OSError, ValueError) as exc:
            self.get_logger().error(f'Serial write error: {exc}')
            self.close_serial()
            return False

    # Đóng gói lệnh vận tốc
    def write_command(self, v, w):
        return self.write_payload(encode_command(v, w))

    # Xử lý dữ liệu encoder
    def process_frame(self, raw):
        frame = parse_frame(raw)
        if frame is None:
            return

        msg = Int32MultiArray()     # Tạo ROS2 message Int32MultiArray để gửi dữ liệu encoder
        msg.data = [frame['left'], frame['right']]
        self.encoder_pub.publish(msg)

    # Đọc dữ liệu từ UART
    def read_serial(self):
        if self.serial_conn is None:
            return

        try:
            # Gioi han du lieu xu ly trong mot chu ky timer.
            for _ in range(4):  # 4 * 0.05s = 0.2s max per timer callback
                waiting = self.serial_conn.in_waiting       # Kiểm tra số byte đang chờ
                if waiting <= 0:
                    break

                # Đọc dữ liệu theo từng đoạn và chọn min 
                chunk = self.serial_conn.read(min(waiting, 256))    # Mỗi lần đọc tối đa 256 byte.
                if not chunk:
                    break

                # Duyệt từng byte. Vd: b'ENC,1250,1245\n' -> [69, 78, 67, 44, 49, 50, 53, 48, 44, 49, 50, 52, 53, 10]
                for byte in chunk:
                    if byte == 10:  # newline (\n)
                        if not self.discard_rx_line:
                            self.process_frame(bytes(self.rx_buffer).rstrip(b'\r'))
                        self.rx_buffer.clear()
                        self.discard_rx_line = False
                    elif not self.discard_rx_line:
                        # Cơ chế chống dữ liệu quá dài
                        if len(self.rx_buffer) < 64:
                            self.rx_buffer.append(byte)
                        else:
                            self.rx_buffer.clear()
                            self.discard_rx_line = True

        except (OSError, ValueError) as exc:
            self.get_logger().error(f'Serial read error: {exc}')
            self.close_serial()

    # Điều khiển chu kỳ gửi giữa các lệnh
    def timer_callback(self):
        now = time.monotonic()

        # Kiểm tra kết nối UART
        if self.serial_conn is None:
            if now - self.last_connect_attempt >= 2.0:
                self.open_serial()
            return

        # Nếu UART đang kết nối, Timer ưu tiên đọc dữ liệu nhận
        self.read_serial()

        # Kiểm tra lại kết nối
        if self.serial_conn is None:
            return

        # Kiểm tra lệnh vận tốc còn hiệu lực
        fresh = (self.last_cmd_time is not None and now - self.last_cmd_time <= self.cmd_timeout)
        if fresh:
            if not self.armed:
                self.armed = self.write_payload(b'ARM\n')
            if not self.armed:
                return
            if self.write_command(self.command_v, self.command_w):
                self.stop_sent = False
        elif not self.stop_sent:
            if self.write_payload(b'DISARM\n'):
                self.armed = False
                self.stop_sent = True

    # Hủy node ROS2
    def destroy_node(self):
        self.close_serial(send_disarm=True)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)   # Khởi tạo args ROS 2 cho chương trình Python.
    node = None
    try:
        node = SerialBridge()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


# Chương trình main() sẽ được chạy khi file này được chạy trực tiếp
# Nếu file được import làm module vào chương trình Python khác, main() sẽ không được gọi
if __name__ == '__main__':
    main()
