#!/usr/bin/env python3
"""Motor controller wrapper for the TurboPi Advanced kit."""

import os
import sys
import threading
import time


sys.path.insert(0, os.path.expanduser("~/board_demo"))
import ros_robot_controller_sdk as rrc


def mecanum_ik(vx: float, vy: float, omega: float) -> list[list]:
    """Convert body velocities to wheel duties."""
    v1 = vx - vy - omega
    v2 = vx + vy + omega
    v3 = vx + vy - omega
    v4 = vx - vy + omega

    return [[1, -v1], [2, v2], [3, -v3], [4, v4]]


class MotorController:
    """Thread-safe motor controller with duty clamping and watchdog support."""

    def __init__(self, max_duty: float = 80.0):
        self.board = rrc.Board()
        self.board.enable_reception()
        self.max_duty = max_duty
        self._lock = threading.Lock()
        self._last_command_time = time.monotonic()

        time.sleep(0.2)
        self.center_servos()

    def _clamp(self, value: float) -> float:
        """Clamp duty cycle to the configured safe range."""
        return max(-self.max_duty, min(self.max_duty, value))

    def set_velocity(self, vx: float, vy: float, omega: float) -> list[list]:
        """Send a body velocity command through mecanum inverse kinematics."""
        wheels = mecanum_ik(vx, vy, omega)
        for wheel in wheels:
            wheel[1] = self._clamp(wheel[1])

        with self._lock:
            self.board.set_motor_duty(wheels)
            self._last_command_time = time.monotonic()

        return wheels

    def set_raw_wheels(self, wheels: list[list]) -> None:
        """Send raw wheel duties directly."""
        for wheel in wheels:
            wheel[1] = self._clamp(wheel[1])

        with self._lock:
            self.board.set_motor_duty(wheels)
            self._last_command_time = time.monotonic()

    def stop(self) -> None:
        """Stop all motors immediately and refresh the watchdog timestamp."""
        with self._lock:
            self.board.set_motor_duty([[1, 0], [2, 0], [3, 0], [4, 0]])
            self._last_command_time = time.monotonic()

    def center_servos(self) -> None:
        """Center the camera pan-tilt servos."""
        with self._lock:
            self.board.pwm_servo_set_position(0.5, [[1, 1500], [2, 1500]])

    def set_servos(self, positions: list[list]) -> None:
        """Set servo positions."""
        with self._lock:
            self.board.pwm_servo_set_position(0.3, positions)

    def get_battery_mv(self) -> int | None:
        """Read battery voltage in millivolts."""
        try:
            return self.board.get_battery()
        except Exception:
            return None

    def get_imu(self) -> tuple | None:
        """Read IMU data if available."""
        try:
            return self.board.get_imu()
        except Exception:
            return None

    def beep(
        self,
        freq: int = 1900,
        on_time: float = 0.1,
        off_time: float = 0.0,
        repeat: int = 1,
    ) -> None:
        """Play a buzzer tone."""
        with self._lock:
            self.board.set_buzzer(freq, on_time, off_time, repeat)

    def set_rgb(self, colors: list[list]) -> None:
        """Set RGB LEDs."""
        with self._lock:
            self.board.set_rgb(colors)

    @property
    def seconds_since_last_command(self) -> float:
        """Return the time since the last motor command."""
        return time.monotonic() - self._last_command_time
