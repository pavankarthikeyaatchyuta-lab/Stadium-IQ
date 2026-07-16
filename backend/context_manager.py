from dataclasses import dataclass, field


@dataclass
class ContextManager:
    current_time: str = "19:45"
    match_phase: str = "halftime"
    gate_status: dict = field(
        default_factory=lambda: {"A": "open", "B": "open", "C": "closed", "D": "open"}
    )
    weather: str = "clear"
    queue_times: dict = field(
        default_factory=lambda: {
            "food_court_a": 25,
            "food_court_b": 5,
            "restroom_north": 3,
        }
    )
    section_occupancy: dict = field(
        default_factory=lambda: {
            "A1": 85,
            "A2": 40,
            "B1": 92,
            "B2": 55,
            "C1": 70,
            "C2": 30,
        }
    )
    nearby_transport: dict = field(
        default_factory=lambda: {
            "metro": "available",
            "rideshare": "15min_wait",
            "parking_north": "full",
            "parking_south": "available",
        }
    )

    @classmethod
    def from_dict(cls, data: dict) -> "ContextManager":
        return cls(**data)

    def to_summary(self) -> str:
        return (
            "Stadium Context Summary\n"
            f"- Current time: {self.current_time}\n"
            f"- Match phase: {self.match_phase}\n"
            f"- Gate status: {self.gate_status}\n"
            f"- Weather: {self.weather}\n"
            f"- Queue times: {self.queue_times}\n"
            f"- Section occupancy: {self.section_occupancy}\n"
            f"- Nearby transport: {self.nearby_transport}"
        )
