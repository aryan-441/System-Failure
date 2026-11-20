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
    radius = 46 + round(2 * math.sin(age * 4)) #smooth oscillation
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


def draw_gun_charge(screen, position, target, progress):
    direction = target - position
    if direction.length_squared() == 0:
        direction = pygame.Vector2(0, 1)
    else:
        direction = direction.normalize()
    side = direction.rotate(90)
    glow = pygame.Surface((100, 100), pygame.SRCALPHA)
    centre = pygame.Vector2(50, 50)
    for sign in (-1, 1):
        mount = centre + side * (17 * sign) + direction * 8
        muzzle = mount + direction * (12 + 5 * progress)
        pygame.draw.line(glow, (52, 78, 94), mount, muzzle, 7)
        pygame.draw.circle(glow, (255, 152, 54, 60), muzzle, round(5 + 7 * progress))
        pygame.draw.circle(glow, (255, 237, 172), muzzle, round(2 + 4 * progress))
        for index in range(3):
            travel = (progress * 2 + index / 3) % 1
            spoke = direction.rotate(sign * (index - 1) * 55)
            spark = muzzle + spoke * (19 * (1 - travel))
            pygame.draw.line(glow, (255, 197, 96, 190), spark, spark + spoke * 3, 2)
    screen.blit(glow, glow.get_rect(center=position))


class StoryHUD:
    def __init__(self):
        self.label = pygame.font.Font(None, 18)
        self.body = pygame.font.Font(None, 23)
        self.title = pygame.font.Font(None, 30)

    def draw_part_marker(self, surface, position, ship, age, unlocked):
        colour = (110, 249, 206) if unlocked else (116, 138, 158)
        pulse = (math.sin(age * 5) + 1) / 2
        radius = round(28 + 6 * pulse) if unlocked else 21
        for i in range(4):
            direction = pygame.Vector2(1, 0).rotate(45 + i * 90)
            corner = position + direction * radius
            for axis in ((direction.x, 0), (0, direction.y)):
                pygame.draw.line(surface, colour, corner, corner - pygame.Vector2(axis) * 10, 2)
        if unlocked:
            offset = position - ship
            if offset.length() > 80:
                direction = offset.normalize()
                tip = ship + direction * 43
                pygame.draw.polygon(surface, colour, [tip, tip - direction.rotate(32) * 14,
                                                       tip - direction.rotate(-32) * 14])
            text = self.label.render('COLLECT', True, colour, (10, 24, 32))
            surface.blit(text, text.get_rect(midtop=(position.x, position.y + 28)))

    def draw_repair(self, surface, position, remaining):
        age = 1 - remaining
        aura = pygame.Surface((132, 132), pygame.SRCALPHA)
        green = (102, 255, 163, round(245 * remaining))
        pygame.draw.circle(aura, green, (66, 66), round(35 + age * 28), 3)
        for x, y in ((37, 58), (87, 42), (79, 87)):
            y -= round(18 * age)
            pygame.draw.line(aura, green, (x-4, y), (x+4, y), 3)
            pygame.draw.line(aura, green, (x, y-4), (x, y+4), 3)
        surface.blit(aura, aura.get_rect(center=position))

    def draw_departure(self, screen, ships, age):
        for index, (image, origin) in enumerate(ships):
            time = max(0, age - 0.24 - index * 0.09)
            progress = min(1, time / 1.45)
            thrust = progress ** 2
            lift = math.sin(progress * math.pi) * (36 + 8 * index)
            x = origin.x + (WIDTH + 160 - origin.x) * thrust
            y = origin.y - lift
            plume = round(5 + 95 * thrust)
            nozzle = pygame.Vector2(x - image.get_width() * 0.36, y)
            if time > 0:
                for offset in (-7, 7):
                    tip = nozzle + (0, offset)
                    pygame.draw.polygon(screen, (45, 123, 172), [tip + (1, -4), tip - (plume, 0), tip + (1, 4)])
                    pygame.draw.line(screen, (173, 250, 255), tip, tip - (plume * 0.65, 0), 2)
            banked = pygame.transform.rotozoom(image, -14 * math.sin(progress * math.pi), 1)
            screen.blit(banked, banked.get_rect(center=(round(x), round(y))))

    def meter(self, surface, x, label, value, limit, colour):
        surface.blit(self.label.render(label, True, colour), (x, 7))
        number = self.body.render(f'{value} / {limit}', True, (237, 244, 246))
        surface.blit(number, number.get_rect(topright=(x+122, 4)))
        for i in range(limit):
            left = x + i * 122 // limit
            right = x + (i+1) * 122 // limit
            pygame.draw.rect(surface, colour if i < value else (49, 66, 82), (left, 26, right-left-1, 5))

    def draw(self, screen, story, health, ammo, hp_limit, ammo_limit, debuff, description):
        phase = story.phase.name
        teal = (114, 239, 207)
        amber = (255, 183, 109)
        white = (231, 241, 247)
        muted = (161, 184, 202)
        recovery = phase in ('RECOVERY', 'RECOVERY_COMPLETE')
        wave = story.objective_index + 1
        if recovery:
            target = story.objectives[story.objective_index]['target']
            heading = f'PHASE 02   /   RECOVERY      WAVE {wave} OF 6'
            title = 'Clear the sector'
            detail = f'{story.objective_progress} / {target} hostiles destroyed'
            step = story.recovery_step.name
            if phase == 'RECOVERY_COMPLETE':
                title, detail = 'Ship reassembled', 'All six components secured'
            elif step == 'PICKUP':
                title, detail = 'Retrieve the component', 'Fly into the green beacon'
            elif step == 'RETURNING':
                title, detail = 'Reattaching component', 'Docking sequence in progress'
            elif step == 'INTERMISSION':
                seconds = math.ceil(story.intermission_timer)
                title = 'Component secured'
                detail = f'Next wave in {seconds}s' if wave < 6 else f'Recovery complete in {seconds}s'
            accent = teal
        else:
            heading = 'PHASE 01   /   FIRST CONTACT'
            title = 'Engage the escorts'
            shield = 'Shield active' if story.shielded else 'Core exposed'
            seconds = max(0, math.ceil(story.opening_duration - story.phase_time))
            detail = f'{shield}    /    Survive {seconds}s'
            if story.charge_start <= story.phase_time < story.charge_start + story.charge_duration:
                title = 'Cannons charging'
            if phase == 'SCRIPTED_DEFEAT':
                title, detail = 'Hull breach', 'Hostiles withdrawing'
            accent = amber
        mission = pygame.Surface((280, 76), pygame.SRCALPHA)
        pygame.draw.polygon(mission, (8, 19, 34, 227), [(0,0),(280,0),(280,59),(263,76),(0,76)])
        pygame.draw.line(mission, accent, (1, 1), (1, 73), 3)
        mission.blit(self.label.render(heading, True, accent), (12, 6))
        mission.blit(self.title.render(title, True, white), (11, 23))
        mission.blit(self.label.render(detail, True, muted), (12, 53))
        screen.blit(mission, (12, 10))

        dock = pygame.Surface((WIDTH, 42), pygame.SRCALPHA)
        dock.fill((7, 16, 30, 233))
        pygame.draw.line(dock, (57, 83, 100), (0,0), (WIDTH,0))
        self.meter(dock, 18, 'HULL', health, hp_limit, amber if health <= 2 else teal)
        self.meter(dock, 164, 'AMMO', ammo, ammo_limit, amber if ammo <= 3 else (130, 196, 253))
        if recovery:
            dock.blit(self.label.render('COMPONENTS', True, muted), (318, 6))
            for index, part in enumerate(story.ship.parts[1:]):
                x = 320 + index * 15
                colour = teal if part.attached else (65, 85, 102)
                pygame.draw.polygon(dock, colour, [(x,24),(x+9,24),(x+6,31),(x-3,31)])
        if debuff != 'NONE':
            name = self.body.render(debuff.replace('_', ' '), True, amber)
            dock.blit(name, name.get_rect(topright=(WIDTH-16, 3)))
            text = self.label.render(description, True, muted)
            dock.blit(text, text.get_rect(topright=(WIDTH-16, 23)))
        screen.blit(dock, (0, HEIGHT-42))

        if story.wave_clear_timer > 0:
            panel = pygame.Surface((226, 44), pygame.SRCALPHA)
            pygame.draw.polygon(panel, (11, 44, 48, 239), [(0,0),(226,0),(213,44),(13,44)])
            pygame.draw.line(panel, teal, (13,42), (213,42), 2)
            message = self.title.render(f'WAVE {wave} CLEARED', True, teal)
            panel.blit(message, message.get_rect(center=(113,22)))
            panel.set_alpha(round(255 * min(1, story.wave_clear_timer / 0.35)))
            screen.blit(panel, panel.get_rect(midtop=(WIDTH//2, 14)))
