
'''Background'''

import pygame
import random
from pathlib import Path

class SpaceBackground:

    def __init__(self, width, height):  
        self.width = width
        self.height = height
        self.scroll = 0
        self.timer = 0 #variables for transitioning to the next background
        self.current_index = 0

        self.display_time = 10  
        self.fade_time = 2
        self.scroll_speed = 15

        self.images = []

        folder = Path(__file__).parent / "assets" / "images" / "backgrounds" / "seamless_space"

        if folder.exists():
            files = sorted(  #comprehension to get only image files
                file for file in folder.rglob("*")
                if file.suffix.lower() in (".png", ".jpg", ".jpeg")
            )

            nebula_files = [
                file for file in files
                if "nebula" in file.stem.lower()  #stem method from path library
            ]

            if nebula_files:
                files = nebula_files

            for file in files:
                try:
                    image = pygame.image.load(str(file)).convert()
                    self.images.append(image)
                except pygame.error:
                    print("Could not load:", file.name)

        print("Background images loaded:", len(self.images))

        self.stars = []

        for i in range(80):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 2)
            speed = random.randint(10, 45)

            self.stars.append([x, y, size, speed])

    def update(self, dt):
        self.scroll += self.scroll_speed * dt
        self.timer += dt

        if self.timer >= self.display_time + self.fade_time:
            self.timer = 0

            if len(self.images) > 0:
                self.current_index = (self.current_index + 1) % len(self.images)

        for star in self.stars:
            star[1] += star[3] * dt

            if star[1] > self.height:
                star[1] = 0
                star[0] = random.randint(0, self.width)

    def draw_image(self, screen, image):
        image_width = image.get_width()
        image_height = image.get_height()

        offset = int(self.scroll) % image_height

        for x in range(0, self.width, image_width):
            for y in range(-image_height + offset, self.height, image_height):
                screen.blit(image, (x, y))

    def draw(self, screen):
        screen.fill((8, 10, 25))

        if len(self.images) > 0:
            current_image = self.images[self.current_index]
            self.draw_image(screen, current_image)

            if self.timer >= self.display_time and len(self.images) > 1:
                next_index = (self.current_index + 1) % len(self.images)
                next_image = self.images[next_index]

                progress = (self.timer - self.display_time) / self.fade_time
                alpha = min(255, int(progress * 255))

                next_image.set_alpha(alpha)
                self.draw_image(screen, next_image)
                next_image.set_alpha(None)

        for star in self.stars:
            pygame.draw.circle(
                screen,
                (180, 210, 255),
                (int(star[0]), int(star[1])),
                star[2]
            )
