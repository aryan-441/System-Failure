from pathlib import Path
import pygame


class ArcadeAudio:
    """Loads optional sound effects; missing audio never blocks gameplay."""

    
    SOUND_FILES = {
        "shoot": "weapons/laser_small.ogg",
        "hit": "warnings/player_damage_metal_impact.ogg",
        "enemy_down": "explosions/explosion_crunch.ogg",
        "player_hit": "warnings/player_damage_metal_impact.ogg",
        "game_over": "interface/defeat.ogg",
        "overheat": "warnings/system_force_field.ogg",
        "ammo": "interface/recovery_shield_up.ogg",
        "core_shot": "weapons/laser_large.ogg",
        "core_shield": "warnings/system_force_field.ogg",
        "core_repair": "interface/recovery_shield_up.ogg",
        "wave_clear": "interface/victory_or_confirm.ogg",
        "part_pickup": "interface/kenney/select_006.ogg",
        "part_attached": "interface/kenney/confirmation_002.ogg",
        "wave_fault": "interface/kenney/glitch_003.ogg",
        "warning": "warnings/system_computer_noise.ogg"
    }


    def __init__(self):
        self.sounds = {}
        self.enabled = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            folder = Path(__file__).parent / "assets" / "audio"

            for key, filename in self.SOUND_FILES.items():
                path = folder / filename
                if path.exists():
                    try:
                        sound = pygame.mixer.Sound(str(path))
                        sound.set_volume(0.45)
                        self.sounds[key] = sound
                    except (pygame.error, OSError):
                        pass

            self.enabled = True
            print("Loaded sounds:", list(self.sounds.keys()))
            print("Audio enabled:", self.enabled)

            
        except pygame.error:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass