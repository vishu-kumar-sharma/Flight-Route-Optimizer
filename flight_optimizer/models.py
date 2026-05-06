from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlightRoute:
    src: str
    dest: str
    distance: int
    time: int
    fare: int
    flight_num: str

    @property
    def route_key(self) -> tuple[str, str, str]:
        return (self.src, self.dest, self.flight_num)

    @property
    def label(self) -> str:
        return (
            f"{self.src} -> {self.dest} | {self.flight_num} | "
            f"{self.time} min | Rs {self.fare} | {self.distance} km"
        )

    def to_file_line(self) -> str:
        return (
            f"{self.src} {self.dest} {self.distance} "
            f"{self.time} {self.fare} {self.flight_num}"
        )


@dataclass(frozen=True)
class Booking:
    booking_id: int
    passenger: str
    route: str
    fare: int
    seat: str

    def to_file_line(self) -> str:
        return (
            f"{self.booking_id} | {self.passenger} | {self.route} | "
            f"{self.fare} | {self.seat}"
        )


@dataclass(frozen=True)
class RouteResult:
    title: str
    metric_label: str
    metric_value: int | float | None
    path: list[str]
    route_keys: list[tuple[str, str, str]]
    message: str = ""

