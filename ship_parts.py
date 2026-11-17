
'''MODULAR SPACESHIP SYSTEM FOR STORY MODE'''

import random
import pygame
from pathlib import Path
from effects import ArcadeEffects


class ShipPart:

    def __init__(self, image, offset, centre):
        self.image = image
        self.offset = pygame.Vector2(offset) 

        self.position = pygame.Vector2(centre) + self.offset
        self.velocity = pygame.Vector2(0, 0)

        self.angle = 0
        self.rotation_speed = 0

        self.start_position = self.position.copy()
        self.start_angle = 0

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_image.get_rect(center=self.position)
        screen.blit(rotated_image, rect)


class ModularShip:

    def __init__(self, image, centre):
        self.centre = pygame.Vector2(centre)
        self.parts = []

        self.state = 'intact'
        self.animation_timer = 0

        width, height = image.get_size()
        side_width = width // 3

        
        cockpit_rect = pygame.Rect(
            side_width, 0,
            width - 2 * side_width, height
        )

        self.add_part(image, cockpit_rect)

        # Three components on each side
        for x in (0, width - side_width):

            for row in range(3):
                top = row * height // 3
                bottom = (row + 1) * height // 3

                part_rect = pygame.Rect(
                    x, top,
                    side_width, bottom - top
                )

                self.add_part(image, part_rect)

    def add_part(self, image, rect):
        part_image = image.subsurface(rect).copy()

        offset = (
            rect.centerx - image.get_width() / 2, #distance between point and centre of ship
            rect.centery - image.get_height() / 2
        )

        part = ShipPart(part_image, offset, self.centre)
        self.parts.append(part)

    def explode(self):
        self.state = 'broken'

        # The cockpit remains intact
        for part in self.parts[1:]:

            direction = part.offset.copy()

            direction += pygame.Vector2(
                random.uniform(-25, 25),
                random.uniform(-25, 25)
            )

            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)

            direction = direction.normalize()

            part.velocity = direction * random.uniform(130, 260)
            part.rotation_speed = random.uniform(-240, 240)

    def reassemble(self):
        self.state = 'reassembling'
        self.animation_timer = 0

        for part in self.parts[1:]:
            part.start_position = part.position.copy()
            part.start_angle = part.angle

    def update(self, dt):

        if self.state == 'broken':

            for part in self.parts[1:]:
                part.position += part.velocity * dt
                part.angle += part.rotation_speed * dt

                part.velocity *= max(0, 1 - 0.7 * dt)

        elif self.state == 'reassembling':

            self.animation_timer += dt
            progress = min(1, self.animation_timer / 1.5)

            # Smooth movement towards the ship
            eased = 1 - (1 - progress) ** 3

            for part in self.parts[1:]:
                target = self.centre + part.offset

                part.position = part.start_position.lerp(  #lerp method for animation
                    target, eased
                )

                part.angle = part.start_angle * (1 - eased)

            if progress >= 1:
                self.state = 'intact'

    def draw(self, screen):

        for part in self.parts:
            part.draw(screen)


#TEST




if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode((900, 600))
    scene = pygame.Surface((900, 600))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)

    effects = ArcadeEffects()

    path = Path(__file__).parent / 'assets' / 'images' / 'player' / 'player_ship_blue.png'

    image = pygame.image.load(str(path)).convert_alpha()

    scale = 170 / max(image.get_size())

    image = pygame.transform.scale(
        image,
        (
            int(image.get_width() * scale),
            int(image.get_height() * scale)
        )
    )

    ship = ModularShip(image, (450, 300))

    # White flash
    flash_surface = pygame.Surface((900, 600))
    flash_surface.fill((220, 235, 255))
    flash_timer = 0

    running = True

    while running:
        dt = min(clock.tick(60) / 1000, 0.05)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE and ship.state == 'intact':
                    ship.explode()

                    effects.sparks(ship.centre, 55, (255, 165, 75))
                    effects.shake = 12
                    flash_timer = 0.17

                elif event.key == pygame.K_r and ship.state == 'broken':
                    ship.reassemble()

                    effects.sparks(ship.centre, 18, (100, 210, 255))

        previous_state = ship.state

        ship.update(dt)

        # Burning particles 
        if ship.state == 'broken':

            for part in ship.parts[1:]:

                if random.random() < 0.08:

                    effects.make_particle(
                        part.position,
                        (
                            random.uniform(-20, 20),
                            random.uniform(-40, 10)
                        ),
                        (255, 130, 65),
                        0.5,
                        3
                    )

        # Effects when all components reconnect
        if previous_state == 'reassembling' and ship.state == 'intact':
            effects.sparks(ship.centre, 35, (100, 220, 255))
            effects.shake = 5
            flash_timer = 0.10

        effects.update(dt)
        flash_timer = max(0, flash_timer - dt)


        scene.fill((8, 12, 28))
        ship.draw(scene)
        effects.draw(scene)

        # Apply camera shake to the entire scene
        screen.fill((8, 12, 28))
        screen.blit(scene, effects.camera_offset())

        # Flash overlay
        if flash_timer > 0:
            opacity = int(130 * flash_timer / 0.17)
            flash_surface.set_alpha(opacity)
            screen.blit(flash_surface, (0, 0))

        instruction = font.render(
            'SPACE: Break apart    R: Reassemble',
            True,
            (210, 225, 255)
        )

        screen.blit(instruction, (20, 20))

        pygame.display.flip()

    pygame.quit()
