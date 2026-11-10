#!/usr/bin/env python3

import math


# STM32 -> RPi4
def parse_frame(raw):

    try:
        line = raw.decode("ascii").strip()  # Chuyển bytes thành chuỗi 
    except (UnicodeDecodeError, AttributeError):
        return None

    if not line or len(line) > 128:
        return None

    # parts = ["ENC", "1250", "1245"]
    parts = line.split(",")

    if parts[0] == "ENC" and len(parts) == 3:
        try:
            left = int(parts[1])
            right = int(parts[2])
        except ValueError:
            return None

        # Encoder counters are signed 32-bit integers.
        if not all(
            -(2**31) <= value <= 2**31 - 1
            for value in (left, right)):
            return None

        return {
            "type": "ENC",
            "left": left,
            "right": right
        }

    # parts = ["IMU", "Timestamp", "a_x", "a_y", "a_z", "g_x", "g_y", "g_z"]
    if parts[0] == "IMU" and len(parts) == 8:
        try:
            time_ms = int(parts[1])
            # values=[a_x, a_y, a_z, g_x, g_y, g_z]
            values = [int(value) for value in parts[2:]]
        except ValueError:
            return None

        if not 0 <= time_ms <= 2**32 - 1:
            return None
        if not all(-(2**15) <= value <= 2**15 - 1 for value in values):
            return None

        return {
            "type": "IMU",
            "time_ms": time_ms,
            "accel": values[:3],
            "gyro": values[3:]
        }

    return None

# RPi 4 -> STM32
def encode_command(v, w):

    if not math.isfinite(v) or not math.isfinite(w):
        raise ValueError("Invalid velocity")

    return f"CMD,{v:.4f},{w:.4f}\n".encode("ascii")     # Chuyển chuỗi thành bytes
