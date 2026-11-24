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


def draw_collector_assembly(screen, centre, cores, progress):
    progress = min(1, progress)
    glow = pygame.Surface((280, 280))
    origin = pygame.Vector2(140, 140)
    intensity = math.sin(progress * math.pi) ** 0.7
    radius = round(116 - progress * 74)
    for size in range(125, 0, -6):
        light = int(42 * intensity * (1 - size / 126) ** 2)
        pygame.draw.circle(glow, (light, light // 4, light // 2), origin, size)
    arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    arc_rect.center = origin
    for index in range(3):
        angle = index * math.tau / 3 + progress * 3.8
        pygame.draw.arc(glow, (165, 70, 94), arc_rect, angle, angle + 0.75, 2)
        for spark in range(4):
            travel = (progress * 1.7 + spark / 4) % 1
            direction = pygame.Vector2(1, 0).rotate_rad(angle - travel * 0.8)
            tip = origin + direction * (radius + 28 - travel * 65)
            pygame.draw.line(glow, (196, 104, 74), tip, tip + direction.rotate(18) * 6, 2)
    if progress > 0.85:
        pulse = (progress - 0.85) / 0.15
        pygame.draw.circle(glow, (190, 125, 84), origin, round(18 + 91 * pulse), 2)
    screen.blit(glow, glow.get_rect(center=centre), special_flags=pygame.BLEND_RGB_ADD)
    for core in cores:
        inward = centre - core.position
        if inward.length_squared() > 70 ** 2:
            tail = inward.normalize() * (10 + 24 * intensity)
            pygame.draw.line(screen, (125, 65, 91), core.position - tail * 2, core.position, 3)
            pygame.draw.line(screen, (246, 169, 114), core.position - tail, core.position, 2)


def draw_minion_arrival(screen, enemy, age):
    progress = min(1, age / 0.65)
    glow = pygame.Surface((120, 100))
    origin = pygame.Vector2(60, 50)
    intensity = 1 - progress
    width = round(20 + 65 * progress)
    height = round(55 * intensity + 7)
    ring = pygame.Rect(0, 0, width, height)
    ring.center = origin
    for pad, blue in ((16, 40), (8, 85), (0, 225)):
        colour = (int(blue * intensity * 0.42), int(blue * intensity * 0.72), int(blue * intensity))
        pygame.draw.ellipse(glow, colour, ring.inflate(pad, pad), 2 if pad == 0 else 4)
    for offset in (-12, 0, 12):
        start = origin + (0, offset)
        heading = 1 if enemy.entry_origin.x < WIDTH / 2 else -1
        tip = start + (heading * (12 + 34 * progress), 0)
        pygame.draw.line(glow, (int(90 * intensity), int(180 * intensity), int(240 * intensity)), start, tip, 2)
    screen.blit(glow, glow.get_rect(center=enemy.entry_origin), special_flags=pygame.BLEND_RGB_ADD)


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
        self.ending_title = pygame.font.Font(None, 64)
        self.gains = {}
        self.gain_duration = 0.85

    def add_gain(self, label, amount):
        if amount > 0:
            previous, _ = self.gains.get(label, (0, 0))
            self.gains[label] = (previous + amount, self.gain_duration)

    def update_gains(self, dt):
        self.gains = {label: (amount, time - dt) for label, (amount, time) in self.gains.items()
                      if time > dt}

    def draw_victory(self, screen):
        screen.fill((8, 19, 34))
        for font, text, colour, y in (
            (self.ending_title, 'MISSION ACCOMPLISHED', (114, 239, 207), 151),
            (self.title, 'THE COLLECTOR HAS BEEN DESTROYED', (231, 241, 247), 220),
            (self.body, 'You survived the System Failure.', (194, 215, 225), 271),
            (self.body, 'Cockpit recovered. Returned to base safely.', (194, 215, 225), 300),
            (self.body, 'R  Replay Story Mode      A  Play Arcade Mode      Esc  Main menu', (114, 239, 207), 399),
        ):
            line = font.render(text, True, colour)
            screen.blit(line, line.get_rect(center=(WIDTH // 2, y)))

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

    def draw_departure(self, screen, ships, age, direction=1):
        exit_x = WIDTH + 160 if direction > 0 else -160
        for index, (image, origin) in enumerate(ships):
            time = max(0, age - 0.24 - index * 0.09)
            progress = min(1, time / 1.45)
            thrust = progress ** 2
            lift = math.sin(progress * math.pi) * (36 + 8 * index)
            x = origin.x + (exit_x - origin.x) * thrust
            y = origin.y - lift
            plume = round(5 + 95 * thrust)
            nozzle = pygame.Vector2(x - direction * image.get_width() * 0.36, y)
            if time > 0:
                for offset in (-7, 7):
                    tip = nozzle + (0, offset)
                    pygame.draw.polygon(screen, (45, 123, 172), [tip + (direction, -4), tip - (direction * plume, 0), tip + (direction, 4)])
                    pygame.draw.line(screen, (173, 250, 255), tip, tip - (direction * plume * 0.65, 0), 2)
            banked = pygame.transform.rotozoom(image, -direction * 14 * math.sin(progress * math.pi), 1)
            screen.blit(banked, banked.get_rect(center=(round(x), round(y))))

    def meter(self, surface, x, label, value, limit, colour):
        surface.blit(self.label.render(label, True, colour), (x, 7))
        number = self.body.render(f'{value} / {limit}', True, (237, 244, 246))
        surface.blit(number, number.get_rect(topright=(x+122, 4)))
        if limit > 40:
            pygame.draw.rect(surface, (49, 66, 82), (x, 26, 122, 5))
            pygame.draw.rect(surface, colour, (x, 26, round(122 * value / limit), 5))
            return
        for i in range(limit):
            left = x + i * 122 // limit
            right = x + (i+1) * 122 // limit
            pygame.draw.rect(surface, colour if i < value else (49, 66, 82), (left, 26, right-left-1, 5))

    def draw(self, screen, story, health, ammo, hp_limit, ammo_limit, debuff, description, heat_percent, overheated):
        phase = story.phase.name
        teal = (114, 239, 207)
        amber = (255, 183, 109)
        white = (231, 241, 247)
        muted = (161, 184, 202)
        recovery = phase in ('RECOVERY', 'RECOVERY_COMPLETE')
        final_boss = phase in ('FINAL_BOSS', 'VICTORY')
        wave = story.objective_index + 1
        if phase in ('SURVIVAL', 'SURVIVAL_COMPLETE'):
            heading = 'FINAL ENCOUNTER   /   SURVIVAL'
            if phase == 'SURVIVAL_COMPLETE':
                title = 'Survival complete'
                detail = 'Core and hostiles cleared' if story.survival_cleared_early else f'{story.survival_duration:.0f} seconds survived'
                accent = teal
            else:
                seconds = math.ceil(story.survival_duration - story.phase_time)
                title = f'Survive: {seconds}s'
                if story.boss.health > 0:
                    detail = 'Core shield active' if story.shielded else 'Core exposed'
                else:
                    detail = 'Core down. Stay alive.'
                accent = amber
        elif phase in ('RETURNING_CORES', 'SECOND_DEFEAT'):
            heading = 'FINAL ENCOUNTER   /   CORE AMBUSH'
            if phase == 'SECOND_DEFEAT':
                title, detail = 'Cockpit separating', 'Emergency ejection'
            elif story.phase_time >= story.retreating_attack_duration - story.returning_charge_duration:
                title, detail = 'Volley charging', 'Three shielded Cores'
            else:
                title, detail = 'Evade the Cores', 'Three shielded Cores'
            accent = (255, 105, 130)

        elif phase == 'COLLECTOR_FORMATION':
            heading = 'FINAL ENCOUNTER   /   THE COLLECTOR'
            title = 'The Collector is forming'
            detail = 'Ship wreckage is being assimilated'
            accent = (255,105,130)

        elif phase == 'COLLECTOR_FIGHT':
            heading = 'FINAL ENCOUNTER   /   THE COLLECTOR'
            title = 'DEFEAT THE COLLECTOR'
            shield = 'SHIELD ACTIVE' if story.collector_shielded else 'SHIELD CHARGING' if story.collector_shield_charging else 'SHIELD DOWN'
            detail = f'Phase {story.collector_phase}   /   {shield}'
            accent = (255,105,130)
        elif phase in ('RETURN_TO_BASE', 'DOCKING'):
            heading = 'EXTRACTION   /   HOME STATION'
            if phase == 'RETURN_TO_BASE':
                title = 'Return to base'
                edge = 'left' if story.dock_position.x < WIDTH / 2 else 'right'
                detail = f'Fly to the green beacon on the {edge}'
            else:
                title, detail = 'Docking', 'Aligning cockpit with berth'
            accent = teal
        elif final_boss:
            heading = 'ENCOUNTER   /   SYSTEM CORE'
            if phase == 'VICTORY':
                title, detail = 'System restored', 'The core has been shut down'
                accent = teal
            else:
                phase_names = {1: 'PHASE 1: SCOUTS', 2: 'PHASE 2: HEAVY ASSAULT',
                               3: 'PHASE 3: CORE EXPOSED', 4: 'FURY MODE'}
                title = phase_names.get(story.final_boss_phase, 'FINAL BOSS')
                vulnerability = 'SHIELDED' if story.final_boss_phase < 3 or story.fury_boss_locked else 'VULNERABLE'
                detail = f'CORE {story.boss.health} / {story.boss.max_health}  ·  {vulnerability}'
                accent = (255, 105, 130) if story.final_boss_phase == 4 else amber
        elif recovery:
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
            title = 'Evade the Core'
            detail = 'Shield active' if story.shielded else 'Core exposed'
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

        progress = story.progress_percent()
        progress_panel = pygame.Surface((200, 42), pygame.SRCALPHA)
        progress_panel.fill((8, 19, 34, 227))
        label = self.label.render(f'STORY PROGRESS  {progress}%', True, teal)
        progress_panel.blit(label, (10, 7))
        pygame.draw.rect(progress_panel, (49, 66, 82), (10, 25, 180, 6))
        pygame.draw.rect(progress_panel, teal, (10, 25, 180 * progress // 100, 6))
        screen.blit(progress_panel, (WIDTH - 212, 10))

        if phase == 'FINAL_BOSS' or (phase == 'SURVIVAL' and story.boss.health > 0):
            bar_width = 300
            bar = pygame.Rect(WIDTH // 2 - bar_width // 2, 24, bar_width, 12)
            pygame.draw.rect(screen, (55, 35, 50), bar, border_radius=5)
            fill = round(bar_width * max(0, story.boss.health) / max(1, story.boss.max_health))
            if fill:
                pygame.draw.rect(screen, (245, 65, 95), (bar.x, bar.y, fill, bar.height), border_radius=5)
            integrity = 'CORE INTEGRITY'
            if phase == 'SURVIVAL':
                integrity = f'{integrity}  {story.boss.health} / {story.boss.max_health}'
            label = self.label.render(integrity, True, (255, 190, 205))
            screen.blit(label, label.get_rect(midbottom=(WIDTH // 2, 20)))

        elif phase == 'COLLECTOR_FIGHT':
            bar_width = 340
            bar = pygame.Rect(WIDTH // 2 - bar_width // 2, 24, bar_width, 14)
            pygame.draw.rect(screen, (55,35,50), bar, border_radius=5)
            fill = round(bar_width * max(0, story.collector.health) / story.collector.max_health)
            if fill > 0:
                colour = (105,226,255) if story.collector_shielded else (255,75,95)
                pygame.draw.rect(screen, colour, (bar.x, bar.y, fill, bar.height), border_radius=5)
            integrity = f'THE COLLECTOR   {story.collector.health} / {story.collector.max_health}'
            label = self.label.render(integrity, True, (255,190,205))
            screen.blit(label,label.get_rect(midbottom=(WIDTH // 2, 20)))

        dock = pygame.Surface((WIDTH, 42), pygame.SRCALPHA)
        dock.fill((7, 16, 30, 233))
        pygame.draw.line(dock, (57, 83, 100), (0,0), (WIDTH,0))
        self.meter(dock, 18, 'HULL', health, hp_limit, amber if health <= 2 else teal)
        self.meter(dock, 164, 'AMMO', ammo, ammo_limit, amber if ammo <= 3 else (130, 196, 253))
        for x, label, colour in ((18, 'HULL', teal), (164, 'AMMO', (130, 196, 253))):
            if label in self.gains:
                amount, time = self.gains[label]
                gain = self.body.render(f'+{amount}', True, colour)
                gain.set_alpha(round(255 * min(1, time / 0.35)))
                y = HEIGHT - 52 - round(14 * (1 - time / self.gain_duration))
                screen.blit(gain, gain.get_rect(midbottom=(x + 104, y)))
        if recovery:
            dock.blit(self.label.render('COMPONENTS', True, muted), (318, 6))
            for index, part in enumerate(story.ship.parts[1:]):
                x = 320 + index * 15
                colour = teal if part.attached else (65, 85, 102)
                pygame.draw.polygon(dock, colour, [(x,24),(x+9,24),(x+6,31),(x-3,31)])
        if debuff != 'NONE':
            debuff_name = 'INVERTED CONTROLS' if debuff == 'REVERSED' else debuff.replace('_', ' ')
            name = self.body.render(debuff_name, True, amber)
            dock.blit(name, name.get_rect(topright=(WIDTH-16, 3)))
            text = self.label.render(description, True, muted)
            dock.blit(text, text.get_rect(topright=(WIDTH-16, 23)))
        if debuff == 'WEAPON_OVERHEATING':
            colour = (255, 105, 130) if overheated else amber
            label = f'WEAPON HEAT  {heat_percent}%'
            if overheated:
                label += '  JAMMED'
            dock.blit(self.label.render(label, True, colour), (460, 6))
            pygame.draw.rect(dock, (49, 66, 82), (460, 26, 150, 5))
            pygame.draw.rect(dock, colour, (460, 26, 150 * heat_percent // 100, 5))
        module_names = ('RIFT_DRIVE', 'SIEGE_CANNON', 'PHASE_CLOAK')
        if any(name in story.recovered_upgrades for name in module_names):
            modules = 'MODULES: ' + ' / '.join(
                name.replace('_', ' ') for name in module_names
                if name in story.recovered_upgrades
            )
            dock.blit(self.label.render(modules, True, (127, 225, 237)), (318, 6))
        ability_hints = []
        if 'RIFT_DRIVE' in story.recovered_upgrades:
            ability_hints.append('SPACE: RIFT DASH')
        if 'PHASE_CLOAK' in story.recovered_upgrades:
            ability_hints.append('Q: PHASE CLOAK')
        if ability_hints:
            dock.blit(self.label.render('   '.join(ability_hints), True, (175, 195, 215)), (318, 23))
        screen.blit(dock, (0, HEIGHT-42))

        if story.module_notice_timer > 0:
            notice = self.body.render(story.module_notice, True, (143, 248, 222))
            screen.blit(notice, notice.get_rect(midtop=(WIDTH // 2, 54)))
        if story.phase_cloak_timer > 0:
            ability = self.label.render(f'PHASE CLOAK {story.phase_cloak_timer:.1f}s', True, (100, 240, 245))
            screen.blit(ability, ability.get_rect(topright=(WIDTH - 18, 94)))
        elif story.rift_drive_cooldown > 0 and 'RIFT_DRIVE' in story.recovered_upgrades:
            ability = self.label.render(f'RIFT DRIVE {story.rift_drive_cooldown:.1f}s', True, (175, 145, 255))
            screen.blit(ability, ability.get_rect(topright=(WIDTH - 18, 94)))

        if story.wave_clear_timer > 0:
            panel = pygame.Surface((226, 44), pygame.SRCALPHA)
            pygame.draw.polygon(panel, (11, 44, 48, 239), [(0,0),(226,0),(213,44),(13,44)])
            pygame.draw.line(panel, teal, (13,42), (213,42), 2)
            message = self.title.render(f'WAVE {wave} CLEARED', True, teal)
            panel.blit(message, message.get_rect(center=(113,22)))
            panel.set_alpha(round(255 * min(1, story.wave_clear_timer / 0.35)))
            screen.blit(panel, panel.get_rect(midtop=(WIDTH//2, 14)))
