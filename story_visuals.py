import math
import random

import pygame

from settings import HEIGHT, WIDTH


class Fragment:
    def __init__(self, image, position, velocity):
        self.image = image
        self.position = pygame.Vector2(position)
        self.velocity = velocity
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-105, 105)

    def update(self, dt):
        self.position += self.velocity * dt
        self.angle = (self.angle + self.rotation_speed * dt) % 360
        if self.velocity.length_squared() > 16:
            self.velocity *= math.exp(-1.4 * dt)
        for axis, limit in enumerate((WIDTH, HEIGHT)):
            if self.position[axis] < 7 or self.position[axis] > limit - 7:
                self.position[axis] = max(7, min(limit - 7, self.position[axis]))
                self.velocity[axis] *= -1

    def draw(self, screen):
        sprite = pygame.transform.rotate(self.image, self.angle)
        screen.blit(sprite, sprite.get_rect(center=self.position))


def scatter_wreckage(source, centre, angle):
    pixels = [(x, y) for y in range(4, source.get_height() - 4)
              for x in range(4, source.get_width() - 4) if source.get_at((x, y)).a > 150]
    fragments = []
    for index in range(32):
        x, y = random.choice(pixels)
        w, h = random.randint(4, 8), random.randint(3, 7)
        crop = pygame.Rect(0, 0, w, h)
        crop.center = (x, y)
        image = source.subsurface(crop).copy()
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255), [(0, h//2), (w//2, 0), (w-1, 1), (w-2, h-1)])
        image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        offset = (pygame.Vector2(x, y) - source.get_rect().center).rotate(-angle)
        direction = pygame.Vector2(1, 0).rotate(index * 360 / 32 + random.uniform(-4, 4))
        fragments.append(Fragment(image, centre + offset, direction * random.uniform(75, 225)))
    return fragments


def draw_shield(screen, position, age, flash):
    aura = pygame.Surface((116, 116), pygame.SRCALPHA)
    centre = (58, 58)
    radius = 46 + round(2 * math.sin(age * 4))
    pygame.draw.circle(aura, (70, 185, 255, 22), centre, radius + 6)
    pygame.draw.circle(aura, (110, 225, 255, 80), centre, radius + 2, 3)
    pygame.draw.circle(aura, (185, 250, 255, 220), centre, radius, 1)
    ring = pygame.Rect(0, 0, radius*2, radius*2)
    ring.center = centre
    for i in range(3):
        start = age * 0.7 + i * math.tau / 3
        pygame.draw.arc(aura, (220, 255, 255, 245), ring, start, start + 0.65, 3)
    if flash > 0:
        pygame.draw.circle(aura, (220, 255, 255, min(200, int(850 * flash))), centre, radius - 1, 5)
    screen.blit(aura, aura.get_rect(center=position))


class StoryHUD:
    def __init__(self):
        self.label = pygame.font.Font(None, 18)
        self.body = pygame.font.Font(None, 23)
        self.notice = 0.0
        self.previous_count = 0

    def panel(self, screen, x, width, heading, title, detail, footer, accent):
        surface = pygame.Surface((width, 90), pygame.SRCALPHA)
        points = [(0, 0), (width-1, 0), (width-1, 78), (width-12, 89), (0, 89)]
        pygame.draw.polygon(surface, (8, 17, 32, 216), points)
        pygame.draw.lines(surface, (*accent, 120), True, points, 1)
        pygame.draw.line(surface, accent, (0, 0), (42, 0), 3)
        for font, text, y, colour in [(self.label, heading, 7, accent),
                                      (self.body, title, 24, (235, 244, 255)),
                                      (self.label, detail, 47, (198, 215, 230)),
                                      (self.label, footer, 67, accent)]:
            image = font.render(text, True, colour)
            if image.get_width() > width - 20:
                image = pygame.transform.smoothscale(image, (width-20, image.get_height()))
            surface.blit(image, (10, y))
        screen.blit(surface, (x, 10))

    def draw(self, screen, story, health, ammo, hp_limit, ammo_limit, debuff, description):
        phase = story.phase.name
        count = sum(p.attached for p in story.ship.parts[1:]) if phase in ('RECOVERY', 'RECOVERY_COMPLETE') else 0
        if count > self.previous_count:
            self.notice = story.phase_time + 1.25
        self.previous_count = count
        accent = (110, 223, 222)
        heading = 'STORY MODE'
        if phase == 'OPENING':
            title = 'Adaptive core inbound'
            detail = story.boss_ai.phase_name + ('   /   SHIELDED' if story.shielded else '   /   EXPOSED')
            footer = f'Evade contact   /   {max(0, math.ceil(story.opening_duration-story.phase_time))}s'
            accent = (255, 153, 115)
        elif phase == 'SCRIPTED_DEFEAT':
            title, detail, footer = 'Hull breach', 'Cockpit separating', 'Flight controls restarting'
        else:
            heading += f'    /    WAVE {story.objective_index+1:02}/06'
            objective = story.objectives[story.objective_index]
            step = story.recovery_step.name
            if phase == 'RECOVERY_COMPLETE':
                title, detail = 'Ship reassembled', 'All components secured'
            elif step == 'PICKUP':
                title, detail = 'Component located', 'Fly into the marked component'
            elif step == 'RETURNING':
                title, detail = 'Component returning', 'Reattachment in progress'
            else:
                title = objective['description']
                if objective['type'] == 'reach':
                    distance = story.ship.centre.distance_to(objective['target'])
                    detail = f'Signal distance   {round(distance)} px'
                elif objective['type'] == 'survive':
                    detail = f"Survived   {int(story.objective_timer)}/{objective['target']}s"
                else:
                    detail = f"Confirmed kills   {story.objective_progress}/{objective['target']}"
            footer = f'SHIP RECOVERY   {count}/6'
            if self.notice > story.phase_time:
                footer += '    + COMPONENT SECURED'
        self.panel(screen, 10, 248, heading, title, detail, footer, accent)
        active = debuff and debuff != 'NONE'
        warning = 'HULL CRITICAL' if health <= 2 else 'AMMO LOW' if ammo <= 3 else 'FLIGHT SYSTEMS'
        self.panel(screen, WIDTH-234, 224, warning, f'Hull {health}/{hp_limit}    Ammo {ammo}/{ammo_limit}',
                   debuff.replace('_', ' ') if active else 'SYSTEM STATUS',
                   description if active else 'No active malfunction',
                   (255, 157, 110) if warning != 'FLIGHT SYSTEMS' else (155, 196, 244))
