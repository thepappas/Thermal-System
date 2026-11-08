import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "mqtt_simulator.py"
spec = importlib.util.spec_from_file_location("mqtt_simulator", path)
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)


class Socket:
    def __init__(self):
        self.sent = []
        self.reply = [b"\x20", b"\x02\x00\x00"]

    def sendall(self, value):
        self.sent.append(value)

    def recv(self, _size):
        return self.reply.pop(0)


class SimulatorTest(unittest.TestCase):
    def test_packet_length(self):
        self.assertEqual(simulator.packet(0x30, b"x" * 128)[:3], b"\x30\x80\x01")

    def test_connect_and_publish(self):
        sock = Socket()
        simulator.connect(sock, "user", "password")
        simulator.publish(sock, "hvac/core/temp", 20.5)
        self.assertTrue(sock.sent[0].startswith(b"\x10"))
        self.assertTrue(sock.sent[1].endswith(b"20.5"))
        self.assertEqual(sock.sent[1][0], 0x30)

    def test_password_needs_username(self):
        with self.assertRaises(ValueError):
            simulator.connect(Socket(), "", "password")


if __name__ == "__main__":
    unittest.main()
