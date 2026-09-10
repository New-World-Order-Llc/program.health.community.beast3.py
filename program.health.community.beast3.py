# program.health.community.beast3.py
# Beast System 3.0 — Deterministic Community Health Engine

from dataclasses import dataclass, field
import time
import hashlib
import statistics

@dataclass
class CommunityPacket:
    community_id: str
    aggregated_score: float
    stability_index: float
    shared_risk_flags: list
    recommended_interventions: list
    population_size: int
    ts: float = field(default_factory=time.time)
    hash: str = ""

    def finalize(self):
        serialized = f"{self.community_id}{self.aggregated_score}{self.stability_index}{self.shared_risk_flags}{self.recommended_interventions}{self.population_size}{self.ts}".encode("utf-8")
        self.hash = hashlib.sha256(serialized).hexdigest()

@dataclass
class CommunityProfile:
    community_id: str
    packets: list = field(default_factory=list)
    last_update: float = field(default_factory=time.time)

    def add_packet(self, packet: CommunityPacket):
        packet.finalize()
        self.packets.append(packet)
        self.last_update = packet.ts

class CommunityHealthEngine:
    def __init__(self, kernel, scoring_engine, vitals_engine, continuity_engine):
        self.kernel = kernel
        self.scoring_engine = scoring_engine
        self.vitals_engine = vitals_engine
        self.continuity_engine = continuity_engine
        self.communities = {}

    def create_community(self, community_id: str):
        profile = CommunityProfile(community_id)
        self.communities[community_id] = {
            "profile": profile,
            "families": set()
        }

        return self.kernel.dispatch(
            module="health.community",
            action="create_community",
            payload={"community_id": community_id}
        )

    def add_family(self, community_id: str, family_id: str):
        if community_id not in self.communities:
            raise ValueError("Community not found")

        self.communities[community_id]["families"].add(family_id)

        return self.kernel.dispatch(
            module="health.community",
            action="add_family",
            payload={"community_id": community_id, "family_id": family_id}
        )

    def compute_community_health(self, community_id: str):
        if community_id not in self.communities:
            raise ValueError("Community not found")

        families = list(self.communities[community_id]["families"])
        if not families:
            raise ValueError("No families in community")

        scores = []
        stability_values = []
        risk_flags = []

        for family_id in families:
            # Scoring
            score_profile = self.scoring_engine.get_scores(family_id)
            if score_profile and score_profile.packets:
                latest_score = score_profile.packets[-1]
                scores.append(latest_score.score)
                risk_flags.extend(latest_score.risk_flags)

            # Vitals
            vitals_profile = self.vitals_engine.get_packets(family_id)
            if vitals_profile and vitals_profile.packets:
                latest_vitals = vitals_profile.packets[-1]
                stability_values.append(latest_vitals.stability_score)
                risk_flags.extend(latest_vitals.risk_flags)

            # Continuity
            continuity_profile = self.continuity_engine.get_packets(family_id)
            if continuity_profile and continuity_profile.packets:
                latest_continuity = continuity_profile.packets[-1]
                stability_values.append(latest_continuity.continuity_score)
                if latest_continuity.escalation_required:
                    risk_flags.append("continuity_escalation")

        aggregated_score = round(statistics.mean(scores), 4) if scores else 0.0
        stability_index = round(statistics.mean(stability_values), 4) if stability_values else 0.0

        # Shared risk indicators
        shared_risk_flags = list(set(risk_flags))

        # Community-level interventions
        recommended_interventions = []
        if aggregated_score < 0.40:
            recommended_interventions.append("community_intensive_support")
        elif aggregated_score < 0.55:
            recommended_interventions.append("community_support_programs")

        if stability_index < 0.50:
            recommended_interventions.append("community_health_stabilization")

        packet = CommunityPacket(
            community_id=community_id,
            aggregated_score=aggregated_score,
            stability_index=stability_index,
            shared_risk_flags=shared_risk_flags,
            recommended_interventions=recommended_interventions,
            population_size=len(families)
        )

        profile = self.communities[community_id]["profile"]
        profile.add_packet(packet)

        return self.kernel.dispatch(
            module="health.community",
            action="compute_community_health",
            payload={
                "community_id": community_id,
                "aggregated_score": aggregated_score,
                "stability_index": stability_index,
                "shared_risk_flags": shared_risk_flags,
                "recommended_interventions": recommended_interventions,
                "population_size": len(families)
            }
        )

    def get_packets(self, community_id: str):
        if community_id not in self.communities:
            return None
        return self.communities[community_id]["profile"].packets
