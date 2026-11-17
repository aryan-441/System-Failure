
import pygame


class Enemy:
    def __init__(self, x, y, enemy_type='normal'):
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.center = self.position
        self.speed = 100
        self.health = 3
        self.max_health = 3
        self.image = None
        self.ship_image = None
        self.is_boss = False
        self.last_hit = -1000
        self.hit_flash_timer = 0.0
        self.enemy_type = enemy_type

        if self.enemy_type == 'interceptor':
            self.speed = 170
            self.health = 2
            self.rect.size = (32, 32)

        elif self.enemy_type == 'ranger':
            self.speed = 85
            self.health = 2
            self.rect.size = (36, 36)
            self.fire_timer = 1.5

        elif self.enemy_type == 'bomber':
            self.speed = 155
            self.health = 1
            self.rect.size = (30, 30)

        self.max_health = self.health
        self.rect.center = self.position

    def update(self, dt, player_position):
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        direction = player_position - self.position
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()

            if self.enemy_type == 'ranger':
                if distance > 350:
                    self.position += direction * self.speed * dt

                elif distance < 250:
                    self.position -= direction * self.speed * dt

            else:
                self.position += direction * self.speed * dt

        if self.enemy_type == 'ranger':
            self.fire_timer -= dt

        self.rect.center = self.position

    def take_damage(self, amount):
        self.health -= amount
        self.last_hit = pygame.time.get_ticks()
        self.hit_flash_timer = 0.17
        return self.health <= 0

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)

        for index in range(self.max_health):
            colour = (255, 70, 80) if index < self.health else (65, 65, 80)

            pygame.draw.rect(
                screen,
                colour,
                (self.rect.x + index * 14, self.rect.y - 9, 12, 4)
            )
