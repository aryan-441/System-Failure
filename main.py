'''HAVEN GAMEJAM'''
import random
import time
import pygame
from settings import WIDTH, HEIGHT, FPS, PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED, BG_COLOUR
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
round_manager = RoundManager()
malfunction = 'NONE'
bullets = []
score = 0
high_score = load_high_score()
previous_high_score = high_score
new_record = False
shot_timer = 0
damage_timer = 0
game_time = 0
first_failure_started = False
game_over_sound_played = False
ammo = 16
ammo_per_kill = 5
max_ammo = 24
empty_ammo_timer = 0
weapon_heat = 0
max_weapon_heat = 100
heat_per_shot = 5
cooling_rate = 9
overheated = False
stall_timer = 0
stall_duration = 1.5
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
enemies = [
    Enemy(150, 150),
    Enemy(800, 150),
    Enemy(150, 400)
]
for enemy in enemies:
    ship_sprites.prepare_enemy(enemy, allow_boss=False)

# ENEMY SPAWNER
spawner = EnemySpawner()
boss_spawn_cooldown = 20
last_boss_spawn = 0
max_enemies = 9

font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 24)
game_over_font = pygame.font.Font(None, 85)
restart_font = pygame.font.Font(None, 32)

while running:
    dt = min(clock.tick(FPS) / 1000, 0.05)  #change in time
    game_time += dt
    background.update(dt)  #bg updates after each line
    effects.update(dt)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN: #restarts
            if event.key == pygame.K_r and player.health <= 0:
                player = Player(WIDTH/2, HEIGHT/2)
                enemies = [
                    Enemy(150, 150),
                    Enemy(800, 150),
                    Enemy(150, 400)
                ]
                for enemy in enemies:
                    ship_sprites.prepare_enemy(enemy, allow_boss=False)
                bullets = []
                score = 0
                previous_high_score = high_score
                new_record = False
                shot_timer = 0
                damage_timer = 0
                round_manager = RoundManager()
                malfunction = 'NONE'
                game_time = 0
                first_failure_started = False
                game_over_sound_played = False
                ammo = 16
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
                spawner = EnemySpawner()
                last_boss_spawn = 0
                effects.reset()

    keys = pygame.key.get_pressed()

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
        high_score_display = font.render(f"HIGH SCORE: {high_score}", True, (255, 220, 90))

        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT/2 - 70)))
        screen.blit(score_display, score_display.get_rect(center=(WIDTH/2, HEIGHT/2 + 10)))
        screen.blit(restart, restart.get_rect(center=(WIDTH/2, HEIGHT/2 + 70)))
        screen.blit(high_score_display, high_score_display.get_rect(center=(WIDTH/2, HEIGHT/2 + 115)))

        if new_record:
            record_text = font.render(f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}", True, (120, 255, 170))
            screen.blit(record_text, record_text.get_rect(center=(WIDTH/2, HEIGHT/2 + 155)))

        pygame.display.flip()
        continue

    # No system errors for the first 15 seconds
    round_changed = round_manager.update(dt)

    if game_time >= 15 and not first_failure_started and round_manager.current_malfunction != 'NONE':
        first_failure_started = True
        malfunction = round_manager.current_malfunction
        effects.malfunction_changed(malfunction)
        audio.play("warning")
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
        audio.play("warning")

        stall_timer = 0
        is_stalled = False
        reactor_timer = 0
        reactor_impulse = pygame.Vector2(0, 0)
        reactor_active = False
        reactor_duration = 0.5
        weapon_heat = 0
        overheated = False

    if malfunction == 'ENGINE_STALLING':
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

    if malfunction == 'DAMAGED_THRUSTERS':
        player.speed = PLAYER_SPEED * 0.5
    else:
        player.speed = PLAYER_SPEED

    original_speed = player.speed

    if malfunction == 'ENGINE_STALLING' and is_stalled:
        player.speed = 0

    player.update(dt, keys,malfunction)

    player.speed = original_speed

    if malfunction == 'ENGINE_DRIFT':
        player.position += drift_direction * drift_speed * dt

    if malfunction == 'REACTOR_INSTABILITY' and reactor_active:
        player.position += reactor_impulse * 350 * dt

    half = player.rect.width / 2
    player.position.x = max(half, min(WIDTH - half, player.position.x))
    player.position.y = max(half, min(HEIGHT - half, player.position.y))
    player.rect.center = player.position

    enemies_per_second = min(0.55, 0.24 + game_time * 0.00172)
    spawner.spawn_interval = 1 / enemies_per_second

    # AUTOMATIC ENEMY SPAWNING
      
    if len(enemies) < max_enemies and spawner.update(dt):
        new_enemy = spawner.spawn()
        allow_boss = game_time >= 40 and game_time - last_boss_spawn >= boss_spawn_cooldown
        allow_boss = allow_boss and not any(enemy.is_boss for enemy in enemies)
        ship_sprites.prepare_enemy(new_enemy, allow_boss=allow_boss)

        if new_enemy.is_boss:
            last_boss_spawn = game_time

        enemies.append(new_enemy)

    for enemy in enemies:
        enemy.update(dt,player.position)

    separate_enemies(enemies, WIDTH, HEIGHT)

    #shooting logic
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()
    shot_timer = max(0, shot_timer - dt) #decreases the timer and ensures that the value doesnt become negative
    damage_timer = max(0, damage_timer - dt)

    if malfunction == 'WEAPON_OVERHEATING':
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

    if mouse_buttons[0] and shot_timer <= 0 and ammo > 0 and not overheated: #if the user clicks and time is left
        direction = pygame.Vector2(mouse_pos) - player.position

        if malfunction == 'TARGETING_GLITCH':
            direction = direction.rotate(random.uniform(-17, 17))

        if direction.length() > 0:
            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            effects.muzzle_flash(player.position, direction)
            audio.play("shoot")
            shot_timer = 0.2
            ammo -= 1

            if malfunction == 'WEAPON_OVERHEATING':
                weapon_heat = min(max_weapon_heat, weapon_heat + heat_per_shot)

                if weapon_heat >= max_weapon_heat:
                    overheated = True
                    audio.play("overheat")

            if malfunction == 'RECOIL':
                    player.apply_recoil(direction)

    if malfunction == 'WEAPON_OVERHEATING' and overheated:
        effects.smoke(player.position, dt)

    #aim_direction = pygame.Vector2(mouse_pos) - player.position
    for bullet in bullets[:]:   #slicing to loop over a copy
        bullet.update(dt)

        if bullet.is_off_screen():
            bullets.remove(bullet)

    for bullet in bullets[:]:
        for enemy in enemies[:]:  #nested list
            if bullet.rect.colliderect(enemy.rect):
                bullets.remove(bullet)
                enemy_last_tick = pygame.time.get_ticks()
                enemy.last_hit = enemy_last_tick
                effects.hit_enemy(enemy)
                audio.play("hit")

                if enemy.take_damage(1):
                    effects.enemy_destroyed(enemy)
                    audio.play("enemy_down")
                    enemies.remove(enemy)
                    score += 100
                    ammo = min(max_ammo, ammo + ammo_per_kill)

                    if score > high_score:
                        new_record = True
                        high_score = score
                        try:
                            get_high_score(high_score)
                        except OSError:
                            pass

                break
    collision = False

    for enemy in enemies:
        if enemy.rect.colliderect(player.rect):
            collision = True

            if damage_timer <= 0 and player.health > 0:
                if malfunction == 'SHIELD_MALFUNCTION':
                    damage = 2
                else:
                    damage = 1
                player.health = max(0, player.health - damage)
                damage_timer = 1
                effects.player_hit(player.position, damage)
                audio.play("player_hit")
            break

    if collision:
        pygame.display.set_caption("COLLISION DETECTED!")
    else:
        pygame.display.set_caption("SYSTEM FAILURE: Bounce Back")
        
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
        malfunction_text = small_font.render(f"FIRST FAILURE IN {max(0, int(16 - game_time))}s", True, (255, 120, 130))
    else:
        round_text = font.render(f"ROUND: {round_manager.round_number}", True, (255, 255, 255))
        malfunction_text = small_font.render(f"SYSTEM ERROR: {malfunction.replace('_', ' ')}", True, (255, 120, 130))

    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))
    screen.blit(ammo_text, (20, 100))
    screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 20))
    screen.blit(round_text, (WIDTH - round_text.get_width() - 20, 60))
    screen.blit(malfunction_text, (WIDTH - malfunction_text.get_width() - 20, 100))

    if malfunction == 'WEAPON_OVERHEATING':
        heat_text = font.render(f"Weapon Heat: {int(weapon_heat)}%", True, (255, 100, 80))
        screen.blit(heat_text, (WIDTH - heat_text.get_width() - 20, 180))

        if overheated:
            warning = font.render("WEAPON OVERHEATED!", True, (255, 50, 50))
            screen.blit(warning, (WIDTH - warning.get_width() - 20, 220))

    if ammo == 0:
        reload_text = font.render("OUT OF AMMO - EMERGENCY SUPPLY INCOMING", True, (255, 80, 80))
        screen.blit(reload_text, (20, 140))

    if new_record:
        record_text = font.render(f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}", True, (120, 255, 170))
        screen.blit(record_text, (WIDTH - record_text.get_width() - 20, 140))

    effects.draw_overlay(screen, WIDTH, HEIGHT)
    pygame.display.flip() #the flip method updates the display
pygame.quit()
