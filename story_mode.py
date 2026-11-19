import math
from enum import Enum, auto

import pygame

from enemy import Enemy
from settings import WIDTH, HEIGHT
from ship_parts import ModularShip, load_explosion_frames


class StoryPhase(Enum):
    OPENING = auto()
    SCRIPTED_DEFEAT = auto()
    RECOVERY = auto()
    RECOVERY_COMPLETE = auto()


class StoryMode:
    opening_duration = 18.0
    defeat_duration = 0.95
    explosion_frame_time = 0.048
    assembled_hitbox = (64, 64)
    cockpit_hitbox = (44, 44)

    def __init__(self, player, ship_sprites):
        self.phase = StoryPhase.OPENING
        self.phase_time = 0.0
        self.tank_shot_timer = 1.0
        self.tank = Enemy(WIDTH - 160, HEIGHT // 2, 'tank')
        ship_sprites.prepare_enemy(self.tank)
        image = ship_sprites.player_image
        size = (80, round(80 * image.get_height() / image.get_width()))
        self.ship = ModularShip(pygame.transform.scale(image, size), player.position)
        self.explosion_frames = load_explosion_frames()
        player.rect.size = self.assembled_hitbox
        player.rect.center = player.position

    @property
    def controls_enabled(self):
        return self.phase != StoryPhase.SCRIPTED_DEFEAT

    def advance(self, dt, effects, audio):
        self.phase_time += dt
        if self.phase == StoryPhase.OPENING and self.phase_time >= self.opening_duration:
            self.phase = StoryPhase.SCRIPTED_DEFEAT
            self.phase_time = 0.0
            self.ship.explode()
            effects.sparks(self.ship.centre, 32, (255, 170, 70))
            effects.shake = 12
            effects.hit_overlay_timer = 0.28
            audio.play('enemy_down')
            return True

        if self.phase == StoryPhase.SCRIPTED_DEFEAT and self.phase_time >= self.defeat_duration:
            self.phase = StoryPhase.RECOVERY
            self.phase_time = 0.0
        return False

    def tank_ready_to_fire(self, enemy, dt):
        if enemy is not self.tank:
            return False
        self.tank_shot_timer -= dt
        if self.tank_shot_timer > 0:
            return False
        self.tank_shot_timer += 1.5
        return True

    def recover_part(self, key):
        if self.phase == StoryPhase.RECOVERY and pygame.K_1 <= key <= pygame.K_6:
            self.ship.recover_part(key - pygame.K_0)

    def update_ship(self, player, aim, dt, effects):
        self.ship.centre.update(player.position)
        if self.controls_enabled:
            direction = pygame.Vector2(aim) - player.position
            if direction.length_squared() > 0:
                self.ship.angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
        self.ship.update(dt)

        if self.phase == StoryPhase.RECOVERY and self.ship.state == 'intact':
            self.phase = StoryPhase.RECOVERY_COMPLETE
            player.rect.size = self.assembled_hitbox
            player.rect.center = player.position
            effects.sparks(self.ship.centre, 16, (95, 210, 255))
            effects.shake = max(effects.shake, 5)

    def draw_ship(self, surface):
        self.ship.draw(surface)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT:
            frame = int(self.phase_time / self.explosion_frame_time)
            if frame < len(self.explosion_frames):
                image = self.explosion_frames[frame]
                surface.blit(image, image.get_rect(center=self.ship.centre))

    def draw_hud(self, screen, font, player, ammo):
        if self.phase == StoryPhase.OPENING:
            message = 'Hold off the tank'
        elif self.phase == StoryPhase.SCRIPTED_DEFEAT:
            message = 'SYSTEM FAILURE'
        elif self.phase == StoryPhase.RECOVERY:
            recovered = sum(part.attached for part in self.ship.parts[1:])
            message = f'Press 1–6 to recover ship components  ({recovered}/6)'
        else:
            message = 'Ship reassembled'

        title = font.render(message, True, (210, 235, 255))
        screen.blit(title, title.get_rect(midtop=(WIDTH // 2, 20)))
        status = font.render(f'Health: {player.health}    Ammo: {ammo}', True, (255, 220, 90))
        screen.blit(status, (20, 20))
