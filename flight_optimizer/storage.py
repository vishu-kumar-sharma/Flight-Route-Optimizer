from __future__ import annotations

import json
from pathlib import Path

from .models import Booking, FlightRoute


def load_routes(path: Path) -> list[FlightRoute]:
    routes: list[FlightRoute] = []
    if not path.exists():
        return routes

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        src, dest, distance, time, fare, flight_num = parts[:6]
        try:
            routes.append(
                FlightRoute(
                    src=src,
                    dest=dest,
                    distance=int(distance),
                    time=int(time),
                    fare=int(fare),
                    flight_num=flight_num,
                )
            )
        except ValueError:
            continue
    return routes


def save_routes(path: Path, routes: list[FlightRoute]) -> None:
    text = "\n".join(route.to_file_line() for route in routes)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def load_bookings(path: Path) -> list[Booking]:
    bookings: list[Booking] = []
    if not path.exists():
        return bookings

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            continue
        try:
            bookings.append(
                Booking(
                    booking_id=int(parts[0]),
                    passenger=parts[1],
                    route=parts[2],
                    fare=int(parts[3]),
                    seat=parts[4],
                )
            )
        except ValueError:
            continue
    return sorted(bookings, key=lambda booking: booking.booking_id)


def save_bookings(path: Path, bookings: list[Booking]) -> None:
    ordered = sorted(bookings, key=lambda booking: booking.booking_id)
    text = "\n".join(booking.to_file_line() for booking in ordered)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def next_booking_id(bookings: list[Booking]) -> int:
    if not bookings:
        return 1000
    return max(booking.booking_id for booking in bookings) + 1


def make_seat(booking_id: int) -> str:
    seat_letter = chr(ord("A") + (booking_id % 6))
    seat_num = 1 + (booking_id % 30)
    return f"{seat_num}{seat_letter}"


def load_custom_coords(path: Path) -> dict[str, tuple[float, float]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    coords: dict[str, tuple[float, float]] = {}
    for city, value in raw.items():
        if (
            isinstance(city, str)
            and isinstance(value, list)
            and len(value) == 2
            and all(isinstance(item, (int, float)) for item in value)
        ):
            coords[city.strip().lower()] = (float(value[0]), float(value[1]))
    return coords


def save_custom_coords(path: Path, coords: dict[str, tuple[float, float]]) -> None:
    serializable = {
        city: [round(lat, 6), round(lon, 6)]
        for city, (lat, lon) in sorted(coords.items())
    }
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

