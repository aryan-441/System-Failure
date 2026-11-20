import math
from enum import Enum, auto #cool library for game states

import pygame

from boss_ai import BossAI
from story_visuals import StoryHUD, scatter_wreckage, draw_shield
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
    RETURNING = auto()

class StoryMode:
    opening_duration = 18.0
    defeat_duration = 0.95
    explosion_frame_time = 0.048
    assembled_hitbox = (64, 64)
    cockpit_hitbox = (44, 44)

    def __init__(self, player, ship_sprites):
        self.phase = StoryPhase.OPENING
        self.phase_time = 0.0
        self.boss_ai = BossAI()
        self.boss = Enemy(WIDTH - 75, 110, 'adaptive core')
        self.boss.ship_image = ship_sprites.adaptive_image
        self.boss.is_boss = True
        self.boss.health = self.boss.max_health = 9
        self.boss.speed = 175
        self.boss.rect.size = (64, 64)
        self.boss.rect.center = self.boss.position
        self.shot_timer = 0.65
        self.shield_flash = 0.0
        self.shielded = False
        self.wreckage = []
        self.hud = StoryHUD()
        image = ship_sprites.player_image
        size = (80, round(80 * image.get_height() / image.get_width()))
        self.ship = ModularShip(pygame.transform.scale(image, size), player.position)
        self.debris_source = pygame.transform.scale(image, size)
        self.explosion_frames = load_explosion_frames()
        player.rect.size = self.assembled_hitbox
        player.rect.center = player.position

        self.recovery_step = RecoveryStep.OBJECTIVE
        self.objective_index = 0
        self.objective_progress = 0
        self.objective_timer = 0.0

        
        self.objectives = [
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'normal'],
                'target': 3,
                'debuff': 'DAMAGED_THRUSTERS',
                'upgrade': 'ENHANCED_THRUSTERS',
                'description': 'Wave 1: Defeat 3 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'normal', 'normal', 'interceptor'],
                'target': 5,
                'debuff': 'TARGETING_GLITCH',
                'upgrade': 'TARGETING_COMPUTER',
                'description': 'Wave 2: Defeat 5 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'normal', 'interceptor', 'interceptor'],
                'target': 5,
                'debuff': 'HULL_BREACH',
                'upgrade': 'REINFORCED_ARMOUR',
                'description': 'Wave 3: Defeat 5 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'interceptor', 'interceptor', 'ranger'],
                'target': 5,
                'debuff': 'AMMO_LEAK',
                'upgrade': 'EXPANDED_MAGAZINE',
                'description': 'Wave 4: Defeat 5 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'interceptor', 'interceptor', 'ranger', 'ranger'],
                'target': 6,
                'debuff': 'SALVAGE_FAILURE',
                'upgrade': 'SALVAGE_MODULE',
                'description': 'Wave 5: Defeat 6 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'normal', 'interceptor', 'interceptor', 'tank'],
                'target': 5,
                'debuff': 'WEAPON_OVERHEATING',
                'upgrade': 'OVERCLOCKED_WEAPONS',
                'description': 'Wave 6: Defeat 5 enemies'
            }
        ]

        self.spawned_objective_index = -1
        self.wave_spawn_index = 0
        self.wave_spawn_timer = 0.0
        self.wave_spawn_interval = 0.0
        self.wave_active_limit = 0
        self.wave_active_enemies = []

    @property #decorator- allows controls_enabled to behave like an attribute instead of a method
    def controls_enabled(self):
        return self.phase != StoryPhase.SCRIPTED_DEFEAT

    def advance(self, dt, effects, audio):
        self.phase_time += dt
        self.shield_flash = max(0, self.shield_flash - dt)
        for fragment in self.wreckage:
            fragment.update(dt)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT and self.phase_time >= self.defeat_duration:
            self.phase = StoryPhase.RECOVERY
            self.phase_time = 0.0

    def opening_enemies(self, sprites):
        enemies = [self.boss]
        for x, y in [(WIDTH - 70, HEIGHT - 70), (90, 85)]:
            minion = Enemy(x, y, 'interceptor')
            sprites.prepare_enemy(minion, allow_boss=False)
            enemies.append(minion)
        return enemies

    def update_boss(self, dt, player, firing, audio):
        changed = self.boss_ai.record_player(dt, player.position, firing, self.boss.health, self.boss.max_health)
        if changed:
            audio.play('warning')
        self.boss.update(dt, player.position, self.boss_ai.strategy, self.boss_ai.phase)
        arena = pygame.Rect(0, 0, WIDTH, HEIGHT)
        if not arena.contains(self.boss.rect):
            self.boss.rect.clamp_ip(arena)
            self.boss.position.update(self.boss.rect.center)
        self.shot_timer -= dt

    def aim_boss_shot(self, player):
        offset = player.position - self.boss.position
        history = self.boss_ai.history
        if len(history) >= 2:
            velocity = (history[-1]['position'] - history[-2]['position']) / self.boss_ai.sample_interval
            offset += velocity * min(0.55, offset.length() / 320)
        self.shot_timer = 0.95
        return offset

    def hit_boss(self, impact, effects, audio):
        if self.shielded:
            self.shield_flash = 0.22
            effects.sparks(impact, 9, (140, 235, 255))
        else:
            self.boss.take_damage(1)
            effects.hit_enemy(self.boss)
            if self.boss.health <= self.boss.max_health - 3:
                self.shielded = True
                self.shield_flash = 0.35
                audio.play('warning')

    def finish_opening(self, player, enemies, bullets, enemy_bullets, effects, audio):
        if self.phase != StoryPhase.OPENING:
            return False
        if self.phase_time < self.opening_duration and not self.boss.rect.colliderect(player.rect):
            return False
        self.phase = StoryPhase.SCRIPTED_DEFEAT
        self.phase_time = 0.0
        self.ship.centre.update(player.position)
        self.ship.update(0)
        self.ship.explode()
        self.wreckage = scatter_wreckage(self.debris_source, player.position, self.ship.angle)
        effects.sparks(player.position, 32, (255, 170, 70))
        effects.shake = 12
        effects.hit_overlay_timer = 0.28
        audio.play('enemy_down')
        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()
        player.rect.size = self.cockpit_hitbox
        player.rect.center = player.position
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

    def draw_boss_shield(self, surface):
        draw_shield(surface, self.boss.rect.center, self.phase_time, self.shield_flash)

    def draw_ship(self, surface):
        for fragment in self.wreckage:
            fragment.draw(surface)
        if self.phase == StoryPhase.RECOVERY:
            objective = self.objectives[self.objective_index]
            target = None
            if self.recovery_step == RecoveryStep.PICKUP:
                target = self.ship.parts[self.objective_index + 1].position
            elif self.recovery_step == RecoveryStep.OBJECTIVE and objective['type'] == 'reach':
                target = objective['target']
            if target is not None:
                pygame.draw.circle(surface, (115, 235, 215), target, 18, 2)
        self.ship.draw(surface)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT:
            frame = int(self.phase_time / self.explosion_frame_time)
            if frame < len(self.explosion_frames):
                image = self.explosion_frames[frame]
                surface.blit(image, image.get_rect(center=self.ship.centre))

    def draw_hud(self, screen, player, ammo, health_limit, ammo_limit, debuff, description):
        self.hud.draw(screen, self, player.health, ammo, health_limit, ammo_limit, debuff, description)

    def update_objective(self, dt, player):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step !=  RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return

        self.objective_timer += dt

    def record_kill(self,enemy):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step != RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return
        objective = self.objectives[self.objective_index]
        if objective['type'] != 'kill':
            return
        if enemy.enemy_type != objective['enemy']:
            return

        self.wave_active_enemies.remove(enemy)
        self.objective_progress += 1

        objective = self.objectives[self.objective_index]
        
        if self.objective_progress >= objective['target']:
            if self.wave_spawn_index >= len(objective['enemies']):
                if not self.wave_active_enemies:

                    self.recovery_step = RecoveryStep.PICKUP

    def update_pickup(self,player):
        if self.phase != StoryPhase.RECOVERY:
            return
        part_id = self.objective_index + 1 #bcuz we arent collecting the cockpit
        part = self.ship.parts[part_id]
        if self.recovery_step == RecoveryStep.PICKUP:
            part.velocity = pygame.Vector2(0,0)
            part.rotation_speed = 0

            margin = 60
            part.position.x = max(margin,min(WIDTH-margin, part.position.x))

            part.position.y = max(margin,min(HEIGHT - margin, part.position.y))

            distance = player.position.distance_to(part.position)
            if distance <= 40:
                self.ship.recover_part(part_id)
                self.recovery_step = RecoveryStep.RETURNING
        elif self.recovery_step == RecoveryStep.RETURNING:
            if part.attached:
                if self.objective_index < len(self.objectives) - 1:
                    self.objective_index += 1
                    self.objective_progress = 0
                    self.objective_timer = 0.0
                    self.recovery_step = RecoveryStep.OBJECTIVE

    def spawn_recovery_enemies(self, enemies, ship_sprites, player, dt):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step != RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return
        
        objective = self.objectives[self.objective_index]

        if self.spawned_objective_index != self.objective_index:
            self.spawned_objective_index = self.objective_index
            self.wave_spawn_index = 0
            self.wave_spawn_timer = self.wave_spawn_interval
            self.wave_active_enemies = []

        self.wave_spawn_timer += dt

        if self.wave_spawn_index >= len(objective['enemies']):
            return
        if len(self.wave_active_enemies) >= self.wave_active_limit:
            return
        spawn_positions = [
            (70,70),
            (WIDTH - 70, 70),
            (70, HEIGHT - 70),
            (WIDTH - 70, HEIGHT - 70),
            (WIDTH // 2, 70),
            (WIDTH // 2, HEIGHT - 70),
        ]

        spawn_positions.sort(
            key = lambda position: player.position.distance_to(position), reverse=True
        )
        position_index = self.wave_spawn_index % len(spawn_positions)
        x,y = spawn_positions[position_index]

        enemy_type = objective['enemies'][self.wave_spawn_index]
        enemy = Enemy(x, y, enemy_type)
        ship_sprites.prepare_enemy(enemy,allow_boss=True)

        enemies.append(enemy)
        self.wave_active_enemies.append(enemy)
        self.wave_spawn_index += 1
        self.wave_spawn_timer = 0.0
