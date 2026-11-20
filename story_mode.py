import math
from enum import Enum, auto #cool library for game states

import pygame

from boss_ai import BossAI
from story_visuals import StoryHUD, scatter_wreckage, draw_shield, draw_gun_charge
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
    INTERMISSION = auto()

class StoryMode:
    boss_bullet_speed = 315
    charge_start = 6.0
    charge_duration = 1.5
    opening_shot_interval = 1.8
    charged_shot_interval = 0.95
    opening_duration = 18.0
    defeat_duration = 2.15
    scatter_duration = 0.95
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
        self.boss.speed = 90
        self.boss.rect.size = (64, 64)
        self.boss.rect.center = self.boss.position
        self.shot_timer = self.opening_shot_interval
        self.shield_flash = 0.0
        self.shielded = False
        self.repair_timer = 0.0
        self.last_player_position = player.position.copy()
        self.player_velocity = pygame.Vector2()
        self.part_origins = []
        self.part_locations = [(0.16, 0.32), (0.82, 0.74), (0.46, 0.83),
                               (0.76, 0.32), (0.19, 0.76), (0.50, 0.36)]
        self.wave_clear_timer = 0.0
        self.wreckage = []
        self.departing_ships = []
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

        self.active_debuffs = set()
        self.recovered_upgrades = set()
        self.rewarded_parts = set()
        self.pending_rewards = 0
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
        self.wave_spawn_interval = 1.35
        self.wave_active_limit = 2
        self.wave_active_enemies = []
        self.intermission_duration = 3.0
        self.intermission_timer = 0.0
    @property #decorator- allows controls_enabled to behave like an attribute instead of a method
    def controls_enabled(self):
        return self.phase != StoryPhase.SCRIPTED_DEFEAT

    def advance(self, dt, effects, audio):
        self.phase_time += dt
        self.repair_timer = max(0, self.repair_timer - dt)
        self.wave_clear_timer = max(0, self.wave_clear_timer - dt)
        self.shield_flash = max(0, self.shield_flash - dt)
        for fragment in self.wreckage:
            fragment.update(dt)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT and self.phase_time >= self.defeat_duration:
            self.departing_ships.clear()
            self.phase = StoryPhase.RECOVERY
            self.phase_time = 0.0

    def opening_enemies(self, sprites):
        enemies = [self.boss]
        for kind, x, y in [('normal', WIDTH - 100, HEIGHT - 75),
                           ('normal', 70, 110), ('interceptor', WIDTH - 180, 70)]:
            escort = Enemy(x, y, kind)
            sprites.prepare_enemy(escort, allow_boss=False)
            enemies.append(escort)
        return enemies

    def update_boss(self, dt, player, firing, audio):
        if dt > 0:
            self.player_velocity = (player.position - self.last_player_position) / dt
        self.last_player_position.update(player.position)
        changed = self.boss_ai.record_player(dt, player.position, firing, self.boss.health, self.boss.max_health)
        if changed:
            audio.play('warning')
        if player.position.distance_to(self.boss.position) > 260:
            self.boss.update(dt, player.position, self.boss_ai.strategy, self.boss_ai.phase)
        arena = pygame.Rect(0, 0, WIDTH, HEIGHT)
        if not arena.contains(self.boss.rect):
            self.boss.rect.clamp_ip(arena)
            self.boss.position.update(self.boss.rect.center)
        charge_end = self.charge_start + self.charge_duration
        if self.charge_start <= self.phase_time < charge_end:
            self.shot_timer = charge_end - self.phase_time
        else:
            self.shot_timer -= dt

    def aim_boss_shot(self, player):
        offset = player.position - self.boss.position
        if self.phase_time < self.charge_start:
            self.shot_timer = self.opening_shot_interval
            return offset
        velocity = self.player_velocity
        speed = self.boss_bullet_speed
        closing = speed * speed - velocity.length_squared()
        if closing > 0:
            projection = offset.dot(velocity)
            lead_time = (projection + math.sqrt(projection ** 2 + closing * offset.length_squared())) / closing
            target = player.position + velocity * lead_time
            target.x = max(0, min(WIDTH, target.x))
            target.y = max(0, min(HEIGHT, target.y))
            offset = target - self.boss.position
        self.shot_timer = self.charged_shot_interval
        return offset

    def update_shield(self, bullets):
        self.shielded = any(
            bullet.position.distance_squared_to(self.boss.position) <= 82 ** 2
            and bullet.direction.dot(self.boss.position - bullet.position) > 0
            for bullet in bullets
        )

    def hit_boss(self, impact, effects, audio):
        if self.shielded:
            if self.shield_flash <= 0:
                audio.play('core_shield')
            self.shield_flash = 0.22
            effects.sparks(impact, 9, (140, 235, 255))
        else:
            self.boss.take_damage(1)
            effects.hit_enemy(self.boss)
            if self.boss.health <= 2:
                self.boss.health = self.boss.max_health
                self.repair_timer = 0.85
                effects.sparks(self.boss.position, 22, (92, 255, 158))
                audio.play('core_repair')

    def finish_opening(self, player, enemies, bullets, enemy_bullets, effects, audio):
        if self.phase != StoryPhase.OPENING:
            return False
        if self.phase_time < self.opening_duration:
            return False
        self.phase = StoryPhase.SCRIPTED_DEFEAT
        self.phase_time = 0.0
        self.ship.centre.update(player.position)
        self.ship.update(0)
        self.ship.explode()
        self.part_origins = [part.position.copy() for part in self.ship.parts[1:]]
        self.wreckage = scatter_wreckage(self.debris_source, player.position, self.ship.angle)
        effects.sparks(player.position, 32, (255, 170, 70))
        effects.shake = 12
        effects.hit_overlay_timer = 0.28
        audio.play('enemy_down')
        for enemy in enemies:
            image = enemy.ship_image
            if image is None:
                image = pygame.Surface(enemy.rect.size, pygame.SRCALPHA)
                pygame.draw.polygon(image, (230, 105, 95), [(0, 0), (image.get_width()-1, image.get_height()//2),
                                                           (0, image.get_height()-1)])
            self.departing_ships.append((pygame.transform.smoothscale(image, enemy.rect.size), enemy.position.copy()))
        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()
        player.rect.size = self.cockpit_hitbox
        player.rect.center = player.position
        return True

    def update_ship(self, player, aim, dt, effects):
        self.ship.centre.update(player.position)
        if self.controls_enabled:
            direction = pygame.Vector2(aim) - player.position
            if direction.length_squared() > 0:
                self.ship.angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
        self.ship.update(dt)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT or self.part_origins:
            progress = min(1, self.phase_time / self.scatter_duration) if self.phase == StoryPhase.SCRIPTED_DEFEAT else 1
            for part, origin, (x,y) in zip(self.ship.parts[1:], self.part_origins, self.part_locations):
                part.position = origin.lerp((WIDTH * x, HEIGHT * y), 1 - (1 - progress) ** 3)
                part.velocity.update(0, 0)
            if progress == 1:
                self.part_origins.clear()
        if self.phase == StoryPhase.RECOVERY and self.recovery_step == RecoveryStep.RETURNING:
            part_id = self.objective_index + 1

            if self.ship.parts[part_id].attached and part_id not in self.rewarded_parts:
                objective = self.objectives[self.objective_index]

                self.rewarded_parts.add(part_id)
                self.recovered_upgrades.add(objective['upgrade'])
                self.active_debuffs.discard(objective['debuff']) #using the discard method instead of remove to prevent a keyerror
                self.pending_rewards += 1
                self.recovery_step = RecoveryStep.INTERMISSION
                self.intermission_timer = self.intermission_duration
                
        if self.phase == StoryPhase.RECOVERY and self.ship.state == 'intact' and player.rect.size != self.assembled_hitbox:
            player.rect.size = self.assembled_hitbox
            player.rect.center = player.position
            effects.sparks(self.ship.centre, 16, (95, 210, 255))
            effects.shake = max(effects.shake, 5)

    def draw_boss_defences(self, surface):
        progress = (self.phase_time - self.charge_start) / self.charge_duration
        if 0 <= progress < 1:
            draw_gun_charge(surface, self.boss.position, self.last_player_position, progress)
        if self.repair_timer > 0:
            self.hud.draw_repair(surface, self.boss.position, self.repair_timer / 0.85)
        if self.shielded:
            draw_shield(surface, self.boss.rect.center, self.phase_time, self.shield_flash)

    def draw_ship(self, surface):
        for fragment in self.wreckage:
            fragment.draw(surface)
        if self.phase == StoryPhase.RECOVERY:
            for part_id, part in enumerate(self.ship.parts[1:], 1):
                if not part.attached and not part.returning:
                    unlocked = self.recovery_step == RecoveryStep.PICKUP and part_id == self.objective_index + 1
                    self.hud.draw_part_marker(surface, part.position, self.ship.centre, self.phase_time, unlocked)
        self.ship.draw(surface)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT:
            self.hud.draw_departure(surface, self.departing_ships, self.phase_time)
            frame = int(self.phase_time / self.explosion_frame_time)
            if frame < len(self.explosion_frames):
                image = self.explosion_frames[frame]
                surface.blit(image, image.get_rect(center=self.ship.centre))

    def resource_limits(self, health_limit, ammo_limit):
        if 'REINFORCED_ARMOUR' in self.recovered_upgrades:
            health_limit += 1
        if 'HULL_BREACH' in self.active_debuffs:
            health_limit -= 1
        if 'EXPANDED_MAGAZINE' in self.recovered_upgrades:
            ammo_limit += 4
        if 'AMMO_LEAK' in self.active_debuffs:
            ammo_limit -= 5
        return max(1, health_limit), max(1, ammo_limit)

    def draw_hud(self, screen, player, ammo, health_limit, ammo_limit, debuff, description):
        self.hud.draw(screen, self, player.health, ammo, health_limit, ammo_limit, debuff, description)

    def update_objective(self, dt, player):
        if self.phase != StoryPhase.RECOVERY:
            return

        if self.recovery_step == RecoveryStep.INTERMISSION:
            self.intermission_timer = max(0, self.intermission_timer - dt)
            if self.intermission_timer > 0:
                return
            if self.objective_index == len(self.objectives) - 1:
                self.phase = StoryPhase.RECOVERY_COMPLETE
                return

            self.objective_index += 1
            self.objective_progress = 0
            self.objective_timer = 0.0
            self.recovery_step = RecoveryStep.OBJECTIVE

        if self.recovery_step == RecoveryStep.OBJECTIVE:
            self.objective_timer += dt

    def record_kill(self,enemy, audio):
        if self.phase != StoryPhase.RECOVERY:
            return
        if self.recovery_step != RecoveryStep.OBJECTIVE:
            return
        if self.objective_index >= len(self.objectives):
            return
        objective = self.objectives[self.objective_index]
        if objective['type'] != 'kill':
            return
        if enemy not in self.wave_active_enemies:
            return

        self.wave_active_enemies.remove(enemy)
        self.objective_progress += 1

        if (self.objective_progress >= objective['target']
                and self.wave_spawn_index == len(objective['enemies'])
                and not self.wave_active_enemies):
            self.recovery_step = RecoveryStep.PICKUP
            self.wave_clear_timer = 2.0
            audio.play('wave_clear')

    def update_pickup(self,player, audio):
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
                audio.play('part_pickup')
                self.ship.recover_part(part_id)
                self.recovery_step = RecoveryStep.RETURNING

    def retry_wave(self):
        self.spawned_objective_index = -1
        self.objective_progress = 0
        self.objective_timer = 0.0
        self.recovery_step = RecoveryStep.OBJECTIVE
        self.wave_clear_timer = 0.0

    def spawn_recovery_enemies(self, enemies, ship_sprites, player, dt, effects, audio):
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
            self.wave_active_limit = (2, 3, 3, 3, 4, 4)[self.objective_index]
            self.wave_spawn_interval = (1.35, 1.30, 1.25, 1.20, 1.15, 1.10)[self.objective_index]
            self.wave_spawn_timer = 0.0
            self.wave_active_enemies = []

            self.active_debuffs.clear()
            self.active_debuffs.add(objective['debuff'])
            effects.malfunction_changed(objective['debuff'])
            audio.play('wave_fault')

        self.wave_spawn_timer += dt

        if self.wave_spawn_index >= len(objective['enemies']):
            return
        if self.wave_spawn_timer < self.wave_spawn_interval:
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
        position_index = self.wave_spawn_index % 3
        x,y = spawn_positions[position_index]

        enemy_type = objective['enemies'][self.wave_spawn_index]
        enemy = Enemy(x, y, enemy_type)
        ship_sprites.prepare_enemy(enemy,allow_boss=False)

        enemies.append(enemy)
        self.wave_active_enemies.append(enemy)
        self.wave_spawn_index += 1
        self.wave_spawn_timer = 0.0