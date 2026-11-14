
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
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
background = SpaceBackground(WIDTH, HEIGHT)
running = True
malfunction = 'NONE'
bullets = []
score = 0
high_score = load_high_score()
previous_high_score = high_score
new_record = False
shot_timer = 0
damage_timer = 0
ammo = 16
ammo_per_kill = 4
max_ammo = 24
empty_ammo_timer = 0
player = Player(WIDTH/2, HEIGHT/2)
enemies = [
    Enemy(150, 150),
    Enemy(800, 150),
    Enemy(150, 400)
]

# ENEMY SPAWNER
spawner = EnemySpawner()

font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 85)
restart_font = pygame.font.Font(None, 32)

while running:
    dt = clock.tick(FPS) / 1000  #change in time
    background.update(dt)  #bg updates after each line
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
                bullets = []
                score = 0
                previous_high_score = high_score
                new_record = False
                shot_timer = 0
                damage_timer = 0
                malfunction = 'NONE'
                ammo = 18
                empty_ammo_timer = 0

                # RESET SPAWNER
                spawner = EnemySpawner()

    keys = pygame.key.get_pressed()

    if not running:
        break

    if player.health <= 0:
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

    player.update(dt, keys,malfunction)

    if score >= 2000:
        spawner.spawn_interval = 1.0
    elif score >= 1000:
        spawner.spawn_interval = 1.5
    elif score >= 500:
        spawner.spawn_interval = 2.0
    else:
        spawner.spawn_interval = 2.5

    # AUTOMATIC ENEMY SPAWNING
    if spawner.update(dt):
        enemies.append(spawner.spawn())

    for enemy in enemies:
        enemy.update(dt,player.position)

    #shooting logic
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()
    shot_timer = max(0, shot_timer - dt) #decreases the timer and ensures that the value doesnt become negative
    damage_timer = max(0, damage_timer - dt)

    if ammo == 0 and len(bullets) == 0:
        empty_ammo_timer += dt

        if empty_ammo_timer >= 5:
            ammo = 3
            empty_ammo_timer = 0
    else:
        empty_ammo_timer = 0

    if mouse_buttons[0] and shot_timer <= 0 and ammo > 0: #if the user clicks and time is left
        direction = pygame.Vector2(mouse_pos) - player.position

        if direction.length() > 0:
            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            shot_timer = 0.2
            ammo -= 1

            if malfunction == 'RECOIL':
                    player.apply_recoil(direction)

    #aim_direction = pygame.Vector2(mouse_pos) - player.position
    for bullet in bullets[:]:   #slicing to loop over a copy
        bullet.update(dt)

        if bullet.is_off_screen():
            bullets.remove(bullet)

    for bullet in bullets[:]:
        for enemy in enemies[:]:  #nested list
            if bullet.rect.colliderect(enemy.rect):
                bullets.remove(bullet)

                if enemy.take_damage(1):
                    enemies.remove(enemy)
                    score += 100
                    ammo = min(max_ammo, ammo + ammo_per_kill)

                    if score > high_score:
                        new_record = True
                        high_score = score
                        get_high_score(high_score)

                break
    collision = False

    for enemy in enemies:
        if enemy.rect.colliderect(player.rect):
            collision = True

            if damage_timer <= 0 and player.health > 0:
                player.health -= 1
                damage_timer = 1
            break

    if collision:
        pygame.display.set_caption("COLLISION DETECTED!")
    else:
        pygame.display.set_caption("SYSTEM FAILURE: Bounce Back")

    screen.fill(BG_COLOUR)
    background.draw(screen)
    player.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)

    for bullet in bullets:
         bullet.draw(screen)
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

    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))
    screen.blit(ammo_text, (20, 100))
    screen.blit(high_score_text, (20, 180))

    if ammo == 0:
        reload_text = font.render("OUT OF AMMO - EMERGENCY SUPPLY INCOMING", True, (255, 80, 80))
        screen.blit(reload_text, (20, 140))

    if new_record:
        record_text = font.render(f"NEW HIGH SCORE! PREVIOUS: {previous_high_score}", True, (120, 255, 170))
        screen.blit(record_text, (20, 220))

    pygame.display.flip() #the flip method updates the display
pygame.quit()
