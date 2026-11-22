
import pygame

from settings import WIDTH, HEIGHT
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
        self.is_adaptive_boss = False
        self.is_story_miniboss = False
        self.miniboss_kind = None
        self.is_phasing = False
        self.special_timer = 0.0
        self.last_hit = -1000
        self.hit_flash_timer = 0.0
        self.enemy_type = enemy_type

        if self.enemy_type == 'interceptor':
            self.speed = 185
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
        elif self.enemy_type == 'rift_stalker':
            self.speed = 170
            self.health = 5
            self.rect.size = (44, 44)
            self.special_timer = 1.8
        elif self.enemy_type == 'siege_walker':
            self.speed = 58
            self.health = 8
            self.rect.size = (58, 58)
            self.fire_timer = 1.0
        elif self.enemy_type == 'phase_wraith':
            self.speed = 150
            self.health = 5
            self.rect.size = (44, 44)
            self.special_timer = 0.0

        self.max_health = self.health
        self.rect.center = self.position

    def update(self, dt, player_position, strategy=None, boss_phase=1):
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        if self.enemy_type == 'rift_stalker':
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.position.update(player_position)
                self.position += pygame.Vector2(1, 0).rotate(pygame.time.get_ticks() % 360) * 165
                self.position.x = max(35, min(WIDTH - 35, self.position.x))
                self.position.y = max(35, min(HEIGHT - 35, self.position.y))
                self.special_timer = 2.1
        elif self.enemy_type == 'phase_wraith':
            self.special_timer += dt
            self.is_phasing = self.special_timer % 2.4 < 0.65
        direction = player_position - self.position
        distance = direction.length()

        if distance > 0:
            direction = direction.normalize()

            if self.is_boss and strategy is not None:
                perpendicular = pygame.Vector2(-direction.y, direction.x)
                if boss_phase == 1:
                    movement = direction
                    speed_multiplier = 1.0
                elif boss_phase == 2:
                    if strategy == 'AGGRESSIVE':
                        movement = direction * 0.25 + perpendicular
                    elif strategy == 'STATIONARY':
                        movement = direction * 1.35
                    else:
                        movement = direction * 0.35 + perpendicular * 0.9
                    speed_multiplier = 1.15
                else:
                    movement = direction * 0.55 + perpendicular * 1.15
                    speed_multiplier = 1.55

                if movement.length_squared() > 0:
                    self.position += movement.normalize() * self.speed * speed_multiplier * dt
            elif self.enemy_type in ('ranger', 'siege_walker'):
                if distance > 350:
                    self.position += direction * self.speed * dt

                elif distance < (250 if self.enemy_type == 'ranger' else 300):
                    self.position -= direction * self.speed * dt

            else:
                self.position += direction * self.speed * dt

        if self.enemy_type == 'ranger':
            self.fire_timer -= dt
            self.position.x = max(20,min(WIDTH-20,self.position.x))
            self.position.y=max(20,min(HEIGHT-20,self.position.y))
        elif self.enemy_type == 'siege_walker':
            self.fire_timer -= dt
            self.position.x = max(30,min(WIDTH-30,self.position.x))
            self.position.y=max(30,min(HEIGHT-30,self.position.y))

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
