import sys
import math
import pygame
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BASE_DT,
                      C_MAX, WORLD_WIDTH, WORLD_HEIGHT, ROCKET_RAD)
from menu import run_level_menu
from levels import create_level
from collisions import handle_collision
from utils import limit_speed, wrap_pos
from draw import draw_rocket

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space-Force")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    # 1. Menu -> pick level
    level_name = run_level_menu(screen, font)
    level_obj  = create_level(level_name)

    # 2. Setup rocket
    rocket = {
        'type': 'rocket',
        'x': level_obj.WORLD_WIDTH/2,
        'y': level_obj.WORLD_HEIGHT/2 + 2000,  # Just an arbitrary start
        'vx': 0, 'vy': 0,
        'radius': ROCKET_RAD,
        'mass': 10.0,
        'heading': 0,
        'angvel': 0,
        'forcefield_on': False,
        'shield_on': False,
    }

    game_state = {'game_over': False}

    def reset_game():
        nonlocal level_obj, rocket
        level_obj = create_level(level_name)  # fresh instance
        rocket['x'] = level_obj.WORLD_WIDTH/2
        rocket['y'] = level_obj.WORLD_HEIGHT/2 + 2000
        rocket['vx'] = 0
        rocket['vy'] = 0
        rocket['heading'] = 0
        rocket['angvel'] = 0
        rocket['forcefield_on'] = False
        rocket['shield_on'] = False
        game_state['game_over'] = False

    running = True
    while running:
        dt_real = clock.tick(FPS) / 1000.0

        # EVENT HANDLING
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if game_state['game_over']:
                        reset_game()
                elif event.key == pygame.K_r:
                    reset_game()

        # KEY STATES
        keys = pygame.key.get_pressed()
        torque = 50.0
        turn_left = False
        turn_right= False
        forward_thrust = False
        reverse_thrust = False

        if keys[pygame.K_a]:
            rocket['angvel'] -= torque * dt_real
            turn_left = True
        if keys[pygame.K_d]:
            rocket['angvel'] += torque * dt_real
            turn_right = True
        if keys[pygame.K_w] and not rocket['forcefield_on']:
            h_rad = math.radians(rocket['heading'])
            rocket['vx'] += 100.0 * dt_real * math.cos(h_rad)
            rocket['vy'] += 100.0 * dt_real * math.sin(h_rad)
            rocket['vx'], rocket['vy'] = limit_speed(rocket['vx'], rocket['vy'], C_MAX)
            forward_thrust = True
        if keys[pygame.K_s] and not rocket['forcefield_on']:
            h_rad = math.radians(rocket['heading'])
            rocket['vx'] -= 100.0 * dt_real * math.cos(h_rad)
            rocket['vy'] -= 100.0 * dt_real * math.sin(h_rad)
            rocket['vx'], rocket['vy'] = limit_speed(rocket['vx'], rocket['vy'], C_MAX)
            reverse_thrust = True

        # UPDATE ROCKET PHYSICS
        ax, ay = level_obj.force_func(rocket['x'], rocket['y'], rocket['vx'], rocket['vy'])
        rocket['vx'] += ax * BASE_DT
        rocket['vy'] += ay * BASE_DT
        rocket['vx'], rocket['vy'] = limit_speed(rocket['vx'], rocket['vy'], C_MAX)
        rocket['heading'] += rocket['angvel'] * BASE_DT
        rocket['x'] += rocket['vx'] * BASE_DT
        rocket['y'] += rocket['vy'] * BASE_DT
        rocket['x'], rocket['y'] = wrap_pos(rocket['x'], rocket['y'], level_obj.WORLD_WIDTH, level_obj.WORLD_HEIGHT)

        # Shield logic
        rocket['shield_on'] = rocket['forcefield_on']

        # Check lethal zone
        if level_obj.lethal_check(rocket['x'], rocket['y']):
            game_state['game_over'] = True

        # Collisions with asteroids, etc.
        all_objects = [rocket] + level_obj.asteroids
        for i in range(len(all_objects)):
            for j in range(i+1, len(all_objects)):
                handle_collision(all_objects[i], all_objects[j], game_state)
                if game_state['game_over']:
                    break
            if game_state['game_over']:
                break

        # DRAW
        screen.fill((0,0,0))
        cam_x = rocket['x'] - (SCREEN_WIDTH  / 2)
        cam_y = rocket['y'] - (SCREEN_HEIGHT / 2)
        level_obj.draw_background(screen, rocket, cam_x, cam_y)

        draw_rocket(screen, rocket, forward_thrust, reverse_thrust, turn_left, turn_right)

        # Example: you might also draw asteroids if you define a draw function for them
        # for ast in level_obj.asteroids:
        #     draw_asteroid(screen, ast, cam_x, cam_y)

        if game_state['game_over']:
            msg = "GAME OVER! Press SPACE or R to restart."
            surf = font.render(msg, True, (255,0,0))
            screen.blit(surf, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
