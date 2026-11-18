
import pygame
from arcade_audio import ArcadeAudio

pygame.init()

audio = ArcadeAudio()

audio.play('shoot')

pygame.time.wait(500)

pygame.quit()
