
import random

class RoundManager:

    def __init__(self):
        self.round_number = 1
        self.round_duration = 30
        self.round_timer = 0

        self.malfunctions = [
            'REVERSED',
            'RECOIL',
            'DAMAGED_THRUSTERS',
            'SHIELD_MALFUNCTION',
            'WEAPON_OVERHEATING',
            'ENGINE_STALLING',
            'TARGETING_GLITCH',
            'ENGINE_DRIFT',
            'REACTOR_INSTABILITY'
        ]

        self.current_malfunction = random.choice(self.malfunctions)

    def update(self, dt):
        self.round_timer += dt

        if self.round_timer >= self.round_duration:
            self.round_timer -= self.round_duration
            self.round_number += 1

            available = [
                m for m in self.malfunctions
                if m != self.current_malfunction
            ]

            self.current_malfunction = random.choice(available)

            return True

        return False