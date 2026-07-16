class CrowdRiskEngine:
    CHOKE_POINT_ADJACENCY = {
        "concourse_1": ["A1", "A2"],
        "concourse_2": ["B1", "B2", "C1", "C2"],
    }

    RISK_ACTIONS = {
        "low": "No action required",
        "medium": "Monitor closely",
        "high": "Activate crowd guidance volunteers",
        "critical": "Immediate redirect — close entry to this section",
    }

    RISK_ORDER = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }

    def score_section(
        self,
        section_id: str,
        occupancy_pct: float,
        match_phase: str,
        weather: str,
        queue_times: dict,
    ) -> dict:
        """Calculate a crowd risk score and response recommendation for one section.

        The score starts from occupancy percentage and applies deterministic bonuses
        for high-flow match phases, weather, choke point adjacency, and the nearest
        food court queue. The final score is capped at 100 and translated into a
        low, medium, high, or critical risk level.
        """
        risk_score = occupancy_pct
        risk_factors = []

        if match_phase in ["halftime", "post_match"]:
            risk_score += 15
            risk_factors.append(f"Match phase is {match_phase}")

        if weather == "rainy":
            risk_score += 10
            risk_factors.append("Rainy weather")
        elif weather == "humid":
            risk_score += 8
            risk_factors.append("Humid weather")

        if self._is_adjacent_to_choke_point(section_id):
            risk_score += 12
            risk_factors.append("Adjacent to choke point")

        nearest_food_court = self._nearest_food_court(section_id)
        if queue_times.get(nearest_food_court, 0) > 20:
            risk_score += 10
            risk_factors.append(f"Nearest food court queue exceeds 20 minutes")

        final_score = min(risk_score, 100)
        risk_level = self._risk_level(final_score)

        return {
            "section_id": section_id,
            "occupancy_pct": occupancy_pct,
            "risk_score": final_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "suggested_action": self.RISK_ACTIONS[risk_level],
        }

    def analyze_stadium(
        self,
        section_occupancy: dict,
        match_phase: str,
        weather: str,
        queue_times: dict,
    ) -> dict:
        """Score every stadium section and summarize the overall crowd risk.

        Each section in section_occupancy is evaluated with score_section. The
        result groups high and critical sections, produces navigation avoid node
        IDs for those sections, identifies the worst risk level, and returns a
        concise operations summary.
        """
        section_scores = [
            self.score_section(
                section_id,
                occupancy_pct,
                match_phase,
                weather,
                queue_times,
            )
            for section_id, occupancy_pct in section_occupancy.items()
        ]

        critical_sections = [
            score["section_id"]
            for score in section_scores
            if score["risk_level"] == "critical"
        ]
        high_risk_sections = [
            score["section_id"]
            for score in section_scores
            if score["risk_level"] == "high"
        ]
        avoid_sections = critical_sections + high_risk_sections
        avoid_nodes = [f"section_{section_id.lower()}" for section_id in avoid_sections]

        overall_risk = "low"
        for score in section_scores:
            if self.RISK_ORDER[score["risk_level"]] > self.RISK_ORDER[overall_risk]:
                overall_risk = score["risk_level"]

        return {
            "sections": section_scores,
            "critical_sections": critical_sections,
            "high_risk_sections": high_risk_sections,
            "avoid_nodes": avoid_nodes,
            "overall_risk": overall_risk,
            "summary": self._build_summary(critical_sections, high_risk_sections),
        }

    def compute_choke_pressure(self, concourse_id: str, section_scores: list) -> dict:
        """Average adjacent section scores to estimate pressure at a concourse.

        Only sections adjacent to the requested concourse are included. The average
        pressure score is converted into the same low, medium, high, or critical
        levels used for sections, then paired with an operations recommendation.
        """
        adjacent_sections = self.CHOKE_POINT_ADJACENCY.get(concourse_id, [])
        relevant_scores = [
            score["risk_score"]
            for score in section_scores
            if score["section_id"] in adjacent_sections
        ]

        if relevant_scores:
            pressure_score = sum(relevant_scores) / len(relevant_scores)
        else:
            pressure_score = 0

        pressure_level = self._risk_level(pressure_score)

        return {
            "concourse_id": concourse_id,
            "pressure_score": pressure_score,
            "pressure_level": pressure_level,
            "recommendation": self._pressure_recommendation(pressure_level),
        }

    def _is_adjacent_to_choke_point(self, section_id: str) -> bool:
        return any(
            section_id in adjacent_sections
            for adjacent_sections in self.CHOKE_POINT_ADJACENCY.values()
        )

    def _nearest_food_court(self, section_id: str) -> str:
        if section_id.startswith("A"):
            return "food_court_a"
        return "food_court_b"

    def _risk_level(self, score: float) -> str:
        if score < 40:
            return "low"
        if score < 65:
            return "medium"
        if score < 80:
            return "high"
        return "critical"

    def _build_summary(self, critical_sections: list[str], high_risk_sections: list[str]) -> str:
        if critical_sections:
            return (
                f"{len(critical_sections)} critical sections detected. "
                "Immediate action required."
            )
        if high_risk_sections:
            return (
                f"{len(high_risk_sections)} high risk sections detected. "
                "Activate crowd guidance volunteers."
            )
        return "No high or critical crowd risks detected. Continue monitoring."

    def _pressure_recommendation(self, pressure_level: str) -> str:
        recommendations = {
            "low": "Concourse flow is normal",
            "medium": "Monitor concourse density",
            "high": "Deploy volunteers to improve concourse flow",
            "critical": "Redirect fans away from this concourse immediately",
        }
        return recommendations[pressure_level]
