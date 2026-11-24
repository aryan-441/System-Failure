
'''HAVEN GAMEJAM'''
import random
import sys

import pygame
from settings import WIDTH, HEIGHT, FPS, PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED, BG_COLOUR
from player import Player
from bullet import Bullet
from enemy import Enemy
from enemy_spawner import EnemySpawner, choose_enemy_type
from highscore import load_high_score, get_high_score
from background import SpaceBackground
from ship_sprites import ShipSprites
from rounds import RoundManager
from effects import ArcadeEffects
from arcade_audio import ArcadeAudio
from enemy_spacing import separate_enemies
from difficulty import DIFFICULTIES, DEFAULT_DIFFICULTY, ARCADE_TANK_COOLDOWN, ARCADE_TANK_CHANCE
from story_mode import StoryMode, StoryPhase, RecoveryStep
from story_visuals import draw_shield

try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except pygame.error:
    pass
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
world_surface = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("SYSTEM FAILURE: Bounce Back")
clock = pygame.time.Clock()
ship_sprites = ShipSprites()
background = SpaceBackground(WIDTH, HEIGHT)
effects = ArcadeEffects()
audio = ArcadeAudio()
running = True


def draw_menu_choice(rect, label, detail, shortcut, accent, label_font, detail_font, hovered):
    fill = (24, 42, 60) if hovered else (12, 25, 41)
    border = accent if hovered else (67, 88, 110)
    pygame.draw.rect(screen, fill, rect)
    pygame.draw.rect(screen, border, rect, 2)
    pygame.draw.rect(screen, accent, (rect.x, rect.y, 5, rect.height))

    heading = label_font.render(label, True, (241, 247, 255))
    subtitle = detail_font.render(detail, True, (183, 204, 222))
    screen.blit(heading, heading.get_rect(midleft=(rect.x + 23, rect.centery - 10)))
    screen.blit(subtitle, subtitle.get_rect(midleft=(rect.x + 24, rect.centery + 19)))

    keycap = pygame.Rect(0, 0, 39, 32)
    keycap.midright = (rect.right - 16, rect.centery)
    pygame.draw.rect(screen, accent if hovered else (29, 46, 64), keycap)
    hint = detail_font.render(shortcut, True, (12, 25, 41) if hovered else accent)
    screen.blit(hint, hint.get_rect(center=keycap.center))


def choose_difficulty(story_only=False):
    mode = 'story' if story_only else None
    title_font = pygame.font.Font(None, 96)
    mode_font = pygame.font.Font(None, 52)
    difficulty_font = pygame.font.Font(None, 37)
    detail_font = pygame.font.Font(None, 24)
    story_rect = pygame.Rect(WIDTH // 2 - 370, 250, 358, 144)
    arcade_rect = pygame.Rect(WIDTH // 2 + 12, 250, 358, 144)
    difficulties = (
        ('easy', 'ROOKIE PILOT', (120, 220, 170), pygame.K_1),
        ('medium', 'SPACE CADET', (130, 200, 255), pygame.K_2),
        ('hard', 'SYSTEM FAILURE', (255, 120, 120), pygame.K_3)
    )
    difficulty_rects = [pygame.Rect(WIDTH // 2 - 228, 198 + index * 76, 456, 65)
                        for index in range(len(difficulties))]
    back_rect = pygame.Rect(WIDTH // 2 - 228, 445, 120, 35)
    previous_cursor = pygame.mouse.set_visible(True)

    try:
        while True:
            background.update(min(clock.tick(FPS) / 1000, 0.05))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                is_key = event.type == pygame.KEYDOWN
                is_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                if not is_key and not is_click:
                    continue

                if mode is None:
                    if is_key and event.key == pygame.K_ESCAPE:
                        return None
                    if (is_key and event.key == pygame.K_s) or (is_click and story_rect.collidepoint(event.pos)):
                        mode = 'story'
                    elif (is_key and event.key == pygame.K_a) or (is_click and arcade_rect.collidepoint(event.pos)):
                        mode = 'arcade'
                    if mode is not None:
                        audio.play('part_pickup')
                    continue

                if (is_key and event.key == pygame.K_ESCAPE) or (is_click and back_rect.collidepoint(event.pos)):
                    if story_only:
                        return 'back', None
                    mode = None
                    continue

                if is_key and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    audio.play('part_attached')
                    return mode, DEFAULT_DIFFICULTY
                for rect, (name, _, _, key) in zip(difficulty_rects, difficulties):
                    if (is_key and event.key == key) or (is_click and rect.collidepoint(event.pos)):
                        audio.play('part_attached')
                        return mode, name

            screen.fill(BG_COLOUR)
            background.draw(screen)
            pointer = pygame.mouse.get_pos()
            if mode is None:
                title = title_font.render('SYSTEM FAILURE', True, (255, 100, 118))
                subtitle = detail_font.render('B O U N C E   B A C K', True, (204, 225, 241))
                screen.blit(title, title.get_rect(center=(WIDTH // 2, 118)))
                screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 177)))
                draw_menu_choice(story_rect, 'STORY MODE', 'Rebuild your ship. Face the Core.', 'S',
                                 (104, 227, 207), mode_font, detail_font, story_rect.collidepoint(pointer))
                draw_menu_choice(arcade_rect, 'ARCADE MODE', 'Survive and chase a high score', 'A',
                                 (255, 126, 143), mode_font, detail_font, arcade_rect.collidepoint(pointer))
            else:
                title = detail_font.render('SYSTEM FAILURE', True, (255, 126, 143))
                heading = mode_font.render(f'{mode.upper()} MODE', True, (241, 247, 255))
                prompt = detail_font.render('CHOOSE DIFFICULTY', True, (184, 207, 225))
                screen.blit(title, title.get_rect(center=(WIDTH // 2, 56)))
                screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 105)))
                screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 151)))

                for index, (rect, (name, detail, accent, _)) in enumerate(zip(difficulty_rects, difficulties), 1):
                    draw_menu_choice(rect, name.upper(), detail, str(index), accent, difficulty_font,
                                     detail_font, rect.collidepoint(pointer))

                back_colour = (255, 126, 143) if back_rect.collidepoint(pointer) else (183, 204, 222)
                pygame.draw.rect(screen, (12, 25, 41), back_rect)
                pygame.draw.rect(screen, back_colour, back_rect, 1)
                back = detail_font.render('Esc  Back', True, back_colour)
                screen.blit(back, back.get_rect(center=back_rect.center))

            pygame.display.flip()
    finally:
        pygame.mouse.set_visible(previous_cursor)

test_returning_cores = '--test-returning-cores' in sys.argv
selection = ('story', 'hard') if test_returning_cores else choose_difficulty()

if selection is None:
    pygame.quit()
    raise SystemExit

mode, difficulty_name = selection
story_selected = mode == 'story'
story_difficulty = difficulty_name if story_selected else None
if story_selected:
    difficulty_name = DEFAULT_DIFFICULTY

difficulty = DIFFICULTIES[difficulty_name]

ship_sprites.boss_chance = ARCADE_TANK_CHANCE


def create_starting_enemies():
    positions = [(150, 150), (800, 150), (150, 400), (800, 400)]
    starting_enemies = []

    for x, y in positions[:difficulty['starting_enemies']]:
        enemy = Enemy(x, y, choose_enemy_type())
        ship_sprites.prepare_enemy(enemy, allow_boss=False)
        starting_enemies.append(enemy)

    return starting_enemies


def create_spawner():
    return EnemySpawner(difficulty)


round_manager = RoundManager()
malfunction = 'NONE'
bullets = []
enemy_bullets = []
score = 0
high_score = 0 if story_selected else load_high_score()[difficulty_name]
previous_high_score = high_score
new_record = False
shot_timer = 0
last_aim_direction = pygame.Vector2(0, -1)
damage_timer = 0
game_time = 0
first_failure_started = False
game_over_sound_played = False

ammo = difficulty['starting_ammo']
ammo_per_kill = difficulty['ammo_per_kill']
max_ammo = 30 if story_selected else difficulty['max_ammo']

empty_ammo_timer = 0
weapon_heat = 0
max_weapon_heat = 100
heat_per_shot = 10
cooling_rate = difficulty['cooling_rate']
overheated = False

stall_timer = 0
stall_duration = 1.0
stall_interval = 5
is_stalled = False

drift_direction = pygame.Vector2(1, 0)
drift_speed = 80
reactor_timer = 0
reactor_interval = 4
reactor_impulse = pygame.Vector2(0, 0)
reactor_duration = 0.5
reactor_active = False

player = Player(WIDTH/2, HEIGHT/2)
player.health = difficulty['player_health']

story = StoryMode(player, ship_sprites, story_difficulty) if story_selected else None
enemies = story.opening_enemies(ship_sprites) if story else create_starting_enemies()
minimum_health = 0

if test_returning_cores:
    story.objective_index = len(story.objectives) - 1
    story.rewarded_parts.update(range(1, len(story.objectives) + 1))
    story.recovered_upgrades.update(objective['upgrade'] for objective in story.objectives)
    player.health, ammo = story.resource_limits(difficulty['player_health'], max_ammo)
    story.phase = StoryPhase.SURVIVAL_COMPLETE
    story.phase_time = story.survival_retreat_duration
    enemies.clear()

pygame.mouse.set_visible(False)
target_font = pygame.font.Font(None,22)

# ENEMY SPAWNER
spawner = create_spawner()
last_boss_spawn = 0
max_enemies = difficulty['max_enemies']

font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 24)
game_over_font = pygame.font.Font(None, 85)
restart_font = pygame.font.Font(None, 32)

error_explanations = {
    'NONE': 'All systems operational',
    'REVERSED': 'Movement controls are reversed',
    'RECOIL': 'Firing pushes your ship backwards',
    'DAMAGED_THRUSTERS': 'Movement speed is reduced',
    'SHIELD_MALFUNCTION': 'Collisions cause increased damage',
    'WEAPON_OVERHEATING': 'Firing builds heat until the weapon jams',
    'ENGINE_STALLING': 'Your engines periodically stop',
    'TARGETING_GLITCH': 'Bullets may veer off target',
    'ENGINE_DRIFT': 'Your ship drifts to the right',
    'REACTOR_INSTABILITY': 'Random bursts push your ship off course'
}


def draw_crosshair(screen,enemies,font, camera_offset): #custom crosshair
    mouse_pos = pygame.mouse.get_pos()
    x,y = mouse_pos

    world_mous_pos = (
        x - camera_offset[0],
        y -camera_offset[1]
    )

    target = None

    for enemy in enemies:
        if enemy.rect.collidepoint(world_mous_pos):
            target = enemy
            break

    colour = (255,80,90) if target else (100,220,255)

    pygame.draw.circle(screen,colour,(x,y),2)
    pygame.draw.line(screen, colour, (x - 15, y), (x - 6, y), 2)
    pygame.draw.line(screen, colour, (x + 6, y), (x + 15, y), 2)
    pygame.draw.line(screen, colour, (x, y - 15), (x, y - 6), 2)
    pygame.draw.line(screen, colour, (x, y + 6), (x, y + 15), 2)

    if target is not None:
        enemy_type = getattr(target,'enemy_type','normal')

        if getattr(target, 'is_adaptive_boss', False):
            enemy_type = 'adaptive core'
        elif getattr(target,'is_boss',False) and enemy_type != 'adaptive core':
            enemy_type = 'tank'

        label = font.render(
            enemy_type.upper() + ' | ' + str(target.health) + 'HP',
            True,
            (255,255,255)
        )

        label_rect = label.get_rect(
            centerx=target.rect.centerx + camera_offset[0],
            bottom=target.rect.top + camera_offset[1] - 16
        )

        screen.blit(label,label_rect)


while running:
    dt = min(clock.tick(FPS) / 1000, 0.05)  #change in time
    game_time += dt
    background.update(dt)  #bg updates after each line
    effects.update(dt)
    camera_offset = effects.camera_offset()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN: #restarts
            if story:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and player.health <= 0 and game_over_sound_played:
                    was_final_boss = story.phase in (StoryPhase.FINAL_BOSS, StoryPhase.SURVIVAL)
                    story.retry_wave()
                    player.health, ammo = story.resource_limits(difficulty['player_health'], max_ammo)
                    player.position.update(WIDTH / 2, HEIGHT / 2)
                    player.rect.center = player.position
                    enemies.clear()
                    bullets.clear()
                    enemy_bullets.clear()
                    weapon_heat = shot_timer = empty_ammo_timer = 0
                    overheated = game_over_sound_played = False
                    stall_timer = 0
                    is_stalled = False
                    damage_timer = difficulty['damage_cooldown']
                    effects.reset()
                    if was_final_boss:
                        story.module_notice = 'FINAL ENCOUNTER RESTARTED'
                        story.module_notice_timer = 2.0
                if event.key == pygame.K_SPACE and player.health > 0 and story.controls_enabled and 'RIFT_DRIVE' in story.recovered_upgrades and story.rift_drive_cooldown <= 0:
                    event_keys = pygame.key.get_pressed()
                    move = pygame.Vector2(
                        int(event_keys[pygame.K_d] or event_keys[pygame.K_RIGHT]) - int(event_keys[pygame.K_a] or event_keys[pygame.K_LEFT]),
                        int(event_keys[pygame.K_s] or event_keys[pygame.K_DOWN]) - int(event_keys[pygame.K_w] or event_keys[pygame.K_UP])
                    )
                    if move.length_squared() == 0:
                        move = pygame.Vector2(pygame.mouse.get_pos()) - pygame.Vector2(camera_offset) - player.position
                    if move.length_squared() > 0:
                        old_position = player.position.copy()
                        player.position += move.normalize() * 170
                        half = player.rect.width / 2
                        player.position.x = max(half, min(WIDTH - half, player.position.x))
                        player.position.y = max(half, min(HEIGHT - half, player.position.y))
                        player.rect.center = player.position
                        story.rift_drive_cooldown = 5.5
                        effects.sparks(old_position, 12, (155, 105, 255))
                        effects.sparks(player.position, 12, (155, 105, 255))
                if event.key == pygame.K_q and player.health > 0 and story.controls_enabled and 'PHASE_CLOAK' in story.recovered_upgrades and story.phase_cloak_cooldown <= 0:
                    story.phase_cloak_timer = 1.8
                    story.phase_cloak_cooldown = 10.0
                    audio.play('core_shield')
                #story.recover_part(event.key)
                continue
            if player.health <= 0 and event.key in (
                pygame.K_r, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_s
            ):

                story_difficulty = None
                if event.key == pygame.K_1:
                    difficulty_name = 'easy'
                elif event.key == pygame.K_2:
                    difficulty_name = 'medium'
                elif event.key == pygame.K_3:
                    difficulty_name = 'hard'
                elif event.key == pygame.K_s:
                    selection = choose_difficulty(story_only=True)
                    if selection is None:
                        running = False
                        break
                    mode, story_difficulty = selection
                    if mode == 'back':
                        continue
                    difficulty_name = DEFAULT_DIFFICULTY

                difficulty = DIFFICULTIES[difficulty_name]

                player = Player(WIDTH/2, HEIGHT/2)
                player.health = difficulty['player_health']
                story = StoryMode(player, ship_sprites, story_difficulty) if story_difficulty else None
                enemies = story.opening_enemies(ship_sprites) if story else create_starting_enemies()

                max_enemies = difficulty['max_enemies']
                max_ammo = 30 if story else difficulty['max_ammo']
                ammo_per_kill = difficulty['ammo_per_kill']
                cooling_rate = difficulty['cooling_rate']

                bullets = []
                enemy_bullets = []
                score = 0
                high_score = 0 if story else load_high_score()[difficulty_name]

                previous_high_score = high_score
                new_record = False
                shot_timer = 0
                last_aim_direction = pygame.Vector2(0, -1)
                damage_timer = 0
                round_manager = RoundManager()
                malfunction = 'NONE'
                game_time = 0
                first_failure_started = False
                game_over_sound_played = False

                ammo = difficulty['starting_ammo']
                empty_ammo_timer = 0
                weapon_heat = 0
                overheated = False
                stall_timer = 0
                is_stalled = False
                reactor_timer = 0
                reactor_impulse = pygame.Vector2(0, 0)
                reactor_active = False
                reactor_duration = 0.5

                # RESET SPAWNER
                spawner = create_spawner()
                last_boss_spawn = 0
                effects.reset()

    keys = pygame.key.get_pressed()

    if not running:
        break

    if player.health <= 0:
        screen.fill(BG_COLOUR)
        background.draw(screen)

        if story and story.hull_loss_time < story.hull_loss_duration:
            story.animate_hull_loss(screen, player, dt, effects, audio)
            effects.draw(screen)
            pygame.display.flip()
            continue

        if not game_over_sound_played:
            audio.play("game_over")
            game_over_sound_played = True

        if story:
            title = game_over_font.render('HULL LOST', True, (255, 105, 115))
            retry_text = ('R  Retry survival     Esc  Exit'
                          if story.phase == StoryPhase.SURVIVAL
                          else 'R  Retry final encounter     Esc  Exit'
                          if story.phase == StoryPhase.FINAL_BOSS
                          else f'R  Retry wave {story.objective_index + 1}     Esc  Exit')
            retry = restart_font.render(retry_text, True, (175, 224, 236))
            screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT/2 - 24)))
            screen.blit(retry, retry.get_rect(center=(WIDTH/2, HEIGHT/2 + 42)))
            pygame.display.flip()
            continue

        title = game_over_font.render("SYSTEM FAILURE", True, (255, 65, 85))
        mode_display = small_font.render(
            f"DIFFICULTY: {difficulty_name.upper()}",
            True,
            (200, 215, 245)
        )
        score_display = font.render(f"FINAL SCORE: {score}", True, (255, 255, 255))
        restart = restart_font.render(
            "R: RESTART    1: EASY    2: MEDIUM    3: HARD    S: STORY MODE",
            True,
            (120, 200, 255)
        )
        high_score_display = font.render(
            f"HIGH SCORE: {high_score}", True, (255, 220, 90)
        )

        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT/2 - 70)))
        screen.blit(mode_display, mode_display.get_rect(center=(WIDTH/2, HEIGHT/2 - 28)))
        screen.blit(score_display, score_display.get_rect(center=(WIDTH/2, HEIGHT/2 + 10)))
        screen.blit(restart, restart.get_rect(center=(WIDTH/2, HEIGHT/2 + 70)))
        screen.blit(high_score_display, high_score_display.get_rect(center=(WIDTH/2, HEIGHT/2 + 115)))

        if new_record:
            record_text = font.render(
                f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}",
                True,
                (120, 255, 170)
            )
            screen.blit(record_text, record_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 155)))

        pygame.display.flip()
        continue

    if story:
        if story.phase == StoryPhase.OPENING and story.phase_time == 0.0:
            effects.announce_objective('SURVIVE THE ASSAULT', 'Evade the Adaptive Core and its escorts')
        if story.phase == StoryPhase.SURVIVAL:
            dt = min(dt, story.survival_duration - story.phase_time)
        story.advance(dt, effects, audio)

        if story.phase == StoryPhase.COLLECTOR_FORMATION and not story.collector_formation_started:
            story.start_collector_formation(enemies,bullets,enemy_bullets,effects,audio)
        if story.phase == StoryPhase.COLLECTOR_FORMATION and story.phase_time >= story.collector_formation_duration:
            story.start_collector_fight(enemies, player, effects, audio)
        
        if story.phase == StoryPhase.SURVIVAL_COMPLETE and story.phase_time >= story.survival_retreat_duration:
            story.start_returning_cores(enemies,bullets,enemy_bullets,ship_sprites,effects,audio)
            story.last_player_position.update(player.position)
            story.player_velocity.update(0, 0)
        if story.phase == StoryPhase.RECOVERY_COMPLETE:
            story.start_final_boss(enemies, bullets, enemy_bullets, audio, survival=True)
            story.last_player_position.update(player.position)
            effects.announce_objective(f'SURVIVE {story.survival_duration:.0f} SECONDS',
                                       'Defeat the Core and all hostiles to finish early')
        elif story.phase == StoryPhase.FINAL_BOSS and not story.final_boss_started:
            story.start_final_boss(enemies, bullets, enemy_bullets, audio)
        elif story.phase == StoryPhase.SURVIVAL:
            story.update_survival_spawns(dt, enemies, ship_sprites, player)
        story.update_final_encounter(dt, enemies, ship_sprites, player, audio)
        story.update_objective(dt, player)
        story.spawn_recovery_enemies(enemies, ship_sprites, player,dt, effects, audio)

        minimum_health = 0 if story.phase in (StoryPhase.OPENING, StoryPhase.RECOVERY, StoryPhase.FINAL_BOSS, StoryPhase.SURVIVAL, StoryPhase.RETURNING_CORES, StoryPhase.COLLECTOR_FIGHT) else 1

    controls_enabled = story is None or story.controls_enabled

    story_debuffs=story.active_debuffs if story else set()
    story_upgrades = story.recovered_upgrades if story else set()

    current_health_limit = difficulty['player_health']
    current_max_ammo = max_ammo
    current_ammo_per_kill = ammo_per_kill

    if story:
        current_health_limit, current_max_ammo = story.resource_limits(current_health_limit, current_max_ammo)

    if 'SALVAGE_MODULE' in story_upgrades:
        current_ammo_per_kill += 1

    current_health_limit = max(1,current_health_limit)
    current_max_ammo = max(1, current_max_ammo)
    current_ammo_per_kill = max(0, current_ammo_per_kill)

    player.health = min(player.health, current_health_limit)
    ammo = min(ammo, current_max_ammo)
    round_changed = story is None and round_manager.update(dt)

    if story is None and game_time >= 15 and not first_failure_started and round_manager.current_malfunction != 'NONE':
        first_failure_started = True
        round_manager.round_timer = 0
        malfunction = round_manager.current_malfunction
        effects.malfunction_changed(malfunction)
        audio.play("wave_fault")
        stall_timer = 0
        is_stalled = False
        reactor_timer = 0
        reactor_impulse = pygame.Vector2(0, 0)
        reactor_active = False
        reactor_duration = 0.5
        weapon_heat = 0
        overheated = False

    elif game_time >= 15 and round_changed:
        malfunction = round_manager.current_malfunction
        effects.malfunction_changed(malfunction)
        audio.play("wave_fault")

        stall_timer = 0
        is_stalled = False
        reactor_timer = 0
        reactor_impulse = pygame.Vector2(0, 0)
        reactor_active = False
        reactor_duration = 0.5
        weapon_heat = 0
        overheated = False

    active_malfunction = next(iter(story_debuffs), 'NONE') if story else malfunction
    if active_malfunction == 'ENGINE_STALLING':
        stall_timer += dt

        if is_stalled:
            if stall_timer >= stall_duration:
                is_stalled = False
                stall_timer = 0
        elif stall_timer >= stall_interval:
            is_stalled = True
            stall_timer = 0
    else:
        stall_timer = 0
        is_stalled = False

    if malfunction == 'REACTOR_INSTABILITY':
        reactor_timer += dt

        if not reactor_active and reactor_timer >= reactor_interval:
            reactor_impulse = pygame.Vector2(
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            )

            if reactor_impulse.length() > 0:
                reactor_impulse = reactor_impulse.normalize()

            reactor_active = True
            reactor_timer = 0

        if reactor_active:
            reactor_duration -= dt

            if reactor_duration <= 0:
                reactor_active = False
                reactor_duration = 0.5
    else:
        reactor_timer = 0
        reactor_active = False
        reactor_duration = 0.5

    if story:
        player.speed = PLAYER_SPEED

        if 'ENHANCED_THRUSTERS' in story_upgrades:
            player.speed *= 1.10

        if 'DAMAGED_THRUSTERS' in story_debuffs:
            player.speed *= 0.75

    elif malfunction == 'DAMAGED_THRUSTERS':
        player.speed = PLAYER_SPEED * difficulty['thruster_multiplier']
    else:
        player.speed = PLAYER_SPEED

    original_speed = player.speed

    if is_stalled:
        player.speed = 0

    if controls_enabled:
        player.update(dt, keys,active_malfunction)

    player.speed = original_speed

    if malfunction == 'ENGINE_DRIFT':
        player.position += drift_direction * drift_speed * dt

    if malfunction == 'REACTOR_INSTABILITY' and reactor_active:
        player.position += reactor_impulse * 350 * dt

    half = player.rect.width / 2
    player.position.x = max(half, min(WIDTH - half, player.position.x))
    player.position.y = max(half, min(HEIGHT - half, player.position.y))
    player.rect.center = player.position
    #enemies_per_second = min(0.65, 0.30 + game_time * 0.002)
    #spawner.spawn_interval = 1 / enemies_per_second

    # AUTOMATIC ENEMY SPAWNING
    spawn_ready = story is None and spawner.update(dt, malfunction != 'NONE') 
    if len(enemies) < max_enemies and spawn_ready:
            new_enemy = spawner.spawn()
            allow_boss = game_time >= 40 and game_time - last_boss_spawn >= ARCADE_TANK_COOLDOWN
            '''tank_alive = False
            for enemy in enemies:
                if enemy.is_boss:
                    tank_alive = True
                    break
            if tank_alive:
                allow_boss = False'''
            allow_boss = allow_boss and not any(enemy.is_boss for enemy in enemies) #generator attribute


            ship_sprites.prepare_enemy(new_enemy, allow_boss=allow_boss)
            if new_enemy.is_boss:
                last_boss_spawn = game_time
                audio.play('boss_spawn')

            enemies.append(new_enemy)

    if story and story.phase == StoryPhase.RETURNING_CORES:
        story.track_returning_player(dt, player)

    for enemy in enemies:
        if story and enemy is story.boss:
            story.update_boss(dt, player, pygame.mouse.get_pressed()[0], audio)
        elif story and enemy in story.returning_cores:
            if story.phase == StoryPhase.RETURNING_CORES:
                story.update_returning_core(enemy, dt, player)
        else:
            enemy.update(dt,player.position)

        # RANGER SHOOTING
        story_shot = story is not None and enemy is story.boss and story.shot_timer <= 0
        opening_core_shot = story_shot and story.phase == StoryPhase.OPENING
        if enemy.enemy_type in ('ranger', 'siege_walker') or story_shot:
            distance = enemy.position.distance_to(player.position)

            if story_shot or (enemy.fire_timer <= 0 and distance <= (540 if enemy.enemy_type == 'siege_walker' else 500)):
                direction = story.aim_boss_shot(player) if story_shot else player.position - enemy.position
                if opening_core_shot and direction.length_squared() == 0:
                    direction = pygame.Vector2(0, 1)

                if direction.length_squared() > 0:
                    spread = (-10, 0, 10) if enemy.enemy_type == 'siege_walker' else (0,)
                    for angle in spread:
                        new_bullet = Bullet(enemy.position, direction.rotate(angle))
                        new_bullet.speed = story.boss_bullet_speed if story_shot else (285 if enemy.enemy_type == 'siege_walker' else 250)
                        new_bullet.is_opening_core_shot = opening_core_shot
                        new_bullet.is_ranger_shot = enemy.enemy_type == 'ranger' and not story_shot
                        enemy_bullets.append(new_bullet)
                    if story_shot or story is None:
                        audio.play('core_shot')
                    if not story_shot:
                        enemy.fire_timer = 1.7 if enemy.enemy_type == 'siege_walker' else 2.5

        if (story and story.phase == StoryPhase.RETURNING_CORES and enemy in story.returning_cores
                and enemy.role != 'rammer' and enemy.fire_timer <= 0):
            gunner = enemy.role == 'gunner'
            speed = 305 if gunner else 285
            direction = story.aim_returning_core_shot(enemy, player, speed)
            if direction.length_squared() > 0:
                for angle in ((-10, 0, 10) if gunner else (0,)):
                    new_bullet = Bullet(enemy.position, direction.rotate(angle))
                    new_bullet.speed = speed
                    enemy_bullets.append(new_bullet)
                audio.play('core_shot')
                enemy.fire_timer = 1.05 if gunner else 1.8
    separate_enemies(enemies, WIDTH, HEIGHT)

    #shooting logic
    mouse_pos = pygame.mouse.get_pos()
    world_mous_pos = (
        mouse_pos[0] - camera_offset[0],
        mouse_pos[1] - camera_offset[1]
    )
    mouse_buttons = pygame.mouse.get_pressed()
    shot_timer = max(0, shot_timer - dt) #decreases the timer and ensures that the value doesnt become negative
    damage_timer = max(0, damage_timer - dt)
    damage_cooldown = difficulty['damage_cooldown']
    if story and story.phase == StoryPhase.RETURNING_CORES:
        damage_cooldown = story.returning_damage_cooldown

    # ENEMY PROJECTILES
    for bullet in enemy_bullets:
        bullet.update(dt)

    if malfunction == 'WEAPON_OVERHEATING' or 'WEAPON_OVERHEATING' in story_debuffs:
        weapon_heat = max(0, weapon_heat - cooling_rate * dt)

        if overheated and weapon_heat <= 40:
            overheated = False
    else:
        weapon_heat = 0
        overheated = False

    if ammo == 0 and len(bullets) == 0:
        empty_ammo_timer += dt

        if empty_ammo_timer >= 5:
            ammo = 3
            empty_ammo_timer = 0
            audio.play("ammo")
    else:
        empty_ammo_timer = 0

    aim_direction = pygame.Vector2(world_mous_pos) - player.position
    if aim_direction.length_squared() > 0:
        last_aim_direction = aim_direction

    if controls_enabled and mouse_buttons[0] and shot_timer <= 0 and ammo > 0 and not overheated: #if the user clicks and time is left
        direction = last_aim_direction

        if 'TARGETING_GLITCH' in story_debuffs:
            direction = direction.rotate(random.uniform(-15, 15))
        elif malfunction == 'TARGETING_GLITCH':
            direction = direction.rotate(random.uniform(-17, 17))

        if direction.length() > 0:
            bullet = Bullet(player.position, direction)
            if 'SIEGE_CANNON' in story_upgrades:
                bullet.pierce_remaining = 2
            if 'TARGETING_COMPUTER' in story_upgrades:
                bullet.speed *= 1.15
            bullets.append(bullet)
            effects.muzzle_flash(player.position, direction)
            audio.play("shoot")
            shot_timer = 0.2
            if 'OVERCLOCKED_WEAPONS' in story_upgrades:
                shot_timer *= 0.90
            ammo -= 1

            if malfunction == 'WEAPON_OVERHEATING' or 'WEAPON_OVERHEATING' in story_debuffs:
                weapon_heat = min(max_weapon_heat, weapon_heat + heat_per_shot)

                if weapon_heat >= max_weapon_heat:
                    overheated = True
                    audio.play("overheat")

            if malfunction == 'RECOIL':
                player.apply_recoil(direction)

    if (malfunction == 'WEAPON_OVERHEATING' or 'WEAPON_OVERHEATING' in story_debuffs) and overheated:
        effects.smoke(player.position, dt)

    if story and story.phase == StoryPhase.OPENING:
        story.update_shield(bullets)

    #aim_direction = pygame.Vector2(mouse_pos) - player.position
    for bullet in bullets[:]:   #slicing to loop over a copy
        bullet.update(dt)

    for player_bullet in bullets[:]:
        for enemy_bullet in enemy_bullets[:]:
            if enemy_bullet.is_ranger_shot and player_bullet.intersects_shot(enemy_bullet):
                bullets.remove(player_bullet)
                enemy_bullets.remove(enemy_bullet)
                effects.sparks(enemy_bullet.position, 12, (255, 150, 80))
                audio.play('enemy_down')
                break

    for bullet in enemy_bullets[:]:
        if bullet.overlaps(player.rect):
            enemy_bullets.remove(bullet)

            if (bullet.is_opening_core_shot or damage_timer <= 0) and player.health > 0 and (story is None or story.phase_cloak_timer <= 0):
                damage = 1

                if active_malfunction == 'SHIELD_MALFUNCTION':
                    damage = 2

                previous_health = player.health
                player.health = max(minimum_health, player.health - damage)
                if bullet.is_opening_core_shot:
                    damage = previous_health - player.health
                else:
                    damage_timer = damage_cooldown
                effects.player_hit(player.position, damage)
                audio.play("player_hit")

        elif bullet.is_off_screen():
            enemy_bullets.remove(bullet)
    if player.health <= 0:
        if story is None or story.phase not in (StoryPhase.OPENING, StoryPhase.RETURNING_CORES):
            continue
        controls_enabled = False

    for bullet in bullets[:]:
        if bullet not in bullets:
            break
        for enemy in enemies[:]:  #nested list
            if enemy not in bullet.hit_targets and bullet.overlaps(enemy.rect):
                bullet.hit_targets.add(enemy)
                if bullet.pierce_remaining > 0:
                    bullet.pierce_remaining -= 1
                else:
                    bullets.remove(bullet)

                if getattr(enemy, 'is_story_invulnerable', False):
                    effects.sparks(bullet.position, 8, (140,235,255))
                    if enemy.shield_flash <= 0:
                        audio.play('core_shield')
                    enemy.shield_flash = 0.22
                    break

                if story and enemy is story.boss and (story.phase != StoryPhase.SURVIVAL or story.shielded):
                    result = story.hit_boss(bullet.position, effects, audio)
                    if result == 'FURY':
                        story.begin_fury(enemies, bullets, enemy_bullets, ship_sprites, audio, effects)
                    elif result is True:
                        enemies.clear()
                        enemy_bullets.clear()
                    audio.play("hit")
                    break
                if getattr(enemy, 'is_phasing', False):
                    effects.sparks(bullet.position, 5, (90, 235, 235))
                    break
                enemy_last_tick = pygame.time.get_ticks()
                enemy.last_hit = enemy_last_tick
                effects.hit_enemy(enemy)
                audio.play("hit")


                if enemy.take_damage(1):
                    if story:
                        story.record_kill(enemy, audio)
                        story.record_final_kill(enemy, audio, effects)
                        if story.recovery_step == RecoveryStep.PICKUP:
                            enemy_bullets.clear()
                    effects.enemy_destroyed(enemy)
                    audio.play("enemy_down")
                    if story is None and enemy.is_boss:
                        audio.play('wave_clear')
                    enemies.remove(enemy)
                    score += 100
                    ammo = min(current_max_ammo, ammo + current_ammo_per_kill)

                    if story is None and score > high_score:
                        new_record = True
                        high_score = score
                        try:
                            get_high_score(high_score, difficulty_name)
                        except OSError:
                            pass

                if bullet not in bullets:
                    break

        if bullet in bullets and bullet.is_off_screen():
            bullets.remove(bullet)

    collision = False

    for enemy in enemies[:]:
        if enemy.rect.colliderect(player.rect):
            if getattr(enemy, 'is_phasing', False):
                continue
            collision = True

            if enemy.enemy_type == 'bomber':
                effects.enemy_destroyed(enemy)
                audio.play("enemy_down")
                if story:
                    story.record_final_kill(enemy, audio, effects)
                enemies.remove(enemy)

                if damage_timer <= 0 and player.health > 0 and (story is None or story.phase_cloak_timer <= 0):
                    damage = 2

                    if active_malfunction == 'SHIELD_MALFUNCTION':
                        damage = 3

                    player.health = max(minimum_health, player.health - damage)
                    damage_timer = damage_cooldown
                    effects.player_hit(player.position, damage)
                    audio.play("player_hit")

            elif damage_timer <= 0 and player.health > 0 and (story is None or story.phase_cloak_timer <= 0):
                if story and story.phase == StoryPhase.RETURNING_CORES and enemy in story.returning_cores:
                    damage = 3
                elif active_malfunction == 'SHIELD_MALFUNCTION':
                    damage = 2
                else:
                    damage = 1

                player.health = max(minimum_health, player.health - damage)
                damage_timer = damage_cooldown
                effects.player_hit(player.position, damage)
                audio.play("player_hit")

            break

    if story and story.finish_opening(player, enemies, bullets, enemy_bullets, effects, audio):
        ammo = max_ammo
        player.health = current_health_limit

    if story and story.phase == StoryPhase.RETURNING_CORES:
        if player.health <= 0 or story.phase_time >= story.retreating_attack_duration:
            story.begin_second_defeat(player,bullets,enemy_bullets,effects, audio)

    if story and story.phase == StoryPhase.SURVIVAL and player.health > 0:
        if not enemies or story.phase_time >= story.survival_duration:
            story.finish_survival(enemies, bullets, enemy_bullets, effects, audio)

    if collision:
        pygame.display.set_caption("COLLISION DETECTED!")
    else:
        pygame.display.set_caption("SYSTEM FAILURE: Bounce Back")

    world_surface.fill(BG_COLOUR)
    background.draw(world_surface)
    if story:
        if story.phase_cloak_timer > 0:
            draw_shield(world_surface, player.position, story.phase_time, 0.15)
        story.update_ship(player, world_mous_pos, dt, effects)
        if story.update_pickup(player, audio):
            player.health = min(current_health_limit, player.health + 2)
            ammo = min(current_max_ammo, ammo + 3)

        if story.pending_rewards > 0:
            audio.play('part_attached')
            story.pending_rewards = 0

            current_health_limit, current_max_ammo = story.resource_limits(difficulty['player_health'], max_ammo)
            enemy_bullets.clear()

        story.draw_ship(world_surface)
    else:
        ship_sprites.draw_player(world_surface, player, world_mous_pos)

    for enemy in enemies:
        use_core_hud = story and enemy is story.boss and story.phase in (StoryPhase.SURVIVAL, StoryPhase.FINAL_BOSS)
        returning_core = story and story.phase == StoryPhase.RETURNING_CORES and enemy in story.returning_cores
        ship_sprites.draw_enemy(world_surface, enemy, show_health=not (use_core_hud or returning_core or (story and enemy is story.collector)))
        effects.draw_enemy_flash(world_surface, enemy)
        if story and enemy is story.boss:
            story.draw_boss_defences(world_surface)
        elif returning_core:
            story.draw_returning_core_defences(world_surface, enemy, player, bullets)

    for bullet in bullets:
        bullet.draw(world_surface)

    # RANGER LASERS
    for bullet in enemy_bullets:
        head = bullet.position
        tail = bullet.position - bullet.direction * 18

        pygame.draw.line(world_surface, (100, 15, 20), tail, head, 10)
        pygame.draw.line(world_surface, (255, 50, 65), tail, head, 6)
        pygame.draw.line(world_surface, (255, 215, 215), tail, head, 2)

    effects.draw(world_surface)
    screen.fill(BG_COLOUR)
    screen.blit(world_surface, camera_offset)

    if story:
        story_display_debuff = next(iter(story.active_debuffs), 'NONE')
        heat_percent = int(100 * weapon_heat / max_weapon_heat)
        story.draw_hud(screen, player, ammo, current_health_limit, current_max_ammo, story_display_debuff, error_explanations.get(story_display_debuff,''), heat_percent, overheated)
        effects.draw_overlay(screen, WIDTH, HEIGHT)
        draw_crosshair(screen,enemies,target_font,camera_offset)
        pygame.display.flip()
        continue

    '''pygame.draw.line(
    screen,
    (100, 220, 255), #rgb colour
    player.position,
    mouse_pos,
    2
)'''

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    health_text = font.render(f"Health: {player.health}", True, (255, 255, 255)) #render the font
    ammo_text = font.render(f"Ammo: {ammo}", True, (255, 220, 90))
    high_score_text = font.render(f"High Score: {high_score}", True, (255, 220, 90))

    if game_time < 15:
        round_text = font.render("SYSTEM STABLE", True, (255, 255, 255))
        malfunction_text = small_font.render(
            f"FIRST FAILURE IN {max(0, int(16 - game_time))}s",
            True,
            (255, 120, 130)
        )
    else:
        round_text = font.render(f"ROUND: {round_manager.round_number}", True, (255, 255, 255))
        malfunction_text = small_font.render(
            f"SYSTEM ERROR: {malfunction.replace('_', ' ')}",
            True,
            (255, 120, 130)
        )

    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))
    screen.blit(ammo_text, (20, 100))

    difficulty_text = small_font.render(
        f"MODE: {difficulty_name.upper()}",
        True,
        (190, 200, 225)
    )
    screen.blit(difficulty_text, (20, 180))

    screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 20))
    screen.blit(round_text, (WIDTH - round_text.get_width() - 20, 60))
    screen.blit(malfunction_text, (WIDTH - malfunction_text.get_width() - 20, 100))

    if game_time >= 15:
        explanation = error_explanations.get(malfunction, 'Unknown system error')
        explanation_text = small_font.render(
            explanation,
            True,
            (200, 210, 230)
        )
        screen.blit(explanation_text, (WIDTH - explanation_text.get_width() - 20, 130))

    if malfunction == 'WEAPON_OVERHEATING':
        heat_text = font.render(
            f"Weapon Heat: {int(weapon_heat)}%",
            True,
            (255, 100, 80)
        )
        screen.blit(heat_text, (WIDTH - heat_text.get_width() - 20, 180))

        if overheated:
            warning = font.render("WEAPON OVERHEATED!", True, (255, 50, 50))
            screen.blit(warning, (WIDTH - warning.get_width() - 20, 220))

    if ammo == 0:
        reload_text = font.render(
            "OUT OF AMMO - EMERGENCY SUPPLY INCOMING",
            True,
            (255, 80, 80)
        )
        screen.blit(reload_text, (20, 140))

    if new_record:
        record_text = font.render(
            f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}",
            True,
            (120, 255, 170)
        )
        screen.blit(record_text, (WIDTH - record_text.get_width() - 20, HEIGHT - 40))

    effects.draw_overlay(screen, WIDTH, HEIGHT)
    draw_crosshair(screen,enemies,target_font,camera_offset)
    pygame.display.flip() #the flip method updates the display

pygame.mouse.set_visible(True)
pygame.quit()
