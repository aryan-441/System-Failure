'''PLAYER CLASS'''
import pygame

from settings import (
    PLAYER_SIZE, PLAYER_COLOUR, PLAYER_SPEED, WIDTH, HEIGHT,
    RECOIL_IMPULSE, RECOIL_DAMPING
)


class Player:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.speed = PLAYER_SPEED
        self.health = 5
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = self.position
        self.recoil_velocity = pygame.Vector2(0, 0)

    def update(self, dt, keys, malfunction='NONE'):
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1

        if malfunction == 'REVERSED':
            direction *= -1

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.position += direction * self.speed * dt

        # Recoil is a velocity, so apply it before damping it.
        self.position += self.recoil_velocity * dt
        self.recoil_velocity *= max(0, 1 - RECOIL_DAMPING * dt)

        half = PLAYER_SIZE / 2
        self.position.x = max(half, min(WIDTH - half, self.position.x))
        self.position.y = max(half, min(HEIGHT - half, self.position.y))
        self.rect.center = self.position

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_COLOUR, self.rect)

    def apply_recoil(self, direction):
        if direction.length_squared() > 0:
            self.recoil_velocity -= direction.normalize() * RECOIL_IMPULSE
