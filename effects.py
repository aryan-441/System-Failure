import random
import pygame


class ArcadeEffects:
    """Manages particles, hit feedback, screen shake and malfunction alerts."""

    def __init__(self):
        self.small_font = pygame.font.Font(None, 35)
        self.banner_font = pygame.font.Font(None, 55)
        self.reset()

    def reset(self):
        self.particles = []
        self.floating_text = []
        self.banner_text = ""
        self.banner_timer = 0.0
        self.banner_duration = 2.0
        self.hit_overlay_timer = 0.0
        self.shake = 0.0
        self.smoke_timer = 0.0
        self.white_masks = {}

    def make_particle(self, position, velocity, colour, life, radius, gravity=0, image=None):
        self.particles.append({
            "position": pygame.Vector2(position),
            "velocity": pygame.Vector2(velocity),
            "colour": colour,
            "life": life,
            "maximum_life": life,
            "radius": radius,
            "gravity": gravity,
            "image": image,
        })

    def sparks(self, position, count, colour):
        for _ in range(count):
            direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            speed = random.uniform(60, 220)
            self.make_particle(
                position, direction * speed, colour,
                random.uniform(0.15, 0.5), random.uniform(2, 5)
            )

    def muzzle_flash(self, position, direction):
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        front = pygame.Vector2(position) + direction * 28
        for _ in range(5):
            spread = direction.rotate(random.uniform(-30, 30))
            self.make_particle(
                front, spread * random.uniform(40, 130),
                (95, 220, 255), 0.12, 3
            )

    def smoke(self, position, dt):
        self.smoke_timer += dt
        while self.smoke_timer >= 0.035:
            self.smoke_timer -= 0.035
            particle_position = pygame.Vector2(position) + pygame.Vector2(
                random.uniform(-20, 20), random.uniform(-10, 10)
            )
            velocity = pygame.Vector2(
                random.uniform(-25, 25), random.uniform(-75, -30)
            )
            grey = random.randint(100, 160)
            self.make_particle(
                particle_position, velocity, (grey, grey, grey),
                random.uniform(0.5, 1.1), random.uniform(5, 10)
            )

    def hit_enemy(self, enemy):
        enemy.last_hit = pygame.time.get_ticks()
        enemy.hit_flash_timer = 0.17
        self.sparks(enemy.rect.center, 10, (175, 235, 255))

    def enemy_destroyed(self, enemy):
        colour = (255, 100, 95) if getattr(enemy, "is_boss", False) else (255, 185, 70)
        self.sparks(enemy.rect.center, 24, colour)
        self.shake = max(self.shake, 7 if getattr(enemy, "is_boss", False) else 3)

    def player_hit(self, position, damage):
        self.sparks(position, 22, (255, 65, 90))
        self.floating_text.append({
            "text": f"-{damage}",
            "position": pygame.Vector2(position) + pygame.Vector2(
                random.uniform(-8, 8), -22
            ),
            "life": 0.95,
            "maximum_life": 0.95,
        })
        self.hit_overlay_timer = 0.28
        self.shake = max(self.shake, 9)

    def malfunction_changed(self, malfunction):
        self.banner_text = malfunction.replace("_", " ")
        self.banner_timer = self.banner_duration
        self.shake = max(self.shake, 4)

    def update(self, dt):
        self.banner_timer = max(0.0, self.banner_timer - dt)
        self.hit_overlay_timer = max(0.0, self.hit_overlay_timer - dt)
        self.shake = max(0.0, self.shake - 28 * dt)

        for particle in self.particles:

            particle['life'] -= dt
            if particle['life'] <= 0:
                self.particles.remove(particle)
                continue

            particle['velocity'].y += particle['gravity'] * dt
            particle['position'] += particle['velocity'] * dt

            

        for label in self.floating_text[:]:
            label["life"] -= dt
            label["position"].y -= 60 * dt
            

    def camera_offset(self):
        amount = int(self.shake)
        if amount < 1:
            return (0, 0)
        return (random.randint(-amount, amount), random.randint(-amount, amount))

    def draw_enemy_flash(self, surface, enemy):
        if getattr(enemy, "hit_flash_timer", 0) <= 0:
            return

        image = getattr(enemy, "ship_image", None)
        if isinstance(image, pygame.Surface):
            scale = 1.5 if getattr(enemy, "is_boss", False) else 1
            size = (
                max(1, int(image.get_width() * scale)),
                max(1, int(image.get_height() * scale)),
            )
            key = (id(image), size)
            mask_image = self.white_masks.get(key)

            if mask_image is None:
                scaled = pygame.transform.smoothscale(image, size)
                mask = pygame.mask.from_surface(scaled)
                mask_image = pygame.Surface(size, pygame.SRCALPHA) #for supporting transparency
                mask.to_surface(
                    surface=mask_image,
                    setcolor=(255, 255, 255, 255),
                    unsetcolor=(0, 0, 0, 0),
                )
                self.white_masks[key] = mask_image

            surface.blit(mask_image, mask_image.get_rect(center=enemy.rect.center))
        else:
            pygame.draw.rect(surface, (255, 255, 255), enemy.rect, 3)

    def draw(self, surface):
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for particle in self.particles:
            fraction = max(0.0, particle["life"] / particle["maximum_life"])
            alpha = int(220 * fraction) #220 as the visual choice for transparency
            radius = max(1, int(particle["radius"] * (1.5 - fraction * 0.5))) #math to make the particle size bigger as its transparency increases
            colour = (*particle["colour"], alpha)
            if particle['image'] is not None:
                sprite = particle['image']
                sprite.set_alpha(alpha)
                rect = sprite.get_rect(center=particle['position'])
                layer.blit(sprite,rect)
            else:
                pygame.draw.circle(
                    layer, colour,
                    (int(particle["position"].x), int(particle["position"].y)),
                    radius,
                )

        for label in self.floating_text:
            fraction = max(0.0, label["life"] / label["maximum_life"])
            label_surface = self.small_font.render(
                label["text"], True, (255, 80, 105)
            )
            label_surface.set_alpha(int(255 * fraction))
            position = label_surface.get_rect(
                center=(int(label["position"].x), int(label["position"].y))
            )
            layer.blit(label_surface, position)

        surface.blit(layer, (0, 0))

    def draw_overlay(self, surface, width, height):
        if self.hit_overlay_timer > 0:
            opacity = int(75 * min(1.0, self.hit_overlay_timer / 0.15))
            edge = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(
                edge, (255, 20, 55, opacity), edge.get_rect(), 17
            )
            surface.blit(edge, (0, 0))

        if self.banner_timer > 0:
            age = self.banner_duration - self.banner_timer
            opacity = int(
                255 * min(1.0, age / 0.18, self.banner_timer / 0.45)
            )
            panel = pygame.Surface((width, 90), pygame.SRCALPHA)
            pygame.draw.rect(
                panel, (45, 8, 25, int(160 * opacity / 255)),
                panel.get_rect(), border_radius=12
            )
            pygame.draw.rect(
                panel, (255, 85, 105, opacity),
                panel.get_rect(), 3, border_radius=12
            )
            heading = self.banner_font.render(
                "SYSTEM ERROR", True, (255, 120, 130)
            )
            message = self.small_font.render(
                self.banner_text, True, (255, 255, 255)
            )
            heading.set_alpha(opacity)
            message.set_alpha(opacity)
            panel.blit(heading, heading.get_rect(center=(width // 2, 28)))
            panel.blit(message, message.get_rect(center=(width // 2, 67)))
            surface.blit(panel, (0, int(height * 0.28)))