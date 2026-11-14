'''HAVEN GAMEJAM'''
import random
import time
import pygame
from settings import WIDTH, HEIGHT, FPS, PLAYER_SPEED, ENEMY_SPEED, BULLET_SPEED, BG_COLOUR
from player import Player
from bullet import Bullet
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True

player = Player(WIDTH/2, HEIGHT/2)

while running:
    dt = clock.tick(FPS) / 2000  #change in time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    player.update(dt, keys)

    #shooting logic
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()
    
    bullets = []
    shot_timer = 0

    if mouse_buttons[0] and shot_timer <= 0: #if the user clicks and time is left
        direction = pygame.Vector2(mouse_pos) - player.position

        if direction.length() > 0:
            bullet = Bullet(player.position, direction)
            bullets.append(bullet)
            shot_timer = 0.2

    aim_direction = pygame.Vector2(mouse_pos) - player.position
    screen.fill(BG_COLOUR)
    player.draw(screen)
    pygame.draw.line(
    screen,
    (100, 220, 255), #rgb colour
    player.position,
    mouse_pos,
    2
)
    pygame.display.flip() #the flip method updates the display
pygame.quit()
