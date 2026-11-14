'''HAVEN GAMEJAM'''
import random
import time
import pygame
from settings import WIDTH, HEIGHT, FPS, PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED, BG_COLOUR
from player import Player
from bullet import Bullet
from enemy import Enemy
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True
malfunction = 'NONE'
bullets = []
score = 0
shot_timer = 0
player = Player(WIDTH/2, HEIGHT/2)
enemies =[Enemy(150,100)]

while running:
    dt = clock.tick(FPS) / 1000  #change in time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    player.update(dt, keys,malfunction)

    for enemy in enemies:
        enemy.update(dt,player.position)

    #shooting logic
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()
    shot_timer = max(0, shot_timer - dt) #decreases the timer and ensures that the value doesnt become negative
    

    if mouse_buttons[0] and shot_timer <= 0: #if the user clicks and time is left
        direction = pygame.Vector2(mouse_pos) - player.position

        if direction.length() > 0:
            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            shot_timer = 0.2

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

                break
    screen.fill(BG_COLOUR)
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
    pygame.display.flip() #the flip method updates the display
pygame.quit()