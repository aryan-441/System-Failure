import random


class RoundManager:
    def __init__(self):
        self.round_number = 0
        self.round_duration = 30.0
        self.round_timer = 0.0
        self.initial_safe_time = 15.0
        self.elapsed_time = 0.0
        self.started = False

        self.malfunctions = [
            'REVERSED',
            'RECOIL',
            'DAMAGED_THRUSTERS',
            'SHIELD_MALFUNCTION',
            'WEAPON_OVERHEATING',
            'ENGINE_STALLING',
            'TARGETING_GLITCH',
            'ENGINE_DRIFT',
            'REACTOR_INSTABILITY',
        ]
        self.current_malfunction = 'NONE'

    def update(self, dt):
        self.elapsed_time += dt

        if not self.started:
            if self.elapsed_time >= self.initial_safe_time:
                self.started = True
                self.round_number = 1
                self.round_timer = 0.0
                self.current_malfunction = random.choice(self.malfunctions)
                return True
            return False

        self.round_timer += dt
        if self.round_timer >= self.round_duration:
            self.round_timer -= self.round_duration
            self.round_number += 1

            available = [
                malfunction for malfunction in self.malfunctions
                if malfunction != self.current_malfunction
            ]
            self.current_malfunction = random.choice(available)
            return True

        return False
