# agents.py
import random
import numpy as np

class IntentionAgent:
    """
    Projects direction and scale of market/world intention.
    """
    def __init__(self):
        pass

    def analyze(self, data):
        """
        Analyzes data to produce an intention score (-1 to +1) and scale (0 to 1).
        """
        # Placeholder logic – replace with actual model or logic
        polarity = self._estimate_intention(data)
        scale = self._estimate_scale(data)

        score = polarity * scale
        return {
            "polarity": polarity,
            "scale": scale,
            "score": score
        }

    def _estimate_intention(self, data):
        # e.g., based on sentiment, trend analysis
        return random.choice([-1, 0, 1])

    def _estimate_scale(self, data):
        # e.g., based on volume, social momentum
        return np.clip(np.random.normal(0.5, 0.2), 0, 1)


class ChaosAgent:
    """
    Detects divergence, randomness, or noise in the system.
    """
    def __init__(self):
        pass

    def analyze(self, data):
        """
        Outputs chaos level (0 = no chaos, 1 = maximum chaos).
        """
        chaos_level = self._detect_chaos(data)
        return {
            "chaos_level": chaos_level
        }

    def _detect_chaos(self, data):
        # Placeholder: use volatility, headline frequency, or pattern breaks
        volatility = np.std(data["prices"][-10:]) if "prices" in data else random.random()
        chaos_score = np.clip(volatility / 10, 0, 1)  # scale appropriately
        return chaos_score
