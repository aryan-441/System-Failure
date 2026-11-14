'''SYSTEM FAILURE: BOUNCE BACK'''
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, PLAYER_SPEED, BG_COLOUR
)
from player import Player
from bullet import Bullet
from enemy import Enemy
from enemy_spawner import EnemySpawner
from highscore import load_high_score, get_high_score
from background import SpaceBackground
from ship_sprites import ShipSprites
from rounds import RoundManager
from effects import ArcadeEffects
from arcade_audio import ArcadeAudio
from enemy_spacing import separate_enemies


# Initialise audio before pygame.init so systems with no audio device can
# fall back to silent gameplay instead of failing during startup.
try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except pygame.error:
    pass
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
world_surface = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("SYSTEM FAILURE: Bounce Back")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 24)
game_over_font = pygame.font.Font(None, 85)
restart_font = pygame.font.Font(None, 32)

ship_sprites = ShipSprites()
background = SpaceBackground(WIDTH, HEIGHT)
effects = ArcadeEffects()
audio = ArcadeAudio()


def make_initial_enemies():
    initial = [
        Enemy(150, 150),
        Enemy(800, 150),
        Enemy(150, 400),
    ]
    for enemy in initial:
        ship_sprites.prepare_enemy(enemy, allow_boss=False)
    return initial


def reset_game():
    global player, enemies, bullets, spawner, round_manager, malfunction
    global score, ammo, weapon_heat, overheated, shot_timer, damage_timer
    global empty_ammo_timer, stall_timer, is_stalled, reactor_timer
    global reactor_impulse, reactor_duration, reactor_active
    global game_time, last_boss_spawn, game_over_sound_played
    global previous_high_score, new_record, high_score

    player = Player(WIDTH / 2, HEIGHT / 2)
    enemies = make_initial_enemies()
    bullets = []
    spawner = EnemySpawner()
    round_manager = RoundManager()
    malfunction = round_manager.current_malfunction

    score = 0
    ammo = 16
    weapon_heat = 0.0
    overheated = False
    shot_timer = 0.0
    damage_timer = 0.0
    empty_ammo_timer = 0.0

    stall_timer = 0.0
    is_stalled = False
    reactor_timer = 0.0
    reactor_impulse = pygame.Vector2(0, 0)
    reactor_duration = 0.5
    reactor_active = False

    game_time = 0.0
    last_boss_spawn = 0.0
    game_over_sound_played = False
    previous_high_score = high_score
    new_record = False
    effects.reset()


player = None
enemies = []
bullets = []
spawner = None
round_manager = None
malfunction = 'NONE'
score = 0
high_score = load_high_score()
previous_high_score = high_score
new_record = False

ammo = 16
max_ammo = 24
ammo_per_kill = 5
empty_ammo_timer = 0.0
weapon_heat = 0.0
max_weapon_heat = 100
heat_per_shot = 5
cooling_rate = 9
overheated = False

shot_timer = 0.0
damage_timer = 0.0
stall_timer = 0.0
stall_duration = 1.5
stall_interval = 5.0
is_stalled = False

reactor_timer = 0.0
reactor_interval = 4.0
reactor_impulse = pygame.Vector2(0, 0)
reactor_duration = 0.5
reactor_active = False

game_time = 0.0
last_boss_spawn = 0.0
boss_spawn_cooldown = 20.0
max_enemies = 9
game_over_sound_played = False

reset_game()
running = True

while running:
    dt = min(clock.tick(FPS) / 1000.0, 0.05)
    game_time += dt
    background.update(dt)
    effects.update(dt)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and player.health <= 0:
                reset_game()

    if not running:
        break

    if player.health <= 0:
        if not game_over_sound_played:
            audio.play("game_over")
            game_over_sound_played = True

        screen.fill(BG_COLOUR)
        background.draw(screen)

        title = game_over_font.render("SYSTEM FAILURE", True, (255, 65, 85))
        score_display = font.render(f"FINAL SCORE: {score}", True, (255, 255, 255))
        restart = restart_font.render("PRESS R TO RESTART", True, (120, 200, 255))
        high_score_display = font.render(
            f"HIGH SCORE: {high_score}", True, (255, 220, 90)
        )

        screen.blit(title, title.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 75)))
        screen.blit(score_display, score_display.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 5)))
        screen.blit(restart, restart.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 65)))
        screen.blit(
            high_score_display,
            high_score_display.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 110))
        )

        if new_record:
            record = font.render(
                f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}",
                True, (120, 255, 170)
            )
            screen.blit(record, record.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 155)))

        pygame.display.flip()
        continue

    # The first malfunction begins after the 15 second stable opening
    if round_manager.update(dt):
        malfunction = round_manager.current_malfunction
        effects.malfunction_changed(malfunction)
        audio.play("warning")

        stall_timer = 0.0
        is_stalled = False
        reactor_timer = 0.0
        reactor_impulse.update(0, 0)
        reactor_active = False
        reactor_duration = 0.5
        weapon_heat = 0.0
        overheated = False

    # Timed malfunction behaviour.
    if malfunction == 'ENGINE_STALLING':
        stall_timer += dt
        if is_stalled:
            if stall_timer >= stall_duration:
                is_stalled = False
                stall_timer = 0.0
        elif stall_timer >= stall_interval:
            is_stalled = True
            stall_timer = 0.0
    else:
        stall_timer = 0.0
        is_stalled = False

    if malfunction == 'REACTOR_INSTABILITY':
        reactor_timer += dt
        if not reactor_active and reactor_timer >= reactor_interval:
            reactor_impulse = pygame.Vector2(
                random.uniform(-1, 1), random.uniform(-1, 1)
            )
            if reactor_impulse.length_squared() > 0:
                reactor_impulse = reactor_impulse.normalize()
            reactor_active = True
            reactor_timer = 0.0

        if reactor_active:
            reactor_duration -= dt
            if reactor_duration <= 0:
                reactor_active = False
                reactor_duration = 0.5
    else:
        reactor_timer = 0.0
        reactor_active = False
        reactor_duration = 0.5

    player.speed = PLAYER_SPEED * (
        0.5 if malfunction == 'DAMAGED_THRUSTERS' else 1.0
    )
    original_speed = player.speed
    if malfunction == 'ENGINE_STALLING' and is_stalled:
        player.speed = 0

    keys = pygame.key.get_pressed()
    player.update(dt, keys, malfunction)
    player.speed = original_speed

    if malfunction == 'ENGINE_DRIFT':
        player.position.x += 80 * dt
    if malfunction == 'REACTOR_INSTABILITY' and reactor_active:
        player.position += reactor_impulse * 350 * dt

    half = player.rect.width / 2
    player.position.x = max(half, min(WIDTH - half, player.position.x))
    player.position.y = max(half, min(HEIGHT - half, player.position.y))
    player.rect.center = player.position

    # Spawn pressure rises gradually, with a hard cap on living enemies.
    enemies_per_second = min(0.55, 0.24 + game_time * 0.00172)
    spawner.spawn_interval = 1.0 / enemies_per_second
    if len(enemies) < max_enemies and spawner.update(dt):
        allow_boss = (
            game_time >= 40.0
            and game_time - last_boss_spawn >= boss_spawn_cooldown
            and not any(getattr(enemy, "is_boss", False) for enemy in enemies)
        )
        new_enemy = spawner.spawn()
        ship_sprites.prepare_enemy(new_enemy, allow_boss=allow_boss)
        if getattr(new_enemy, "is_boss", False):
            last_boss_spawn = game_time
        enemies.append(new_enemy)

    for enemy in enemies:
        enemy.update(dt, player.position)
    separate_enemies(enemies, WIDTH, HEIGHT)

    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()
    shot_timer = max(0.0, shot_timer - dt)
    damage_timer = max(0.0, damage_timer - dt)

    if malfunction == 'WEAPON_OVERHEATING':
        weapon_heat = max(0.0, weapon_heat - cooling_rate * dt)
        if overheated and weapon_heat <= 40:
            overheated = False
    else:
        weapon_heat = 0.0
        overheated = False

    if ammo == 0 and not bullets:
        empty_ammo_timer += dt
        if empty_ammo_timer >= 5.0:
            ammo = 3
            empty_ammo_timer = 0.0
            audio.play("ammo")
    else:
        empty_ammo_timer = 0.0

    if (
        mouse_buttons[0] and shot_timer <= 0
        and ammo > 0 and not overheated
    ):
        direction = pygame.Vector2(mouse_pos) - player.position
        if malfunction == 'TARGETING_GLITCH':
            direction = direction.rotate(random.uniform(-17, 17))

        if direction.length_squared() > 0:
            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            effects.muzzle_flash(player.position, direction)
            audio.play("shoot")
            shot_timer = 0.2
            ammo -= 1

            if malfunction == 'WEAPON_OVERHEATING':
                weapon_heat = min(
                    max_weapon_heat, weapon_heat + heat_per_shot
                )
                if weapon_heat >= max_weapon_heat:
                    overheated = True
                    audio.play("overheat")

            if malfunction == 'RECOIL':
                player.apply_recoil(direction)

    if malfunction == 'WEAPON_OVERHEATING' and overheated:
        effects.smoke(player.position, dt)

    for bullet in bullets[:]:
        bullet.update(dt)
        if bullet.is_off_screen():
            bullets.remove(bullet)

    for bullet in bullets[:]:
        hit_enemy = None
        for enemy in enemies:
            if bullet.rect.colliderect(enemy.rect):
                hit_enemy = enemy
                break

        if hit_enemy is not None:
            if bullet in bullets:
                bullets.remove(bullet)
            effects.hit_enemy(hit_enemy)
            audio.play("hit")

            if hit_enemy.take_damage(1):
                effects.enemy_destroyed(hit_enemy)
                audio.play("enemy_down")
                enemies.remove(hit_enemy)
                score += 100
                ammo = min(max_ammo, ammo + ammo_per_kill)

                if score > high_score:
                    high_score = score
                    new_record = True
                    try:
                        get_high_score(high_score)
                    except OSError:
                        pass

    # Apply one player damage event per cooldown, even if several enemies overlap.
    if damage_timer <= 0 and player.health > 0:
        for enemy in enemies:
            if enemy.rect.colliderect(player.rect):
                damage = 2 if malfunction == 'SHIELD_MALFUNCTION' else 1
                player.health -= damage
                damage_timer = 1.0
                effects.player_hit(player.position, damage)
                audio.play("player_hit")
                break

    pygame.display.set_caption(
        "COLLISION DETECTED!" if any(
            enemy.rect.colliderect(player.rect) for enemy in enemies
        ) else "SYSTEM FAILURE: Bounce Back"
    )

    # Draw the game world to a separate surface so screen shake does not
    # displace the HUD.
    world_surface.fill(BG_COLOUR)
    background.draw(world_surface)
    ship_sprites.draw_player(world_surface, player, mouse_pos)

    for enemy in enemies:
        ship_sprites.draw_enemy(world_surface, enemy)
        effects.draw_enemy_flash(world_surface, enemy)

    for bullet in bullets:
        bullet.draw(world_surface)

    effects.draw(world_surface)
    screen.fill(BG_COLOUR)
    screen.blit(world_surface, effects.camera_offset())

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    health_text = font.render(f"Health: {player.health}", True, (255, 255, 255))
    ammo_text = font.render(f"Ammo: {ammo}", True, (255, 220, 90))
    high_score_text = font.render(
        f"High Score: {high_score}", True, (255, 220, 90)
    )
    round_label = (
        "SYSTEM STABLE" if malfunction == 'NONE'
        else f"ROUND: {round_manager.round_number}"
    )
    round_text = font.render(round_label, True, (255, 255, 255))
    malfunction_label = (
        "FIRST FAILURE IN 15s" if not round_manager.started
        else f"ERROR: {malfunction.replace('_', ' ')}"
    )
    malfunction_text = small_font.render(
        malfunction_label, True, (255, 120, 130)
    )

    screen.blit(score_text, (20, 18))
    screen.blit(health_text, (20, 52))
    screen.blit(ammo_text, (20, 86))
    screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 18))
    screen.blit(round_text, (WIDTH - round_text.get_width() - 20, 52))
    screen.blit(malfunction_text, (WIDTH - malfunction_text.get_width() - 20, 88))

    if malfunction == 'WEAPON_OVERHEATING':
        heat_text = small_font.render(
            f"WEAPON HEAT: {int(weapon_heat)}%", True, (255, 120, 90)
        )
        screen.blit(heat_text, (20, 125))
        if overheated:
            warning = font.render(
                "WEAPON OVERHEATED", True, (255, 50, 50)
            )
            screen.blit(
                warning,
                (WIDTH - warning.get_width() - 20, 125)
            )

    if ammo == 0:
        reload_text = small_font.render(
            "OUT OF AMMO - EMERGENCY SUPPLY INCOMING",
            True, (255, 100, 100)
        )
        screen.blit(reload_text, (20, 155))

    if new_record:
        record_text = small_font.render(
            f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}",
            True, (120, 255, 170)
        )
        screen.blit(
            record_text,
            (WIDTH - record_text.get_width() - 20, 125)
        )

    effects.draw_overlay(screen, WIDTH, HEIGHT)
    pygame.display.flip()

pygame.quit()
