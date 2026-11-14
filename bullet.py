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

        head = self.position
        tail = self.position - self.direction * 26

        pygame.draw.line(screen, (15, 65, 110), tail, head, 12)
        pygame.draw.line(screen, (30, 180, 255), tail, head, 7)
        pygame.draw.line(screen, (240, 250, 255), tail, head, 3)  #laser effect through rgb colours of varying thickness
 

    def is_off_screen(self):
        return not pygame.Rect(0, 0, WIDTH, HEIGHT).colliderect(self.rect)
