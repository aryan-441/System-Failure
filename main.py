
'''HAVEN GAMEJAM'''
import random
import time
import pygame

from settings import WIDTH, HEIGHT, FPS, PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED, BG_COLOUR
from player import Player
from bullet import Bullet
from enemy import Enemy
from enemy_spawner import EnemySpawner

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

running = True
malfunction = 'NONE'
bullets = []
score = 0
shot_timer = 0
damage_timer = 0

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

    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r and player.health <= 0:

                player = Player(WIDTH/2, HEIGHT/2)

                enemies = [
                    Enemy(150, 150),
                    Enemy(800, 150),
                    Enemy(150, 400)
                ]

                bullets = []
                score = 0
                shot_timer = 0
                damage_timer = 0
                malfunction = 'NONE'

                # RESET SPAWNER
                spawner = EnemySpawner()

    keys = pygame.key.get_pressed()

    if not running:
        break

    if player.health <= 0:

        screen.fill(BG_COLOUR)

        title = game_over_font.render("SYSTEM FAILURE", True, (255, 65, 85))
        score_display = font.render(f"FINAL SCORE: {score}", True, (255, 255, 255))
        restart = restart_font.render("PRESS R TO RESTART", True, (120, 200, 255))

        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT/2 - 70)))
        screen.blit(score_display, score_display.get_rect(center=(WIDTH/2, HEIGHT/2 + 10)))
        screen.blit(restart, restart.get_rect(center=(WIDTH/2, HEIGHT/2 + 70)))

        pygame.display.flip()
        continue

    player.update(dt, keys, malfunction)

    # AUTOMATIC ENEMY SPAWNING
    if spawner.update(dt):
        enemies.append(spawner.spawn())

    # ENEMY MOVEMENT
    for enemy in enemies:
        enemy.update(dt, player.position)

    # SHOOTING LOGIC
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()

    shot_timer = max(0, shot_timer - dt)
    damage_timer = max(0, damage_timer - dt)

    if mouse_buttons[0] and shot_timer <= 0:

        direction = pygame.Vector2(mouse_pos) - player.position

        if direction.length() > 0:

            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            shot_timer = 0.2

            if malfunction == 'RECOIL':
                player.apply_recoil(direction)

    # BULLET MOVEMENT
    for bullet in bullets[:]:

        bullet.update(dt)

        if bullet.is_off_screen():
            bullets.remove(bullet)

    # BULLET-ENEMY COLLISION
    for bullet in bullets[:]:

        for enemy in enemies[:]:

            if bullet.rect.colliderect(enemy.rect):

                bullets.remove(bullet)

                if enemy.take_damage(1):
                    enemies.remove(enemy)
                    score += 100

                break

    # PLAYER-ENEMY COLLISION
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

    # DRAWING
    screen.fill(BG_COLOUR)

    player.draw(screen)

    for enemy in enemies:
        enemy.draw(screen)

    for bullet in bullets:
        bullet.draw(screen)

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    health_text = font.render(f"Health: {player.health}", True, (255, 255, 255))

    screen.blit(score_text, (20, 20))
    screen.blit(health_text, (20, 60))

    pygame.display.flip()

pygame.quit()
