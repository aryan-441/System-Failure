import math
from enum import Enum, auto #cool library for game states

import pygame

from enemy import Enemy
from settings import WIDTH, HEIGHT
from ship_parts import ModularShip, load_explosion_frames


class StoryPhase(Enum):
    OPENING = auto()
    SCRIPTED_DEFEAT = auto()
    RECOVERY = auto()
    RECOVERY_COMPLETE = auto()

class RecoveryStep(Enum):
    OBJECTIVE = auto()
    PICKUP = auto()
    RETURNNG = auto()

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

        self.recovery_step = RecoveryStep.OBJECTIVE
        self.objective_index = 0
        self.objective_progress = 0
        self.objective_timer = 0.0

        self.objectives = [
            {
                "type": "kill",
                "enemy": "normal",
                "target": 3,
                "description": "Defeat 3 chasers"
            },
            {
                "type": "survive",
                "target": 20,
                "description": "Survive the enemy wave"
            },
            {
                "type": "reach",
                "target": (WIDTH - 120, HEIGHT - 100),
                "description": "Reach the distress signal"
            },
            {
                "type": "kill",
                "enemy": "interceptor",
                "target": 2,
                "description": "Defeat 2 interceptors"
            },
            {
                "type": "survive",
                "target": 25,
                "description": "Survive the enemy assault"
            },
            {
                "type": "kill",
                "enemy": "normal",
                "target": 5,
                "description": "Eliminate the remaining enemies"
            }
        ]

        self.spawned_objective_index = -1
    @property #decorator- allows controls_enabled to behave like an attribute instead of a method
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

    def update_objective(self, dt, player):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step !=  RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return

        objective = self.objectives[self.objective_index]
        if objective['type'] == 'survive':
            self.objective_timer += dt

            if self.objective_timer >= objective['target']:
                self.recovery_step = RecoveryStep.PICKUP

        elif objective['type'] == 'reach':
            target_position = pygame.Vector2(objective['target'])
            distance = player.position.distance_to(target_position)

            if distance <= 35:
                self.recovery_step = RecoveryStep.PICKUP

    def record_kill(self,enemy):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.phase != RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return
        objective = self.objectives[self.objective_index]
        if objective['type'] != 'kill':
            return
        if enemy.enemy_type != objective['enemy']:
            return
        self.objective_progress += 1
        if self.objective_progress >= objective['target']:
            self.recovery_step = RecoveryStep.PICKUP

    def update_pickup(self,player):
        if self.phase != StoryPhase.RECOVERY:
            return
        part_id = self.objective_index + 1 #bcuz we arent collecting the cockpit
        part = self.ship_parts[part_id]
        if self.recovery_step == RecoveryStep.PICKUP:
            part.velocity = pygame.Vector2(0,0)
            part.rotation_speed = 0

            margin = 60
            part.position.x = max(margin,min(WIDTH-margin, part.position.x))

            part.position.y = max(margin,min(HEIGHT - margin, part.position.y))

            distance = player.position.distance_to(part.position)
            if distance <= 40:
                self.ship.recover_part(part_id)
                self.recovery_step(RecoveryStep.RETURNING)
            elif self.recovery_step == RecoveryStep.RETURNING:
                if part.attached:
                    if self.objective_index < len(self.objectives) - 1:
                        self.objective_index += 1
                        self.objective_progress = 0
                        self.objective_timer = 0.0
                        self.recovery_step = RecoveryStep.OBJECTIVE

    def spawn_recovery_enemies(self, enemies, ship_sprites, player):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step != RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return
        if self.spawned_objective_index == self.objective_index:
            return
        objective = self.objectives[self.objective_index]

        if objective['type'] == 'kill':
            enemy_types = [objective['enemy']] * objective['target']
        elif objective['type'] == 'survive':
            enemy_types = ['normal','normal','interceptor']
        elif objective['type'] == 'reach':
            enemy_types = ['normal', 'normal']
        else:
            return

        spawn_positions = [
            (70, 70),
            (WIDTH - 70, 70),
            (70, HEIGHT - 70),
            (WIDTH - 70, HEIGHT - 70),
            (WIDTH // 2, 70),
            (WIDTH // 2, HEIGHT - 70)
        ]

        spawn_positions.sort(
            key=lambda position: player.position.distance_to(position),
            reverse=True
        )

        enemies.clear()

        for i, enemy_type in enumerate(enemy_types):
            x, y = spawn_positions[i]

            enemy = Enemy(x, y, enemy_type)
            ship_sprites.prepare_enemy(enemy, allow_boss=False)

            enemies.append(enemy)

        self.spawned_objective_index = self.objective_index
