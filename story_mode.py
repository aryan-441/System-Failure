import math
import random
from pathlib import Path
from enum import Enum, auto #cool library for game states

import pygame

from bullet import Bullet
from boss_ai import BossAI
from difficulty import STORY_DIFFICULTIES
from story_visuals import StoryHUD, scatter_wreckage, draw_shield, draw_gun_charge, draw_collector_assembly
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
    RETURNING_CORES = auto()
    SECOND_DEFEAT = auto()
    COLLECTOR_FORMATION = auto()
    COLLECTOR_FIGHT = auto()
    RETURN_TO_BASE = auto()
    DOCKING = auto()


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
    opening_pursuit_start = 14.0
    opening_rapid_fire_start = 8.0
    final_shot_interval = 1.8
    final_charged_shot_interval = 0.95
    survival_duration = 35.0
    survival_retreat_duration = 2.65
    retreating_attack_duration = 15.0
    returning_charge_duration = 1.5
    returning_damage_cooldown = 2.2
    survival_shield_cycle = 9.0
    survival_shield_duration = 5.0
    defeat_duration = 2.15
    scatter_duration = 0.95
    explosion_frame_time = 0.048
    assembled_hitbox = (64, 64)
    cockpit_hitbox = (44, 44)
    collector_speeds = (56, 77, 100)
    collector_shields = ((7.2, 2.5), (6.3, 2.75), (5.4, 3.0))
    collector_fire_intervals = (2.15, 1.72, 1.45)
    collector_bullet_speeds = (195, 235, 265)
    collector_windup = 0.65
    collector_spawn_intervals = (2.8, 2.35, 1.9)
    collector_minions = (('normal', 'interceptor', 'normal'),
                         ('ranger', 'normal', 'tank', 'interceptor'),
                         ('bomber', 'ranger', 'interceptor', 'tank', 'normal'))
    collector_faults = (('DAMAGED_THRUSTERS', 'TARGETING_GLITCH'),
                        ('WEAPON_OVERHEATING', 'ENGINE_STALLING', 'TARGETING_GLITCH'),
                        ('REVERSED', 'SHIELD_MALFUNCTION', 'ENGINE_STALLING', 'WEAPON_OVERHEATING'))
    collector_player_start = (WIDTH // 2, HEIGHT - 100)
    dock_align_duration = 1.3
    dock_fade_duration = 0.8

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
        self.hull_loss_duration = max(1.4, len(self.explosion_frames) * self.explosion_frame_time + 0.35)
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

        self.returning_cores = []
        self.returning_volley_fired = False
        self.collector = None
        self.collector_phase = 1
        self.dock_position = pygame.Vector2(WIDTH - 80, HEIGHT // 2)
        dock = ship_sprites.load_image(Path(__file__).parent / 'assets' / 'images', 'docking_station')
        self.dock_images = (dock, pygame.transform.flip(dock, True, False) if dock is not None else None)
        self.collector_formation_started = False
        self.collector_formation_duration = 2.55
        self.collector_centre = pygame.Vector2(WIDTH // 2, HEIGHT // 2 - 60)
        self.collector_entry_times = {}
        self.collector_core_starts = []
        self.collector_part_starts = []
        self.collector_part_angles = []
        self.collector_fragment_starts = []
    @property #decorator- allows controls_enabled to behave like an attribute instead of a method
    def controls_enabled(self):
        return self.phase not in (StoryPhase.SCRIPTED_DEFEAT, StoryPhase.VICTORY, StoryPhase.SURVIVAL_COMPLETE, StoryPhase.SECOND_DEFEAT, StoryPhase.COLLECTOR_FORMATION, StoryPhase.DOCKING)
    

    def advance(self, dt, effects, audio):
        self.phase_time += dt
        self.hud.update_gains(dt)
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

        if self.phase == StoryPhase.SECOND_DEFEAT and self.phase_time >= self.defeat_duration:
            self.phase = StoryPhase.COLLECTOR_FORMATION
            self.phase_time = 0.0
        if (self.phase in (StoryPhase.SURVIVAL_COMPLETE, StoryPhase.RETURN_TO_BASE)
                and self.phase_time >= self.survival_retreat_duration):
            self.departing_ships.clear()

    def opening_enemies(self, sprites):
        enemies = [self.boss]
        for kind, x, y in [('normal', WIDTH - 100, HEIGHT - 75),
                           ('normal', 70, 110), ('interceptor', WIDTH - 180, 70)]:
            escort = Enemy(x, y, kind)
            sprites.prepare_enemy(escort, allow_boss=False)
            enemies.append(escort)
        return enemies

    def create_returning_cores(self, ship_sprites, player):
        self.returning_cores.clear()
        y = 55 if player.position.y >= HEIGHT / 2 else HEIGHT - 55
        left, right = 70, WIDTH - 70
        rammer_x, flanker_x = (left, right) if player.position.x >= WIDTH / 2 else (right, left)
        formation = (
            ('rammer', rammer_x, y, 185),
            ('gunner', WIDTH // 2, y, 190),
            ('flanker', flanker_x, y, 165),
        )
        for role, x, y, speed in formation:
            core = Enemy(x, y, 'adaptive_core')
            core.ship_image = ship_sprites.adaptive_image
            core.is_boss = True
            core.is_adaptive_boss = True
            core.is_story_invulnerable = True
            core.health = core.max_health = 9
            core.role = role
            core.speed = speed
            core.shield_flash = 0.0
            core.fire_timer = 2.0 if role == 'gunner' else 2.8
            core.rect.size = (64, 64)
            core.rect.center = core.position
            self.returning_cores.append(core)

        return self.returning_cores

    def start_returning_cores(self, enemies, bullets, enemy_bullets, ship_sprites, player, effects, audio):
        if self.phase != StoryPhase.SURVIVAL_COMPLETE:
            return

        self.phase  = StoryPhase.RETURNING_CORES
        self.phase_time = 0.0
        self.returning_volley_fired = False

        self.departing_ships.clear()

        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()

        cores = self.create_returning_cores(ship_sprites, player)
        enemies.extend(cores)
        self.module_notice = 'THREE ADAPTIVE CORES INCOMING'
        self.module_notice_timer = 4.0

        effects.announce_objective("CRITICAL THREAT", 'Three Adaptive Cores approaching')
        audio.play('boss_spawn')

    def track_returning_player(self, dt, player):
        if dt > 0:
            velocity = (player.position - self.last_player_position) / dt
            if velocity.length_squared() > player.speed ** 2:
                velocity.scale_to_length(player.speed)
            self.player_velocity = self.player_velocity.lerp(velocity, min(1, dt * 12))
        self.last_player_position.update(player.position)

    def update_returning_core(self, core, dt, player):
        if self.phase != StoryPhase.RETURNING_CORES:
            return

        core.shield_flash = max(0.0, core.shield_flash - dt)
        core.fire_timer -= dt
        target = player.position.copy()
        if core.role == 'gunner':
            # Circle the player while firing, even if the player holds still.
            angle = self.phase_time * 52 - 90
            target += pygame.Vector2(230, 0).rotate(angle)
        elif core.role == 'flanker':
            # Cut across the escape route, then close from the rammer's far side.
            target += self.player_velocity * 0.45
            if self.phase_time % 3.2 < 1.2:
                rammer = self.returning_cores[0]
                far_side = player.position - rammer.position
                if far_side.length_squared() > 0:
                    target += far_side.normalize() * 135

        target.x = max(core.rect.width / 2, min(WIDTH - core.rect.width / 2, target.x))
        target.y = max(core.rect.height / 2, min(HEIGHT - core.rect.height / 2, target.y))
        core.position.move_towards_ip(target, core.speed * dt)
        core.rect.center = core.position

    def aim_returning_core_shot(self, core, player, speed):
        offset = player.position - core.position
        velocity = self.player_velocity
        closing = speed * speed - velocity.length_squared()
        lead = offset.length() / speed
        if closing > 0:
            projection = offset.dot(velocity)
            lead = (projection + math.sqrt(projection ** 2 + closing * offset.length_squared())) / closing
        target = player.position + velocity * min(0.52, lead)
        target.x = max(0, min(WIDTH, target.x))
        target.y = max(0, min(HEIGHT, target.y))
        return target - core.position

    def draw_returning_core_defences(self, surface, core, player, bullets):
        incoming = any(
            bullet.position.distance_squared_to(core.position) <= 96 ** 2
            and bullet.direction.dot(core.position - bullet.position) > 0
            for bullet in bullets
        )
        if core.shield_flash > 0 or incoming:
            draw_shield(surface, core.rect.center, self.phase_time, core.shield_flash)
        charge_start = self.retreating_attack_duration - self.returning_charge_duration
        if self.phase_time >= charge_start:
            progress = min(1.0, (self.phase_time - charge_start) / self.returning_charge_duration)
            draw_gun_charge(surface, core.position, player.position, progress)

    def begin_second_defeat(self,player,bullets,enemy_bullets,effects,audio):
        if self.phase != StoryPhase.RETURNING_CORES:
            return

        self.returning_volley_fired = self.phase_time >= self.retreating_attack_duration and player.health > 0
        self.phase = StoryPhase.SECOND_DEFEAT
        self.phase_time = 0.0

        self.ship.centre.update(player.position)
        self.ship.update(0)
        self.ship.explode()
        self.wreckage = scatter_wreckage(self.debris_source, player.position, self.ship.angle)

        player.health = 1
        player.rect.size = self.cockpit_hitbox

        player.rect.center = player.position
        bullets.clear()
        enemy_bullets.clear()
        effects.sparks(player.position,32,(255,170,70))

        effects.shake = 12
        effects.hit_overlay_timer = 0.28
        if self.returning_volley_fired:
            audio.play('core_shot')
        audio.play('enemy_down')

    def start_collector_formation(self,enemies,bullets,enemy_bullets,player,effects,audio):
        if self.phase != StoryPhase.COLLECTOR_FORMATION or self.collector_formation_started:
            return
        self.collector_formation_started = True
        self.formation_cockpit_start = player.position.copy()
        self.formation_core_image = pygame.transform.smoothscale(self.returning_cores[0].ship_image, (90, 90))
        self.collector_core_starts = [core.position.copy() for core in self.returning_cores]
        self.collector_part_starts = [part.position.copy() for part in self.ship.parts[1:]] #1: to exclude the cockpit
        self.collector_part_angles = [part.angle for part in self.ship.parts[1:]]
        self.collector_fragment_starts = [fragment.position.copy() for fragment in self.wreckage]

        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()

        self.module_notice = 'THE COLLECTOR IS FORMING'
        self.module_notice_timer = self.collector_formation_duration
        effects.shake = max(effects.shake, 8)
        audio.play('boss_phase')

    def update_collector_formation(self):
        if self.phase != StoryPhase.COLLECTOR_FORMATION or not self.collector_formation_started:
            return

        progress = min(1.0, self.phase_time / self.collector_formation_duration)
        eased = progress * progress * (3-2 * progress) #smoothstep func

        for index, core in enumerate(self.returning_cores):
            angle = index *120 + progress * 180
            target = self.collector_centre + pygame.Vector2(0,-35).rotate(angle)

            arc = pygame.Vector2(0, -70).rotate(index * 120 + progress * 130)
            core.position = self.collector_core_starts[index].lerp(target,eased) + arc * math.sin(math.pi * progress)

            core.rect.center = core.position

        for index, part in enumerate(self.ship.parts[1:]):
            angle = index * 60 + progress * 180
            target = self.collector_centre + pygame.Vector2(0,-65).rotate(angle)

            part.position = self.collector_part_starts[index].lerp(target,eased)

            part.angle = self.collector_part_angles[index] + progress * 240

        for index, fragment in enumerate(self.wreckage):
            angle = index * 360 / len(self.wreckage) + progress * 180
            radius = 15 + (index % 6) * 7
            target = self.collector_centre + pygame.Vector2(0,-radius).rotate(angle)

            delay = (index % 5) * 0.045
            travel = max(0, (progress - delay) / (1 - delay))
            fragment.position = self.collector_fragment_starts[index].lerp(target, travel * travel * (3 - 2 * travel))

    def build_collector_image(self):
        size = 176
        image = pygame.Surface((size,size), pygame.SRCALPHA)
        centre = pygame.Vector2(size / 2, size / 2)

        for fragment in self.wreckage:
            rotated = pygame.transform.rotate(fragment.image, fragment.angle)
            position = centre + fragment.position - self.collector_centre
            image.blit(rotated, rotated.get_rect(center=position))

        for part in self.ship.parts[1:]:
            rotated = pygame.transform.rotate(part.image, part.angle)
            position = centre + part.position - self.collector_centre
            image.blit(rotated, rotated.get_rect(center=position))

        for core in self.returning_cores:
            core_image = pygame.transform.smoothscale(core.ship_image, (90,90))
            position = centre + core.position - self.collector_centre
            image.blit(core_image, core_image.get_rect(center=position))

        return image


    def start_collector_fight(self, enemies, player, effects, audio):
        if self.phase != StoryPhase.COLLECTOR_FORMATION:
            return
        if self.phase_time < self.collector_formation_duration:
            return

        self.update_collector_formation()
        image = self.build_collector_image()

        self.collector = Enemy(self.collector_centre.x, self.collector_centre.y, 'collector')
        self.collector.ship_image = image
        self.collector.is_boss = True
        self.collector.rect.size = (104,104)
        self.reset_collector_fight(enemies, player, effects, audio)

    def reset_collector_fight(self, enemies, player, effects, audio):
        self.collector_phase = 1
        self.collector_cycle_time = 0.0
        self.collector_fault_time = 0.0
        self.collector_fault_slot = -1
        self.collector_shot_timer = self.difficulty_settings['collector_interval_multiplier']
        self.collector_volley = 0
        self.collector_aim = pygame.Vector2(0, 1)
        self.collector_pattern = ()
        self.collector_spawn_timer = 0.0
        self.collector_entry_times.clear()
        self.collector_spawn_index = 0
        self.collector_phase_spawn_index = 0
        self.active_debuffs.clear()
        self.shield_flash = 0.0
        self.hull_loss_time = 0.0
        self.phase_cloak_timer = self.phase_cloak_cooldown = self.rift_drive_cooldown = 0.0
        self.collector.position.update(self.collector_centre)
        self.collector.speed = self.collector_speeds[0]
        self.collector.health = self.collector.max_health = 48
        self.collector.rect.center = self.collector.position
        self.collector.hit_flash_timer = 0.0
        self.collector.last_hit = -1000

        enemies.clear()
        enemies.append(self.collector)
        self.wreckage.clear()

        self.phase = StoryPhase.COLLECTOR_FIGHT
        self.phase_time = 0.0

        player.position.update(self.collector_player_start)
        player.recoil_velocity.update(0, 0)
        player.rect.size = self.cockpit_hitbox
        player.rect.center = player.position
        player.health = self.difficulty_settings['collector_cockpit_health']
        self.last_player_position.update(player.position)
        self.player_velocity.update(0, 0)

        self.module_notice = "THE COLLECTOR HAS AWAKENED"
        self.module_notice_timer = 4.0

        effects.shake = max(effects.shake, 12)
        effects.sparks(self.collector.position, 40, (255,100,80)) 
        audio.play('boss_spawn')
    @property
    def collector_shielded(self):
        period, duration = self.collector_shields[self.collector_phase - 1]
        return self.collector_cycle_time >= period - duration

    @property
    def collector_shield_charging(self):
        period, duration = self.collector_shields[self.collector_phase - 1]
        return period - duration - 0.75 <= self.collector_cycle_time < period - duration

    def update_collector_phase(self, effects, audio):
        phase = 3 if self.collector.health <= 16 else 2 if self.collector.health <= 32 else 1
        if phase != self.collector_phase:
            self.collector_phase = phase
            self.collector.speed = self.collector_speeds[phase - 1]
            self.collector_cycle_time = self.collector_fault_time = 0.0
            self.collector_fault_slot = -1
            if effects.banner_heading == 'SYSTEM ERROR':
                effects.banner_timer = 0.0
            self.collector_volley = 0
            self.collector_phase_spawn_index = 0
            self.collector_pattern = ()
            self.collector_shot_timer = 1.5
            self.collector_spawn_timer = min(self.collector_spawn_timer, 1.0)
            self.active_debuffs.clear()
            self.module_notice = f'COLLECTOR PHASE {phase}'
            self.module_notice_timer = 1.8
            audio.play('boss_phase')

    def update_collector_systems(self, dt, enemies, player, ship_sprites, effects, audio):
        index = self.collector_phase - 1
        period = self.collector_shields[index][0]
        self.collector_cycle_time = (self.collector_cycle_time + dt) % period
        self.collector_entry_times = {enemy: birth for enemy, birth in self.collector_entry_times.items()
                                      if self.phase_time - birth < 0.65 and enemy in enemies}
        self.collector_spawn_timer = max(0, self.collector_spawn_timer - dt)
        if self.collector_spawn_timer == 0 and len(enemies) - 1 < self.collector_phase + 3:
            kinds = self.collector_minions[index]
            for _ in range(3 if self.collector_spawn_index == 0 else 1):
                kind = kinds[self.collector_phase_spawn_index % len(kinds)]
                minion = self._spawn_final_enemy(kind, player, ship_sprites)
                self.collector_entry_times[minion] = self.phase_time
                minion.entry_origin = minion.position.copy()
                enemies.append(minion)
                self.collector_spawn_index += 1
                self.collector_phase_spawn_index += 1
            self.collector_spawn_timer = self.collector_spawn_intervals[index] * self.difficulty_settings['collector_interval_multiplier']

        self.collector_fault_time += dt
        faults = self.collector_faults[index]
        active_duration = (4, 6, 7)[index]
        warning_duration = effects.banner_duration
        cycle = warning_duration + active_duration + (6, 5, 4)[index]
        elapsed = self.collector_fault_time - 2.5
        if elapsed < 0 or elapsed % cycle >= warning_duration + active_duration:
            self.active_debuffs.clear()
            return

        slot = int(elapsed // cycle)
        fault = faults[slot % len(faults)]
        if slot != self.collector_fault_slot:
            self.collector_fault_slot = slot
            self.active_debuffs.clear()
            effects.malfunction_changed(fault)
            audio.play('wave_fault')
        elif effects.banner_timer <= 0:
            self.active_debuffs.add(fault)

    def move_and_fire_collector(self, dt, player, enemy_bullets, audio):
        index = self.collector_phase - 1
        core = self.collector
        offset = core.position - player.position
        radial = offset.normalize() if offset.length_squared() else pygame.Vector2(0, -1)
        side = 1 if int(self.phase_time / 3.5) % 2 == 0 else -1
        strafe = min(1, max(0, (offset.length() - 140) / 140))
        target = player.position + radial.rotate(90) * side * strafe * (45, 55, 65)[index]
        target.x = max(core.rect.width / 2, min(WIDTH - core.rect.width / 2, target.x))
        target.y = max(core.rect.height / 2, min(HEIGHT - core.rect.height / 2, target.y))
        core.position.move_towards_ip(target, dt * core.speed)
        core.rect.center = core.position
        core.hit_flash_timer = max(0.0, core.hit_flash_timer - dt)

        self.collector_shot_timer -= dt
        if not self.collector_pattern and self.collector_shot_timer <= self.collector_windup:
            if core.position.distance_to(player.position) < 150:
                self.collector_shot_timer = self.collector_windup
                return
            lead = self.difficulty_settings['collector_aim_lead']
            aim = player.position + self.player_velocity * lead
            aim.x = max(20, min(WIDTH - 20, aim.x))
            aim.y = max(20, min(HEIGHT - 20, aim.y))
            direction = aim - core.position
            self.collector_aim = direction.normalize() if direction.length_squared() else -radial
            self.collector_pattern = (0,) if index == 0 else (-18, 0, 18)
            if index == 2 and self.collector_volley % 2:
                self.collector_pattern = tuple(range(0, 360, 45))
        if self.collector_shot_timer <= 0 and self.collector_pattern:
            if core.position.distance_to(player.position) >= 130:
                for angle in self.collector_pattern:
                    direction = self.collector_aim.rotate(angle)
                    bullet = Bullet(core.position + direction * 55, direction)
                    bullet.speed = self.collector_bullet_speeds[index]
                    bullet.is_collector_shot = True
                    enemy_bullets.append(bullet)
                audio.play('core_shot')
            self.collector_volley += 1
            self.collector_pattern = ()
            self.collector_shot_timer = self.collector_fire_intervals[index] * self.difficulty_settings['collector_interval_multiplier']

    def draw_collector_defences(self, surface):
        centre = self.collector.position
        if self.collector_shielded or self.collector_shield_charging:
            radius = 91 + round(2 * math.sin(self.phase_time * 12))
            if self.collector_shielded:
                colour = (222, 255, 255) if self.shield_flash > 0 else (105, 226, 255)
                pygame.draw.circle(surface, colour, centre, radius, 3)
                pygame.draw.circle(surface, (48, 120, 165), centre, radius + 5, 1)
            else:
                bounds = pygame.Rect(0, 0, radius * 2, radius * 2)
                bounds.center = centre
                for i in range(4):
                    angle = self.phase_time * 3 + i * math.pi / 2
                    pygame.draw.arc(surface, (255, 187, 86), bounds, angle, angle + 0.7, 2)
        if self.phase_time < 0.36:
            progress = self.phase_time / 0.36
            glow = pygame.Surface((280, 280))
            brightness = 1 - progress
            colour = (int(218 * brightness), int(101 * brightness), int(65 * brightness))
            pygame.draw.circle(glow, colour, (140, 140), round(58 + 80 * progress), 3)
            surface.blit(glow, glow.get_rect(center=centre), special_flags=pygame.BLEND_RGB_ADD)
        if self.collector_pattern:
            progress = 1 - max(0, self.collector_shot_timer) / self.collector_windup
            for angle in self.collector_pattern:
                direction = self.collector_aim.rotate(angle)
                muzzle = centre + direction * 55
                pygame.draw.line(surface, (255, 180, 75), muzzle, muzzle + direction * (10 + 20 * progress), 3)
                pygame.draw.circle(surface, (255, 236, 157), muzzle, 3 + round(3 * progress))

    def destroy_collector(self, enemies, bullets, enemy_bullets, player, effects, audio):
        self.phase = StoryPhase.RETURN_TO_BASE
        self.collector_entry_times.clear()
        self.phase_time = 0.0
        self.active_debuffs.clear()
        self.collector_pattern = ()
        self.departing_ships.clear()
        self.queue_departures(enemy for enemy in enemies if enemy is not self.collector)
        enemies.clear()
        bullets.clear()
        enemy_bullets.clear()
        self.wreckage = scatter_wreckage(self.collector.ship_image, self.collector.position, 0)
        if player.position.x > WIDTH / 2:
            self.dock_position.x = 80
        self.module_notice = 'COLLECTOR DESTROYED'
        self.module_notice_timer = 2.0
        effects.announce_objective('COLLECTOR DESTROYED', 'Return to base')
        effects.shake = max(effects.shake, 10)
        audio.play('wave_clear')

    @property
    def dock_beacon(self):
        side = 1 if self.dock_position.x < WIDTH / 2 else -1
        return self.dock_position + pygame.Vector2(36 * side, 0)

    def update_docking(self, player, audio):
        if self.phase == StoryPhase.RETURN_TO_BASE:
            if self.phase_time < 1.2 or self.departing_ships or player.position.distance_to(self.dock_beacon) > 30:
                return
            self.phase = StoryPhase.DOCKING
            self.phase_time = 0.0
            self.dock_start = player.position.copy()
            self.dock_start_angle = self.ship.angle
            player.recoil_velocity.update(0, 0)
            self.module_notice_timer = 0.0
            audio.play('part_pickup')
        if self.phase == StoryPhase.DOCKING:
            progress = min(1, self.phase_time / self.dock_align_duration)
            eased = progress * progress * (3 - 2 * progress)
            player.position = self.dock_start.lerp(self.dock_position, eased)
            player.rect.center = player.position
            angle = 90 if self.dock_position.x < WIDTH / 2 else -90
            turn = (angle - self.dock_start_angle + 180) % 360 - 180
            self.ship.angle = self.dock_start_angle + turn * eased
            if self.phase_time >= self.dock_align_duration + self.dock_fade_duration:
                self.phase = StoryPhase.VICTORY
                self.phase_time = 0.0
                audio.play('part_attached')

    def draw_dock(self, surface):
        left = self.dock_position.x < WIDTH / 2
        image = self.dock_images[int(left)]
        if image is not None:
            rect = image.get_rect(center=self.dock_position + pygame.Vector2(-20 if left else 20, 0))
            surface.blit(image, rect)
        if self.phase == StoryPhase.RETURN_TO_BASE:
            pulse = (math.sin(self.phase_time * 4) + 1) / 2
            pygame.draw.circle(surface, (75, 181, 177), self.dock_beacon, 22 + round(6 * pulse), 2)
            pygame.draw.circle(surface, (164, 255, 219), self.dock_beacon, 15, 1)

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
            speed_factor = 1.1 if self.phase_time >= self.opening_pursuit_start else 0.85
            self.boss.speed = player.speed * speed_factor
            self.boss.update(dt, player.position)
        elif self.phase == StoryPhase.SURVIVAL or player.position.distance_to(self.boss.position) > 260:
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
        if self.phase == StoryPhase.COLLECTOR_FIGHT:
            gates = ((40, 140), (WIDTH - 40, 140), (40, HEIGHT - 110), (WIDTH - 40, HEIGHT - 110))
            start = self.collector_spawn_index % len(gates)
            candidates = gates[start:] + gates[:start]
            x, y = next(point for point in candidates if player.position.distance_to(point) >= 310
                        and all(enemy.entry_origin.distance_to(point) > 80 for enemy in self.collector_entry_times))
        elif self.phase == StoryPhase.SURVIVAL:
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
        if self.phase == StoryPhase.COLLECTOR_FORMATION:
            progress = min(1.0, self.phase_time / self.collector_formation_duration)
            player.position.update(self.formation_cockpit_start.lerp(self.collector_player_start, 1 - (1 - progress) ** 2))
            player.rect.center = player.position
        self.ship.centre.update(player.position)
        if self.controls_enabled:
            direction = pygame.Vector2(aim) - player.position
            if direction.length_squared() > 0:
                self.ship.angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
        self.ship.update(dt)
        if self.phase == StoryPhase.COLLECTOR_FORMATION:
            self.update_collector_formation()
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
        if self.phase == StoryPhase.COLLECTOR_FORMATION:
            draw_collector_assembly(surface, self.collector_centre, self.returning_cores,
                                    self.phase_time / self.collector_formation_duration)
        for fragment in self.wreckage:
            fragment.draw(surface)
        if self.phase == StoryPhase.RECOVERY:
            for part_id, part in enumerate(self.ship.parts[1:], 1):
                if not part.attached and not part.returning:
                    unlocked = self.recovery_step == RecoveryStep.PICKUP and part_id == self.objective_index + 1
                    self.hud.draw_part_marker(surface, part.position, self.ship.centre, self.phase_time, unlocked)
        if self.phase in (StoryPhase.RETURN_TO_BASE, StoryPhase.DOCKING):
            self.draw_dock(surface)
            if self.phase == StoryPhase.RETURN_TO_BASE:
                self.draw_explosion(surface, self.collector.position, self.phase_time)
                self.hud.draw_departure(surface, self.departing_ships, self.phase_time, direction=-1)
        if self.phase in (StoryPhase.COLLECTOR_FIGHT, StoryPhase.RETURN_TO_BASE, StoryPhase.DOCKING, StoryPhase.VICTORY):
            self.ship.parts[0].draw(surface)
            return
        else:
            self.ship.draw(surface)

        if self.phase == StoryPhase.COLLECTOR_FORMATION:
            for core in self.returning_cores:
                image = self.formation_core_image
                surface.blit(image, image.get_rect(center=core.position))
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
        elif self.phase == StoryPhase.SECOND_DEFEAT:
            if self.returning_volley_fired and self.phase_time < 0.26:
                width = max(2, round(16 * (1 - self.phase_time / 0.26)))
                for core in self.returning_cores:
                    pygame.draw.line(surface, (90, 20, 45), core.position, self.ship.centre, width + 6)
                    pygame.draw.line(surface, (255, 138, 78), core.position, self.ship.centre, width)
                    pygame.draw.line(surface, (255, 245, 191), core.position, self.ship.centre, max(1, width // 3))
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
            source = self.debris_source
            if self.phase == StoryPhase.COLLECTOR_FIGHT:
                source = self.ship.parts[0].image
            self.wreckage = scatter_wreckage(source, player.position, self.ship.angle)
            effects.sparks(player.position, 32, (255, 170, 70))
            audio.play('enemy_down')
        for fragment in self.wreckage:
            fragment.update(dt)
            fragment.draw(surface)
        self.draw_explosion(surface, player.position, self.hull_loss_time)
        if self.hull_loss_time < 0.32:
            progress = self.hull_loss_time / 0.32
            radius = round(22 + 53 * progress)
            glow = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 165, 92, round(180 * (1 - progress))), (80, 80), radius, 3)
            surface.blit(glow, glow.get_rect(center=player.position))
        self.hull_loss_time += dt

    def resource_limits(self, health_limit, ammo_limit):
        if 'REINFORCED_ARMOUR' in self.recovered_upgrades:
            health_limit += 1
        if self.phase in (StoryPhase.COLLECTOR_FIGHT, StoryPhase.RETURN_TO_BASE, StoryPhase.DOCKING):
            health_limit = min(health_limit, self.difficulty_settings['collector_cockpit_health'])
            ammo_limit = max(ammo_limit, math.ceil(self.collector.max_health * self.difficulty_settings['collector_ammo_per_hp']))
        if 'EXPANDED_MAGAZINE' in self.recovered_upgrades:
            ammo_limit += 4
        return max(1, health_limit), max(1, ammo_limit)

    def progress_percent(self):
        if self.phase == StoryPhase.VICTORY:
            return 100
        if self.phase in (StoryPhase.RETURN_TO_BASE, StoryPhase.DOCKING):
            return 99
        if self.phase == StoryPhase.COLLECTOR_FIGHT:
            return 88 + int(10 * (1 - self.collector.health / self.collector.max_health))
        if self.phase in (StoryPhase.SURVIVAL_COMPLETE, StoryPhase.RETURNING_CORES, StoryPhase.SECOND_DEFEAT, StoryPhase.COLLECTOR_FORMATION):
            return 88
        if self.phase == StoryPhase.OPENING:
            return 0
        completed = 1 + len(self.rewarded_parts)
        if self.phase == StoryPhase.RECOVERY and self.objective_index + 1 not in self.rewarded_parts:
            target = self.objectives[self.objective_index]['target']
            completed += self.objective_progress / (target + 1)
        elif self.phase == StoryPhase.SURVIVAL:
            completed += self.phase_time / self.survival_duration
        return min(99, int(100 * completed / (len(self.objectives) + 3)))

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
            debuff_name = objective['debuff'].replace('_', ' ')
            if objective['debuff'] == 'REVERSED':
                debuff_name = 'INVERTED CONTROLS'
            effects.announce_objective(f'SURVIVE WAVE {self.objective_index + 1}',
                                       f"Defeat {objective['target']} enemies  |  {debuff_name}")
            audio.play('wave_fault')

        if effects.banner_timer <= 0:
            self.active_debuffs.add(objective['debuff'])

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