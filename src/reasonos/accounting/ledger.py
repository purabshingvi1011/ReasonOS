from typing import Any, Dict, List, Optional

class AccountingLedger:
    """
    Tracks cost, risk, and confidence adjustments for a reasoning run.
    """
    
    def __init__(self, base_confidence: float = 0.0):
        self.total_cost: float = 0.0
        self.total_risk: float = 0.0
        self.base_confidence: float = base_confidence
        self.confidence_adjustments: List[Dict[str, Any]] = []
        self.final_confidence: float = base_confidence
        self.is_blocked: bool = False

    def set_base_confidence(self, confidence: float) -> None:
        """Set the base confidence (e.g. from verification step)."""
        self.base_confidence = confidence
        self._recompute_final_confidence()

    def add_cost(self, amount: float, reason: str) -> None:
        """Record a cost."""
        self.total_cost += amount

    def add_risk(self, amount: float, reason: str) -> None:
        """Record a risk."""
        self.total_risk += amount

    def adjust_confidence(self, delta: float, source: str, reason: str) -> None:
        """Record a confidence adjustment."""
        self.confidence_adjustments.append({
            "source": source,
            "delta": delta,
            "reason": reason
        })
        self._recompute_final_confidence()

    def force_block(self) -> None:
        """Force risk to 1.0 and confidence to 0.0 due to policy block."""
        self.is_blocked = True
        self.total_risk = 1.0
        
        # Add adjustment to bring confidence to 0.0
        current_conf = self.final_confidence
        if current_conf > 0:
            self.confidence_adjustments.append({
                "source": "policy_block",
                "delta": -current_conf,
                "reason": "Policy forced block"
            })
            
        self.final_confidence = 0.0

    def _recompute_final_confidence(self) -> None:
        """Recompute final confidence from base and adjustments."""
        if self.is_blocked:
            self.final_confidence = 0.0
            return

        conf = self.base_confidence
        for adj in self.confidence_adjustments:
            conf += adj["delta"]
        
        # Clamp to 0..1
        self.final_confidence = max(0.0, min(1.0, conf))

    def get_snapshot(self) -> Dict[str, Any]:
        """Return the accounting object for the RSL."""
        return {
            "total_cost": round(self.total_cost, 2),
            "total_risk": round(self.total_risk, 2),
            "base_confidence": round(self.base_confidence, 2),
            "confidence_adjustments": self.confidence_adjustments,
            "final_confidence": round(self.final_confidence, 2)
        }
