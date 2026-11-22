import math
import random
from enum import Enum, auto #cool library for game states

import pygame

from boss_ai import BossAI
from difficulty import STORY_DIFFICULTIES
from story_visuals import StoryHUD, scatter_wreckage, draw_shield, draw_gun_charge
from enemy import Enemy
from settings import WIDTH, HEIGHT
from ship_parts import ModularShip, load_explosion_frames


class StoryPhase(Enum):
    OPENING = auto()
    SCRIPTED_DEFEAT = auto()
    RECOVERY = auto()
    RECOVERY_COMPLETE = auto()
    FINAL_BOSS = auto()
    VICTORY = auto()
    SURVIVAL = auto()
    SURVIVAL_COMPLETE = auto()

class RecoveryStep(Enum):
    OBJECTIVE = auto()
    PICKUP = auto()
    RETURNING = auto()
    INTERMISSION = auto()

class StoryMode:
    boss_bullet_speed = 315
    charge_start = 6.0
    charge_duration = 1.5
    opening_shot_interval = 1.2
    charged_shot_interval = 0.65
    opening_follow_distance = 240
    opening_pursuit_start = 14.0
    opening_rapid_fire_start = 8.0
    final_shot_interval = 1.8
    final_charged_shot_interval = 0.95
    survival_duration = 35.0
    survival_retreat_duration = 2.65
    survival_shield_cycle = 6.0
    survival_shield_duration = 1.0
    defeat_duration = 2.15
    scatter_duration = 0.95
    explosion_frame_time = 0.048
    assembled_hitbox = (64, 64)
    cockpit_hitbox = (44, 44)

    def __init__(self, player, ship_sprites, difficulty='hard'):
        self.difficulty_settings = STORY_DIFFICULTIES[difficulty]
        self.opening_rapid_shot_interval = self.difficulty_settings['opening_rapid_shot_interval']
        self.phase = StoryPhase.OPENING
        self.phase_time = 0.0
        self.boss_ai = BossAI()
        self.boss = Enemy(WIDTH - 75, 110, 'adaptive core')
        self.boss.ship_image = ship_sprites.adaptive_image
        self.boss.is_boss = True
        self.boss.is_adaptive_boss = True
        self.boss.health = self.boss.max_health = 9
        self.boss.speed = player.speed
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
        self.hull_loss_time = 0.0
        self.hull_loss_duration = max(1.15, len(self.explosion_frames) * self.explosion_frame_time)
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
                'enemies': ['normal', 'interceptor', 'normal', 'interceptor', 'normal'],
                'target': 5,
                'debuff': 'DAMAGED_THRUSTERS',
                'upgrade': 'ENHANCED_THRUSTERS',
                'description': 'Wave 1: Defeat 5 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'interceptor', 'normal', 'ranger', 'interceptor', 'normal', 'interceptor'],
                'target': 7,
                'debuff': 'TARGETING_GLITCH',
                'upgrade': 'TARGETING_COMPUTER',
                'description': 'Wave 2: Defeat 7 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['interceptor', 'normal', 'ranger', 'interceptor', 'normal', 'interceptor', 'ranger', 'normal'],
                'target': 8,
                'debuff': 'REVERSED',
                'upgrade': 'REINFORCED_ARMOUR',
                'description': 'Wave 3: Defeat 8 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['normal', 'ranger', 'interceptor', 'tank', 'interceptor', 'ranger', 'normal', 'interceptor', 'ranger'],
                'target': 9,
                'debuff': 'ENGINE_STALLING',
                'upgrade': 'EXPANDED_MAGAZINE',
                'description': 'Wave 4: Defeat 9 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['interceptor', 'ranger', 'normal', 'interceptor', 'ranger', 'tank', 'interceptor', 'ranger', 'interceptor', 'normal'],
                'target': 10,
                'debuff': 'SHIELD_MALFUNCTION',
                'upgrade': 'SALVAGE_MODULE',
                'description': 'Wave 5: Defeat 10 enemies'
            },
            {
                'type': 'kill',
                'enemies': ['interceptor', 'ranger', 'tank', 'normal', 'interceptor', 'ranger', 'interceptor', 'tank', 'ranger', 'normal', 'interceptor', 'ranger'],
                'target': 12,
                'debuff': 'WEAPON_OVERHEATING',
                'upgrade': 'OVERCLOCKED_WEAPONS',
                'description': 'Wave 6: Defeat 12 enemies'
            }
        ]

        for index, target in enumerate(self.difficulty_settings['wave_targets']):
            objective = self.objectives[index]
            objective['enemies'] = objective['enemies'][:target]
            objective['target'] = target
            objective['description'] = f'Wave {index + 1}: Defeat {target} enemies'

        self.spawned_objective_index = -1
        self.wave_spawn_index = 0
        self.wave_spawn_timer = 0.0
        self.wave_spawn_interval = self.difficulty_settings['wave_spawn_intervals'][0]
        self.wave_active_limit = self.difficulty_settings['wave_active_limits'][0]
        self.wave_active_enemies = []
        self.intermission_duration = 1.5
        self.intermission_timer = 0.0
        self.final_boss_phase = 0
        self.final_boss_started = False
        self.fury_started = False
        self.fury_boss_locked = False
        self.final_enemy_queue = []
        self.final_minions = []
        self.final_spawn_timer = 0.0
        self.survival_spawn_index = 0
        self.survival_cleared_early = False
        self.minibosses_defeated = set()
        self.module_notice = ''
        self.module_notice_timer = 0.0
        self.rift_drive_cooldown = 0.0
        self.phase_cloak_timer = 0.0
        self.phase_cloak_cooldown = 0.0
    @property #decorator- allows controls_enabled to behave like an attribute instead of a method
    def controls_enabled(self):
        return self.phase not in (StoryPhase.SCRIPTED_DEFEAT, StoryPhase.VICTORY, StoryPhase.SURVIVAL_COMPLETE)

    def advance(self, dt, effects, audio):
        self.phase_time += dt
        self.repair_timer = max(0, self.repair_timer - dt)
        self.wave_clear_timer = max(0, self.wave_clear_timer - dt)
        self.shield_flash = max(0, self.shield_flash - dt)
        self.module_notice_timer = max(0, self.module_notice_timer - dt)
        self.rift_drive_cooldown = max(0, self.rift_drive_cooldown - dt)
        self.phase_cloak_timer = max(0, self.phase_cloak_timer - dt)
        self.phase_cloak_cooldown = max(0, self.phase_cloak_cooldown - dt)
        for fragment in self.wreckage:
            fragment.update(dt)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT and self.phase_time >= self.defeat_duration:
            self.departing_ships.clear()
            self.phase = StoryPhase.RECOVERY
            self.phase_time = 0.0
        if self.phase == StoryPhase.SURVIVAL_COMPLETE and self.phase_time >= self.survival_retreat_duration:
            self.departing_ships.clear()

    def opening_enemies(self, sprites):
        enemies = [self.boss]
        for kind, x, y in [('normal', WIDTH - 100, HEIGHT - 75),
                           ('normal', 70, 110), ('interceptor', WIDTH - 180, 70)]:
            escort = Enemy(x, y, kind)
            sprites.prepare_enemy(escort, allow_boss=False)
            enemies.append(escort)
        return enemies

    def update_boss(self, dt, player, firing, audio):
        if self.phase == StoryPhase.VICTORY:
            return
        if self.phase == StoryPhase.SURVIVAL:
            self.shielded = self.phase_time % self.survival_shield_cycle < self.survival_shield_duration
        if dt > 0:
            self.player_velocity = (player.position - self.last_player_position) / dt
        self.last_player_position.update(player.position)
        changed = self.boss_ai.record_player(dt, player.position, firing, self.boss.health, self.boss.max_health)
        if changed and self.phase == StoryPhase.OPENING:
            audio.play('warning')
        if self.phase == StoryPhase.OPENING:
            if self.phase_time >= self.opening_pursuit_start:
                self.boss.speed = player.speed * 1.1
                self.boss.update(dt, player.position)
            elif player.position.distance_to(self.boss.position) > self.opening_follow_distance:
                self.boss.update(dt, player.position)
        elif player.position.distance_to(self.boss.position) > 260:
            movement_phase = self.final_boss_phase if self.phase == StoryPhase.FINAL_BOSS else self.boss_ai.phase
            self.boss.update(dt, player.position, self.boss_ai.strategy, movement_phase)
        arena = pygame.Rect(0, 0, WIDTH, HEIGHT)
        if not arena.contains(self.boss.rect):
            self.boss.rect.clamp_ip(arena)
            self.boss.position.update(self.boss.rect.center)
        charge_end = self.charge_start + self.charge_duration
        if self.charge_start <= self.phase_time < charge_end:
            self.shot_timer = charge_end - self.phase_time
        else:
            if self.phase == StoryPhase.OPENING and self.phase_time >= self.opening_rapid_fire_start:
                self.shot_timer = min(self.shot_timer, self.opening_rapid_shot_interval)
            self.shot_timer -= dt

    def aim_boss_shot(self, player):
        offset = player.position - self.boss.position
        if self.phase_time < self.charge_start:
            self.shot_timer = self.opening_shot_interval if self.phase == StoryPhase.OPENING else self.final_shot_interval
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
        if self.phase == StoryPhase.OPENING:
            self.shot_timer = self.opening_rapid_shot_interval if self.phase_time >= self.opening_rapid_fire_start else self.charged_shot_interval
        else:
            self.shot_timer = self.final_charged_shot_interval
        return offset

    def update_shield(self, bullets):
        self.shielded = any(
            bullet.position.distance_squared_to(self.boss.position) <= 82 ** 2
            and bullet.direction.dot(self.boss.position - bullet.position) > 0
            for bullet in bullets
        )

    def hit_boss(self, impact, effects, audio):
        if self.shielded or (self.phase == StoryPhase.FINAL_BOSS
                             and (self.final_boss_phase < 3 or self.fury_boss_locked)):
            if self.shield_flash <= 0:
                audio.play('core_shield')
            self.shield_flash = 0.22
            effects.sparks(impact, 9, (140, 235, 255))
        else:
            self.boss.take_damage(1)
            effects.hit_enemy(self.boss)
            if self.phase == StoryPhase.FINAL_BOSS and self.boss.health <= 0:
                self.boss.health = 0
                self.phase = StoryPhase.VICTORY
                self.phase_time = 0.0
                audio.play('wave_clear')
                return True
            if self.phase == StoryPhase.OPENING and self.boss.health <= 2:
                self.boss.health = self.boss.max_health
                self.repair_timer = 0.85
                effects.sparks(self.boss.position, 22, (92, 255, 158))
                audio.play('core_repair')
            if (self.phase == StoryPhase.FINAL_BOSS and self.final_boss_phase == 3
                    and not self.fury_started and self.boss.health / self.boss.max_health < 0.25):
                return 'FURY'
        return False

    def start_final_boss(self, enemies, bullets, enemy_bullets, audio, survival=False):
        if self.final_boss_started:
            return
        self.final_boss_started = True
        self.phase = StoryPhase.SURVIVAL if survival else StoryPhase.FINAL_BOSS
        self.phase_time = 0.0
        self.final_boss_phase = 1
        self.boss.position.update(WIDTH - 100, HEIGHT // 2)
        self.boss.rect.size = (84, 84)
        self.boss.rect.center = self.boss.position
        self.boss.speed = 78
        self.boss.health = self.boss.max_health = self.difficulty_settings['survival_boss_health'] if survival else 32
        self.shielded = survival
        self.repair_timer = 0.0
        self.boss.is_boss = True
        self.boss.is_adaptive_boss = True
        enemies.clear()
        enemies.append(self.boss)
        bullets.clear()
        enemy_bullets.clear()
        self.final_enemy_queue = ['normal', 'bomber', 'normal', 'bomber', 'normal']
        self.final_minions.clear()
        self.final_spawn_timer = 0.4
        self.survival_spawn_index = 0
        self.shot_timer = self.final_shot_interval
        self.boss_ai.reset()
        audio.play('boss_spawn')

    def begin_fury(self, enemies, bullets, enemy_bullets, ship_sprites, audio, effects):
        if self.fury_started:
            return
        self.fury_started = True
        self.fury_boss_locked = True
        self.final_boss_phase = 4
        self.final_enemy_queue = []
        self.final_minions.clear()
        enemies[:] = [enemy for enemy in enemies if enemy is self.boss]
        bullets.clear()
        enemy_bullets.clear()
        for kind, position in (
            ('rift_stalker', (75, 75)),
            ('siege_walker', (WIDTH - 75, 75)),
            ('phase_wraith', (WIDTH // 2, HEIGHT - 75)),
        ):
            mini = Enemy(*position, kind)
            ship_sprites.prepare_enemy(mini, allow_boss=False)
            mini.is_story_miniboss = True
            mini.miniboss_kind = kind
            self.final_minions.append(mini)
            enemies.append(mini)
        self.module_notice = 'FURY MODE: THREE MINIBOSSES'
        self.module_notice_timer = 4.0
        self.shield_flash = 0.8
        effects.shake = max(effects.shake, 9)
        effects.sparks(self.boss.position, 30, (180, 105, 255))
        audio.play('boss_phase')

    def update_final_encounter(self, dt, enemies, ship_sprites, player, audio):
        if self.phase != StoryPhase.FINAL_BOSS:
            return
        self.final_spawn_timer -= dt
        self.final_minions = [enemy for enemy in self.final_minions if enemy in enemies]

        if self.final_boss_phase in (1, 2):
            if self.final_spawn_timer <= 0 and self.final_enemy_queue and len(self.final_minions) < 2:
                kind = self.final_enemy_queue.pop(0)
                enemy = self._spawn_final_enemy(kind, player, ship_sprites)
                enemies.append(enemy)
                self.final_minions.append(enemy)
                self.final_spawn_timer = 1.25 if self.final_boss_phase == 1 else 1.45
            if not self.final_enemy_queue and not self.final_minions:
                self.final_boss_phase += 1
                self.final_spawn_timer = 1.0
                if self.final_boss_phase == 2:
                    self.final_enemy_queue = ['tank', 'interceptor', 'tank', 'interceptor']
                    self.module_notice = 'PHASE 2: HEAVY ASSAULT'
                    self.module_notice_timer = 2.5
                else:
                    self.boss.health = self.boss.max_health = 32
                    self.final_enemy_queue = []
                    self.module_notice = 'PHASE 3: CORE EXPOSED'
                    self.module_notice_timer = 3.0
                audio.play('boss_phase')
        elif self.final_boss_phase == 3:
            if self.final_spawn_timer <= 0 and len(self.final_minions) < 2:
                kind = random.choice(('normal', 'interceptor', 'bomber'))
                enemy = self._spawn_final_enemy(kind, player, ship_sprites)
                enemies.append(enemy)
                self.final_minions.append(enemy)
                self.final_spawn_timer = 4.2
        elif self.final_boss_phase == 4 and not self.final_minions and len(self.minibosses_defeated) == 3:
            self.fury_boss_locked = False
            self.final_boss_phase = 3
            self.module_notice = 'MINIBOSSES DEFEATED — CORE EXPOSED'
            self.module_notice_timer = 3.0
            audio.play('boss_phase')

    def update_survival_spawns(self, dt, enemies, ship_sprites, player):
        if self.boss not in enemies or self.phase_time >= self.survival_duration:
            return
        if self.phase_time < 10.0:
            interval, limit = 1.8, 4
            kinds = ('normal', 'interceptor', 'normal', 'ranger')
        elif self.phase_time < self.survival_duration - 10.0:
            interval, limit = 1.2, 6
            kinds = ('tank', 'ranger', 'bomber', 'interceptor', 'normal', 'bomber')
        else:
            interval, limit = 0.75, 8
            kinds = ('tank', 'bomber', 'ranger', 'interceptor', 'bomber', 'ranger', 'normal')

        interval *= self.difficulty_settings['survival_spawn_interval_multiplier']
        limit -= self.difficulty_settings['survival_active_limit_reduction']
        self.final_spawn_timer = min(self.final_spawn_timer, interval) - dt
        regular_count = len(enemies) - 1
        if self.final_spawn_timer <= 0 and regular_count < limit:
            kind = kinds[self.survival_spawn_index % len(kinds)]
            enemies.append(self._spawn_final_enemy(kind, player, ship_sprites))
            self.survival_spawn_index += 1
            self.final_spawn_timer += interval
        self.final_spawn_timer = max(0.0, self.final_spawn_timer)

    def finish_survival(self, enemies, bullets, enemy_bullets, effects, audio):
        self.survival_cleared_early = self.phase_time < self.survival_duration
        self.phase = StoryPhase.SURVIVAL_COMPLETE
        self.phase_time = 0.0
        self.queue_departures(enemies)
        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()
        if self.survival_cleared_early:
            message = 'Core and hostiles cleared'
        elif self.departing_ships:
            message = 'Hostiles are withdrawing'
        else:
            message = f'{self.survival_duration:.0f} seconds survived'
        effects.announce_objective('SURVIVAL COMPLETE', message)
        audio.play('wave_clear')

    def _spawn_final_enemy(self, kind, player, ship_sprites):
        positions = [(70, 70), (WIDTH - 70, 70), (70, HEIGHT - 70), (WIDTH - 70, HEIGHT - 70)]
        if self.phase == StoryPhase.SURVIVAL:
            index = self.survival_spawn_index % len(positions)
            positions = positions[index:] + positions[:index]
            x, y = next((point for point in positions if player.position.distance_to(point) >= 140), positions[0])
        else:
            x, y = max(positions, key=lambda point: player.position.distance_to(point))
        enemy = Enemy(x, y, kind)
        ship_sprites.prepare_enemy(enemy, allow_boss=False)
        return enemy

    def record_final_kill(self, enemy, audio, effects):
        if enemy not in self.final_minions:
            return
        self.final_minions.remove(enemy)
        if not getattr(enemy, 'is_story_miniboss', False):
            return
        rewards = {
            'rift_stalker': ('RIFT_DRIVE', 'RIFT DRIVE ONLINE'),
            'siege_walker': ('SIEGE_CANNON', 'SIEGE CANNON ONLINE'),
            'phase_wraith': ('PHASE_CLOAK', 'PHASE CLOAK ONLINE'),
        }
        upgrade, notice = rewards[enemy.miniboss_kind]
        self.recovered_upgrades.add(upgrade)
        self.minibosses_defeated.add(enemy.miniboss_kind)
        self.module_notice = notice
        self.module_notice_timer = 3.0
        audio.play('part_attached')
        effects.sparks(enemy.position, 20, (110, 244, 235))

    def finish_opening(self, player, enemies, bullets, enemy_bullets, effects, audio):
        if self.phase != StoryPhase.OPENING:
            return False
        if player.health > 0:
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
        self.queue_departures(enemies)
        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()
        player.rect.size = self.cockpit_hitbox
        player.rect.center = player.position
        return True

    def queue_departures(self, enemies):
        for enemy in enemies:
            image = enemy.ship_image
            if image is None:
                image = pygame.Surface(enemy.rect.size, pygame.SRCALPHA)
                pygame.draw.polygon(image, (230, 105, 95), [(0, 0), (image.get_width()-1, image.get_height()//2),
                                                           (0, image.get_height()-1)])
            self.departing_ships.append((pygame.transform.smoothscale(image, enemy.rect.size), enemy.position.copy()))

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
        if (self.shielded or (self.phase == StoryPhase.FINAL_BOSS
                              and (self.final_boss_phase < 3 or self.fury_boss_locked))):
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
        module_colours = {
            'RIFT_DRIVE': (155, 105, 255),
            'SIEGE_CANNON': (255, 150, 75),
            'PHASE_CLOAK': (85, 230, 235),
        }
        module_offsets = {
            'RIFT_DRIVE': pygame.Vector2(-29, 21),
            'SIEGE_CANNON': pygame.Vector2(0, -28),
            'PHASE_CLOAK': pygame.Vector2(29, 21),
        }
        for module, colour in module_colours.items():
            if module in self.recovered_upgrades:
                centre = self.ship.centre + module_offsets[module].rotate(-self.ship.angle)
                points = [centre + pygame.Vector2(0, -7).rotate(-self.ship.angle),
                          centre + pygame.Vector2(6, 6).rotate(-self.ship.angle),
                          centre + pygame.Vector2(-6, 6).rotate(-self.ship.angle)]
                pygame.draw.polygon(surface, colour, points)
                pygame.draw.polygon(surface, (235, 250, 255), points, 1)
        if self.phase == StoryPhase.SCRIPTED_DEFEAT:
            self.hud.draw_departure(surface, self.departing_ships, self.phase_time)
            self.draw_explosion(surface, self.ship.centre, self.phase_time)
        elif self.phase == StoryPhase.SURVIVAL_COMPLETE and self.departing_ships:
            self.hud.draw_departure(surface, self.departing_ships, self.phase_time)

    def draw_explosion(self, surface, position, age):
        frame = int(age / self.explosion_frame_time)
        if frame < len(self.explosion_frames):
            image = self.explosion_frames[frame]
            surface.blit(image, image.get_rect(center=position))

    def animate_hull_loss(self, surface, player, dt, effects, audio):
        if self.hull_loss_time == 0.0:
            self.wreckage = scatter_wreckage(self.debris_source, player.position, self.ship.angle)
            effects.sparks(player.position, 32, (255, 170, 70))
            audio.play('enemy_down')
        for fragment in self.wreckage:
            fragment.update(dt)
            fragment.draw(surface)
        self.draw_explosion(surface, player.position, self.hull_loss_time)
        self.hull_loss_time += dt

    def resource_limits(self, health_limit, ammo_limit):
        if 'REINFORCED_ARMOUR' in self.recovered_upgrades:
            health_limit += 1
        if 'EXPANDED_MAGAZINE' in self.recovered_upgrades:
            ammo_limit += 4
        return max(1, health_limit), max(1, ammo_limit)

    def progress_percent(self):
        if self.phase in (StoryPhase.SURVIVAL_COMPLETE, StoryPhase.VICTORY):
            return 100
        if self.phase == StoryPhase.OPENING:
            return 0
        completed = 1 + len(self.rewarded_parts)
        if self.phase == StoryPhase.RECOVERY and self.objective_index + 1 not in self.rewarded_parts:
            target = self.objectives[self.objective_index]['target']
            completed += self.objective_progress / (target + 1)
        elif self.phase == StoryPhase.SURVIVAL:
            completed += self.phase_time / self.survival_duration
        return min(99, int(100 * completed / (len(self.objectives) + 2)))

    def draw_hud(self, screen, player, ammo, health_limit, ammo_limit, debuff, description, heat_percent, overheated):
        self.hud.draw(screen, self, player.health, ammo, health_limit, ammo_limit, debuff, description, heat_percent, overheated)

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
                return True

    def retry_wave(self):
        self.hull_loss_time = 0.0
        self.wreckage.clear()
        if self.phase == StoryPhase.SURVIVAL:
            self.phase = StoryPhase.RECOVERY_COMPLETE
            self.phase_time = 0.0
            self.final_boss_started = False
            self.rift_drive_cooldown = 0.0
            self.phase_cloak_timer = 0.0
            self.phase_cloak_cooldown = 0.0
            return
        if self.phase == StoryPhase.FINAL_BOSS:
            self.final_boss_started = False
            self.final_boss_phase = 1
            self.fury_started = False
            self.fury_boss_locked = False
            self.minibosses_defeated.clear()
            self.final_enemy_queue = []
            self.final_minions.clear()
            self.final_spawn_timer = 0.0
            self.boss.health = self.boss.max_health = 32
            self.boss_ai.reset()
            self.shot_timer = self.final_shot_interval
            self.phase_time = 0.0
            self.rift_drive_cooldown = 0.0
            self.phase_cloak_timer = 0.0
            self.phase_cloak_cooldown = 0.0
            return
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
            self.wave_active_limit = self.difficulty_settings['wave_active_limits'][self.objective_index]
            self.wave_spawn_interval = self.difficulty_settings['wave_spawn_intervals'][self.objective_index]
            self.wave_spawn_timer = 0.0
            self.wave_active_enemies = []

            self.active_debuffs.clear()
            self.active_debuffs.add(objective['debuff'])
            debuff_name = objective['debuff'].replace('_', ' ')
            if objective['debuff'] == 'REVERSED':
                debuff_name = 'INVERTED CONTROLS'
            effects.announce_objective(f'SURVIVE WAVE {self.objective_index + 1}',
                                       f"Defeat {objective['target']} enemies  |  {debuff_name}")
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