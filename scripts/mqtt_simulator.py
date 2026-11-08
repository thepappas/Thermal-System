#!/usr/bin/env python3
"""Publish clearly marked synthetic temperatures to a test MQTT broker."""

import argparse
import math
import os
import socket
import struct
import time


def mqtt_string(value):
    encoded = value.encode("utf-8")
    if len(encoded) > 65535:
        raise ValueError("MQTT string too long")
    return struct.pack("!H", len(encoded)) + encoded


def packet(kind, body):
    length = len(body)
    if length > 268435455:
        raise ValueError("MQTT packet too long")
    encoded = bytearray()
    while True:
        digit = length % 128
        length //= 128
        encoded.append(digit | (128 if length else 0))
        if not length:
            break
    return bytes([kind]) + bytes(encoded) + body


def connect(sock, username, password):
    if password and not username:
        raise ValueError("MQTT username required with password")
    flags = 2 | (128 if username else 0) | (64 if password else 0)
    body = mqtt_string("MQTT") + bytes([4, flags]) + struct.pack("!H", 60)
    body += mqtt_string("thermal-simulator")
    if username:
        body += mqtt_string(username)
    if password:
        body += mqtt_string(password)
    sock.sendall(packet(0x10, body))
    response = bytearray()
    while len(response) < 4:
        part = sock.recv(4 - len(response))
        if not part:
            raise ConnectionError("Broker closed before CONNACK")
        response.extend(part)
    if response != b"\x20\x02\x00\x00":
        raise ConnectionError("Broker rejected MQTT connection")


def publish(sock, topic, value):
    sock.sendall(packet(0x30, mqtt_string(topic) + str(value).encode("ascii")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--count", type=int, default=0, help="0 runs until interrupted")
    args = parser.parse_args()
    if not 0 < args.interval <= 30 or args.count < 0:
        parser.error("interval must be between 0 and 30 seconds; count must be nonnegative")
    print("WARNING: synthetic data uses production topics; use only an isolated test broker.", flush=True)
    with socket.create_connection((args.host, args.port), timeout=10) as sock:
        connect(sock, os.getenv("MQTT_USER", ""), os.getenv("MQTT_PASSWORD", ""))
        start = time.monotonic()
        count = 0
        try:
            while not args.count or count < args.count:
                wave = math.sin((time.monotonic() - start) / 300)
                readings = {
                    "hvac/outdoor/temp": 12 + 4 * wave,
                    "hvac/roof/temp_in": 14 + 4 * wave,
                    "hvac/roof/temp_out": 24 + 6 * wave,
                    "hvac/house/temp_return": 20,
                    "hvac/house/temp_supply": 21,
                    "hvac/mass/temp_in": 22,
                    "hvac/mass/temp_out": 21,
                    "hvac/core/temp": 19,
                }
                for topic, value in readings.items():
                    publish(sock, topic, round(value, 2))
                count += 1
                if not args.count or count < args.count:
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        finally:
            sock.sendall(packet(0xE0, b""))


if __name__ == "__main__":
    main()
