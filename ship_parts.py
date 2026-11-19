
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

        self.attached = True
        self.returning = False
        self.return_timer = 0.0
        self.return_duration = 0.8

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_image.get_rect(center=self.position)
        screen.blit(rotated_image, rect)


class ModularShip:
    def __init__(self, image, centre):
        self.centre = pygame.Vector2(centre)
        self.parts = []
        self.state = "intact"
        self.animation_timer = 0
        self.angle = 0

        self.hull_surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        width, height = image.get_size()
        left_edge = width * 35 // 99
        right_edge = width * 64 // 99
        regions = [
            pygame.Rect(left_edge, 0, right_edge - left_edge, height)
        ]

        left_wing = pygame.Rect(0, 0, left_edge, height)
        right_wing = pygame.Rect(right_edge, 0, width - right_edge, height)
        wings = [
            image.subsurface(wing).get_bounding_rect().move(wing.x, wing.y)
            for wing in (left_wing, right_wing)
        ]

        for row in range(3):
            for wing in wings:
                top = wing.top + row * wing.height // 3
                bottom = wing.top + (row + 1) * wing.height // 3
                regions.append(pygame.Rect(wing.x, top, wing.width, bottom - top))

        for region in regions:
            self.add_part(image, region)

    def add_part(self, image, rect):
        part_image = image.subsurface(rect).copy()
        offset = (
            rect.centerx - image.get_width() / 2,
            rect.centery - image.get_height() / 2,
        )
        self.parts.append(ShipPart(part_image, offset, self.centre))

    def explode(self):
        self.state = "broken"

        directions = [
    pygame.Vector2(-1, -0.8),  # Left upper
    pygame.Vector2(1, -0.8),   # Right upper
    pygame.Vector2(-1, 0.1),   # Left middle
    pygame.Vector2(1, 0.1),    # Right middle
    pygame.Vector2(-1, 0.9),   # Left lower
    pygame.Vector2(1, 0.9),    # Right lower
]

        spins = [-140, 140, -90, 90, -120, 120]

        for part, direction, spin in zip(
            self.parts[1:], directions, spins
        ):
            part.velocity = direction.normalize().rotate(-self.angle) * 170
            part.rotation_speed = spin
            part.attached = False
            part.returning = False
            part.return_timer = 0

    def reassemble(self):
        self.state = "reassembling"
        self.animation_timer = 0

        for part in self.parts[1:]:
            part.start_position = part.position.copy()
            part.start_angle = part.angle

    def recover_part(self,part_id):
        if 1 <= part_id <= 6:
            part = self.parts[part_id]
            if part.attached == False:
                if part.returning == False:
                    part.return_timer = 0
                    part.start_position = part.position.copy()
                    part.start_angle = part.angle
                    part.returning = True


    def part_target(self, part):
        return self.centre + part.offset.rotate(-self.angle)

    def return_angle(self, part, progress):
        turn = (self.angle - part.start_angle + 180) % 360 - 180
        return part.start_angle + turn * progress

    def update(self, dt):
        self.parts[0].position = self.part_target(self.parts[0])
        self.parts[0].angle = self.angle
        if self.state == "broken":
            for part in self.parts[1:]:
                if part.attached:
                    part.position = self.part_target(part)
                    part.angle = self.angle
                elif part.returning:
                # Individual recovery animation
                    part.return_timer += dt

                    progress = min(
                        1, part.return_timer / part.return_duration
                    )

                    eased = 1 - (1 - progress) ** 3

                    target = self.part_target(part)

                    part.position = part.start_position.lerp(
                        target, eased
                    )

                    part.angle = self.return_angle(part, eased)

                    if progress >= 1:
                        part.attached = True
                        part.returning = False
                        part.position = target
                        part.angle = self.angle
                        part.velocity = pygame.Vector2(0, 0)
                        part.rotation_speed = 0

                else:
                    part.position += part.velocity * dt
                    part.angle += part.rotation_speed * dt
                    part.velocity *= max(0, 1 - 1.8 * dt)
                    part.rotation_speed *= max(0, 1 - 2.5 * dt)
            all_attached = True
            for part in self.parts[1:]:
                if part.attached == False:
                    all_attached = False
                    break
            if all_attached:
                self.state = 'intact'
        elif self.state == "reassembling":
            self.animation_timer += dt
            progress = min(1, self.animation_timer / 1.2)
            eased = 1 - (1 - progress) ** 3

            for part in self.parts[1:]:
                target = self.part_target(part)
                part.position = part.start_position.lerp(target, eased)
                part.angle = self.return_angle(part, eased)

            if progress >= 1:
                for part in self.parts[1:]:
                    part.attached = True
                    part.returning = False
                    part.return_timer = 0
                self.state = "intact"

        elif self.state == "intact":
            for part in self.parts[1:]:
                part.position = self.part_target(part)
                part.angle = self.angle
            
    def draw(self, screen):
        if self.angle == 0:
            for part in self.parts:
                part.draw(screen)
            return

        self.hull_surface.fill((0, 0, 0, 0))
        surface_centre = pygame.Vector2(self.hull_surface.get_size()) / 2
        for part in self.parts:
            if part.attached and self.state != "reassembling":
                local_rect = part.image.get_rect(center=surface_centre + part.offset)
                self.hull_surface.blit(part.image, local_rect)
            else:
                part.draw(screen)

        hull = pygame.transform.rotate(self.hull_surface, self.angle)
        screen.blit(hull, hull.get_rect(center=self.centre))


def load_explosion_frames():
    explosion_path = (
        Path(__file__).parent / 'assets' / 'images' / 'effects' / 'animated_explosions' / 'explosion-3.png'

    )
    explosion_sheet = pygame.image.load(str(explosion_path)).convert_alpha()
    frame_size = explosion_sheet.get_height() #works cuz frames are square
    frame_count = explosion_sheet.get_width() // frame_size

    explosion_frames = []
    for i in range(frame_count):
        frame_rect = pygame.Rect(
            i * frame_size,
            0,
            frame_size,
            frame_size,
        )
        frame = explosion_sheet.subsurface(frame_rect).copy()
        frame = pygame.transform.scale(frame,(80,80))

        explosion_frames.append(frame)
    return explosion_frames


#TEST




if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode((900, 600))
    particle_folder = Path(__file__).parent / 'assets' / 'images' / 'effects' / 'particles' 
    def load_particle_texture(filename, size, tint):

        '''particle_folder = Path(__file__).parent / 'assets' / 'images' / 'effects' / 'particles' 
        address = Path.__truediv__(particle_folder,'smoke_02.png')
        smoke_texture = pygame.image.load(
            address

        ).convert_alpha()'''

        texture = pygame.image.load(str(particle_folder / filename)).convert_alpha()
        texture = pygame.transform.smoothscale(texture,(size,size))
        texture.fill(
            (*tint,255), #tuple unpacking so that we can get RGBA
            special_flags=pygame.BLEND_RGBA_MULT
        )
        return texture
    #TEXTURES
    smoke_texture = load_particle_texture('smoke_02.png',42,(135,145,165))
    flame_texture = load_particle_texture('flame_05.png', 28, (255, 145, 65))
    orange_spark_texture = load_particle_texture('star_09.png', 18, (255, 195, 110))
    blue_spark_texture = load_particle_texture('star_09.png', 18, (95, 210, 255)) 


    #smoke_texture.fill((145,150,165,255), special_flags = pygame.BLEND_RGBA_MULT)
    scene = pygame.Surface((900, 600))

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)

    effects = ArcadeEffects()

    def spawn_spark_effect(effects, position, texture, count):
        for i in range(count):
            direction = pygame.Vector2(1,0).rotate(random.uniform(0,360)) #random direction

            speed = random.uniform(90,230)

            effects.make_particle(
                position, 
                direction*speed, #velocity
                (255,210,150),
                random.uniform(0.15,0.4), #life
                radius=2,
                image=texture
            )


    explosion_frames = load_explosion_frames()
    explosion_age = None
    explosion_frame_time = 0.048


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
                    explosion_age = 0

                    spawn_spark_effect(effects,ship.centre,orange_spark_texture,16)
                    effects.shake = 12
                    flash_timer = 0.17

                elif event.key == pygame.K_r and ship.state == 'broken':
                    ship.reassemble()

                    spawn_spark_effect(effects,ship.centre,blue_spark_texture,16)

                elif pygame.K_1 <= event.key <= pygame.K_6 and ship.state == 'broken':
                    ship.recover_part(event.key - pygame.K_0)

        previous_state = ship.state

        ship.update(dt)
        if explosion_age is not None:
            explosion_age += dt
            frame_index = explosion_age / explosion_frame_time
            frame_index = int(frame_index)
            if frame_index >= len(explosion_frames):
                explosion_age = None
        # Burning particles 
        if ship.state == 'broken':

            for part in ship.parts[1:]:

                if random.random() < 3 * dt:
                    smoke_velocity = part.velocity * 0.15 + pygame.Vector2( #inherits 15% of ships velocity
                        random.uniform(-18,18),
                        random.uniform(-35,-8)
                    )
                    effects.make_particle(
                        part.position,
                        smoke_velocity,
                        (135,145,165),
                        random.uniform(0.65,1.1), #life
                        radius=3,
                        image=smoke_texture
                    )

                if random.random() < 1.4 * dt:
                    flame_velocity = part.velocity * 0.1 + pygame.Vector2(
                        random.uniform(-15,15),
                        random.uniform(-20,10)
                    )

                    effects.make_particle(

                part.position,
                flame_velocity,
                (255, 145, 65),
                random.uniform(0.2, 0.45),
                radius=2,
                image=flame_texture
            )
        # Effects when all components reconnect
        if previous_state == 'reassembling' and ship.state == 'intact':
            #effects.sparks(ship.centre, 35, (100, 220, 255))
            spawn_spark_effect(effects,ship.centre,blue_spark_texture,16)
            effects.shake = 5
            flash_timer = 0.10

        effects.update(dt)
        flash_timer = max(0, flash_timer - dt)


        screen.fill((8, 12, 28))
        scene.fill((8,12,28))
        ship.draw(scene)
        if explosion_age is not None:
            current_image = explosion_frames[frame_index]
            explosion_rect = current_image.get_rect(center=ship.centre)
            scene.blit(current_image,explosion_rect)
            #pygame.Surface.get_rect(ship.centre)
        effects.draw(scene)
        
        screen.blit(scene, effects.camera_offset()) 

        # Flash overlay
        if flash_timer > 0:
            opacity = int(130 * flash_timer / 0.17) #flash timer is 0.17 at the start. therefore thid value for opacity helps increase transparency overtime

            flash_surface.set_alpha(opacity)
            screen.blit(flash_surface, (0, 0))

        instruction = font.render(
            'SPACE: Break apart    1-6: Recover part    R: Reassemble',
            True,
            (210, 225, 255)
        )

        screen.blit(instruction, (20, 20))

        pygame.display.flip()

    pygame.quit()
    
