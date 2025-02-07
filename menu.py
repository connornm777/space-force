import pygame, sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from levels import get_all_levels

def run_level_menu(screen, font):
    """Simple menu that reads levels from get_all_levels()."""
    menu_options = list(get_all_levels().keys())  # e.g. ["Flat", "Star", "Hole"]
    idx = 0
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    idx = (idx - 1) % len(menu_options)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    idx = (idx + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    return menu_options[idx]

        screen.fill((20,20,30))
        title_surf = font.render("SPACE-FORCE: SELECT LEVEL", True, (255,255,255))
        screen.blit(title_surf, (SCREEN_WIDTH//2 - 140, 100))

        for i, opt in enumerate(menu_options):
            color = (200,200,100) if i == idx else (200,200,200)
            opt_surf = font.render(opt, True, color)
            screen.blit(opt_surf, (SCREEN_WIDTH//2 - 50 + i*150, 300))

        instruct = "Use Left/Right, Enter=confirm, Esc=quit"
        i_surf = font.render(instruct, True, (200,200,200))
        screen.blit(i_surf, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 80))
        pygame.display.flip()
