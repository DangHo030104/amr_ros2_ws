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

    return None

# RPi 4 -> STM32
def encode_command(v, w):

    if not math.isfinite(v) or not math.isfinite(w):
        raise ValueError("Invalid velocity")

    return f"CMD,{v:.4f},{w:.4f}\n".encode("ascii")     # Chuyển chuỗi thành bytes
