import heapq
import json
from functools import lru_cache
from pathlib import Path


class NavigationGraph:
    def __init__(self, map_path: str | None = None):
        if map_path is None:
            map_path = Path(__file__).resolve().parent.parent / "data" / "stadium_map.json"
        else:
            map_path = Path(map_path)
            if not map_path.exists():
                map_path = Path(__file__).resolve().parents[2] / map_path

        with map_path.open("r", encoding="utf-8") as file:
            stadium_map = json.load(file)

        self.nodes = stadium_map["nodes"]
        self.graph = {node_id: [] for node_id in self.nodes}

        for edge in stadium_map["edges"]:
            start = edge["from"]
            end = edge["to"]
            weight = edge["weight"]
            self.graph[start].append((end, weight))
            self.graph[end].append((start, weight))

    def _dijkstra(self, start, end, blocked_nodes=[]):
        blocked = set(blocked_nodes)
        if start in blocked or end in blocked:
            return []

        queue = [(0, start, [start])]
        visited = set()

        while queue:
            current_distance, current_node, path = heapq.heappop(queue)

            if current_node in visited:
                continue

            if current_node == end:
                return path

            visited.add(current_node)

            for neighbor, weight in self.graph.get(current_node, []):
                if neighbor in visited or neighbor in blocked:
                    continue

                heapq.heappush(
                    queue,
                    (current_distance + weight, neighbor, path + [neighbor]),
                )

        return []

    @lru_cache(maxsize=128)
    def _dijkstra_cached(self, start: str, end: str, blocked_nodes: tuple[str, ...]) -> list[str]:
        return self._dijkstra(start, end, blocked_nodes)

    def find_path(self, start: str, end: str, avoid_nodes: list[str] | None = None) -> list[str]:
        if avoid_nodes is None:
            avoid_nodes = []
        return self._dijkstra_cached(start, end, tuple(avoid_nodes))

    def get_path_summary(self, path: list[str]) -> dict:
        estimated_minutes = 0

        for index in range(len(path) - 1):
            current_node = path[index]
            next_node = path[index + 1]

            for neighbor, weight in self.graph.get(current_node, []):
                if neighbor == next_node:
                    estimated_minutes += weight
                    break

        passes_through = [
            node_id
            for node_id in path
            if self.nodes[node_id]["type"] in {"amenity", "transport"}
        ]

        return {
            "path": path,
            "path_names": [self.nodes[node_id]["name"] for node_id in path],
            "node_count": len(path),
            "estimated_minutes": estimated_minutes,
            "distance_meters": estimated_minutes * 15,
            "passes_through": passes_through,
        }

    def get_open_gates(self, gate_status: dict) -> list[str]:
        gate_mapping = {
            "A": "gate_a",
            "B": "gate_b",
            "C": "gate_c",
            "D": "gate_d",
        }

        return [
            gate_mapping[gate]
            for gate, status in gate_status.items()
            if status == "open" and gate in gate_mapping
        ]
