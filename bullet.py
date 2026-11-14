'''BULLET CLASS'''
import pygame
from settings import HEIGHT, WIDTH, BULLET_SPEED

class Bullet:
    def __init__(self, position, direction):
        self.position = pygame.Vector2(position)
        self.direction = direction.normalize() if direction.length() > 0 else direction #to deal with that normalize bug encountered earlier
        self.speed = BULLET_SPEED

        self.rect = pygame.Rect(0,0,8,8)
        self.rect.center = self.position

    def update(self, dt):
        self.position += self.direction * self.speed * dt
        self.rect.center = self.position

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 220, 90), self.rect.center, 4) 

    def is_off_screen(self):
        return not pygame.Rect(0, 0, WIDTH, HEIGHT).colliderect(self.rect)
