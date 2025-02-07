import pygame
from constants import WORLD_WIDTH, WORLD_HEIGHT

class LevelBase:
    """
    Base class shared by all levels.
    """
    def __init__(self):
        self.WORLD_WIDTH  = WORLD_WIDTH
        self.WORLD_HEIGHT = WORLD_HEIGHT
        self.asteroids    = []  # or other objects

    def force_func(self, x, y, vx, vy):
        """Return (ax, ay) for gravitational or other forces."""
        return (0.0, 0.0)

    def lethal_check(self, x, y):
        """Check if (x,y) is in a lethal region."""
        return False

    def draw_background(self, screen, rocket, cam_x, cam_y):
        screen.fill((0,0,0))
