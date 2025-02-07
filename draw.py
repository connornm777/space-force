import math
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

def draw_rocket(screen, rocket, forward_thrust, reverse_thrust, turn_left, turn_right):
    rx = SCREEN_WIDTH / 2
    ry = SCREEN_HEIGHT / 2
    length = 30.0
    rad = math.radians(rocket['heading'])

    nose_x  = rx + length * math.cos(rad)
    nose_y  = ry + length * math.sin(rad)
    left_x  = rx + (-0.4*length)*math.cos(rad + math.radians(130))
    left_y  = ry + (-0.4*length)*math.sin(rad + math.radians(130))
    right_x = rx + (-0.4*length)*math.cos(rad - math.radians(130))
    right_y = ry + (-0.4*length)*math.sin(rad - math.radians(130))

    color_front = (255, 0, 0)
    color_back  = (180, 0, 0)
    pygame.draw.polygon(screen, color_front, [(nose_x, nose_y),(left_x, left_y),(right_x, right_y)])
    back_x = rx - 0.7*length*math.cos(rad)
    back_y = ry - 0.7*length*math.sin(rad)
    pygame.draw.polygon(screen, color_back, [(left_x, left_y),(back_x, back_y),(right_x, right_y)])

    # Optionally show thruster flames, e.g.:
    # if forward_thrust: ...
    # if reverse_thrust: ...

    # Force field
    if rocket['forcefield_on']:
        shield_rad = 80
        srf = pygame.Surface((shield_rad*2, shield_rad*2), pygame.SRCALPHA)
        pygame.draw.circle(srf, (0,255,0,50), (shield_rad, shield_rad), shield_rad)
        pygame.draw.circle(srf, (0,255,0,150), (shield_rad, shield_rad), shield_rad, 2)
        screen.blit(srf, (rx - shield_rad, ry - shield_rad))
