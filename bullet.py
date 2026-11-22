'''BULLET CLASS'''
import pygame
from settings import HEIGHT, WIDTH, BULLET_SPEED

class Bullet:
    def __init__(self, position, direction):
        self.position = pygame.Vector2(position)
        self.direction = direction.normalize() if direction.length() > 0 else direction #to deal with that normalize bug encountered earlier
        self.speed = BULLET_SPEED
        self.hit_targets = set()
        self.pierce_remaining = 0
        self.is_opening_core_shot = False
        self.is_ranger_shot = False

        self.rect = pygame.Rect(0,0,8,8)
        self.rect.center = self.position
        self.previous_rect = self.rect.copy()

    def update(self, dt):
        self.previous_rect.center = self.rect.center
        self.position += self.direction * self.speed * dt
        self.rect.center = self.position

    
        
    def draw(self, screen):

        head = self.position
        tail = self.position - self.direction * 26

        pygame.draw.line(screen, (15, 65, 110), tail, head, 12)
        pygame.draw.line(screen, (30, 180, 255), tail, head, 7)
        pygame.draw.line(screen, (240, 250, 255), tail, head, 3)  #laser effect through rgb colours of varying thickness
 

    def overlaps(self, rect):
        return self.previous_rect.colliderect(rect) or self.rect.colliderect(rect)

    def intersects_shot(self,other):
        start = (self.previous_rect.centerx - other.previous_rect.centerx, self.previous_rect.centery - other.previous_rect.centery)

        end = (
            self.rect.centerx - other.rect.centerx,
            self.rect.centery - other.rect.centery
        )
        
        hitbox = pygame.Rect(
            0,0,self.rect.width + other.rect.width, self.rect.height + other.rect.height
        )
        hitbox.center = (0,0)
        return bool(hitbox.clipline(start, end))
    
    def is_off_screen(self):
        return not pygame.Rect(0, 0, WIDTH, HEIGHT).colliderect(self.rect)
