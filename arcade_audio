from pathlib import Path
import pygame


class ArcadeAudio:
    """Loads optional sound effects; missing audio never blocks gameplay."""

    SOUND_FILES = {
        "shoot": "shoot.wav",
        "hit": "hit.wav",
        "enemy_down": "enemy_down.wav",
        "player_hit": "player_hit.wav",
        "game_over": "game_over.wav",
        "overheat": "overheat.wav",
        "ammo": "ammo.wav",
        "warning": "warning.wav",
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
