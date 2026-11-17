from collections import deque

import pygame


class BossAI:
    """Rule-based adaptive boss controller with three health-driven phases."""

    def __init__(self):
        self.history = deque(maxlen=60)
        self.sample_interval = 0.2
        self.sample_timer = 0.0
        self.strategy = "ANALYSING"
        self.phase = 1
        self.phase_name = "ANALYSIS"

    def record_player(self, dt, position, shooting, boss_health, boss_max_health):
        previous_phase = self.phase
        health_ratio = boss_health / max(1, boss_max_health)

        if health_ratio <= 1 / 3:
            self.phase = 3
            self.phase_name = "CRITICAL FAILURE"
        elif health_ratio <= 2 / 3:
            self.phase = 2
            self.phase_name = "ADAPTATION"
        else:
            self.phase = 1
            self.phase_name = "ANALYSIS"

        self.sample_timer += dt
        if self.sample_timer >= self.sample_interval:
            self.sample_timer -= self.sample_interval
            self.history.append({
                "position": pygame.Vector2(position),
                "shooting": bool(shooting)
            })
            self.strategy = self.analyse()

        return self.phase != previous_phase

    def analyse(self):
        if len(self.history) < 15:
            return "ANALYSING"

        samples = list(self.history)
        movement = sum(
            samples[i - 1]["position"].distance_to(samples[i]["position"])
            for i in range(1, len(samples))
        )
        shooting_rate = sum(sample["shooting"] for sample in samples) / len(samples)

        if shooting_rate >= 0.60:
            return "AGGRESSIVE"
        if movement < 220:
            return "STATIONARY"
        return "MOBILE"

    def reset(self):
        self.history.clear()
        self.sample_timer = 0.0
        self.strategy = "ANALYSING"
        self.phase = 1
        self.phase_name = "ANALYSIS"
