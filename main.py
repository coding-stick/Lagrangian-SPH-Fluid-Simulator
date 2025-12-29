import pygame, Config, Fluid
from Fluid import *

win = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
pygame.display.set_caption("fluid simulation")

start_cells()

pygame.init()
running = True
my_font = pygame.font.SysFont('Comic Sans MS', 15)
clock = pygame.time.Clock()
# store a safe default timestep so pause/unpause restores it
stored_delta = Config.delta if Config.delta > 0 else 0.02

while running:
    win.fill((0, 0, 0))
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                if Config.delta != 0:
                    # pausing: remember current non-zero delta
                    stored_delta = Config.delta
                    Config.delta = 0
                else:
                    # unpause: restore previously stored safe delta (fallback to 0.02)
                    Config.delta = stored_delta if stored_delta > 0 else 0.02
            if event.key==pygame.K_RETURN:
                Config.debug_mode = not Config.debug_mode
    (leftcl, mid, rightcl) = pygame.mouse.get_pressed()
    if leftcl:
        Config.interaction_strength = 500
    elif rightcl:
        Config.interaction_strength = -500
    else:
        Config.interaction_strength = 0

    #print(Config.delta)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
        Config.delta  = min(0.18, Config.delta+0.001)
    elif keys[pygame.K_MINUS] or keys[pygame.K_UNDERSCORE]:
        Config.delta = max(0, Config.delta-0.001)
    elif keys[pygame.K_UP]:
        Config.stiffness_constant += 10
    elif keys[pygame.K_DOWN]:
        Config.stiffness_constant  = max(0, Config.stiffness_constant-10)
    elif keys[pygame.K_w]:
        Config.interaction_radius += 1
    elif keys[pygame.K_s]:
        Config.interaction_radius  = max(1, Config.interaction_radius-1)
    elif keys[pygame.K_e]:
        Config.viscosity_strength += 0.05
    elif keys[pygame.K_d]:
        Config.viscosity_strength  = max(0, Config.viscosity_strength -0.05)
    elif keys[pygame.K_r]:
        Config.target_density = min(0.5, Config.target_density + 0.001)
    elif keys[pygame.K_f]:
        Config.target_density  = max(0, Config.target_density -0.001)
    
    update(win, pygame.Vector2(Config.gravity), mouse_pos)

    if Config.debug_mode:
        draw_grid(win)
        pygame.draw.circle(win, (255,0,0), mouse_pos, Config.interaction_radius, 1)
        win.blit(my_font.render(f'Delta (space/+/-): {Config.delta}', False, (255,255,255)), (0,10))
        win.blit(my_font.render(f'Stiffness/ Pressure Coef (up/down): {Config.stiffness_constant}', False, (255,255,255)), (0,30))
        win.blit(my_font.render(f'Interact Radius (w/s): {Config.interaction_radius}', False, (255,255,255)), (0,50))
        win.blit(my_font.render(f'Interact strength: {Config.interaction_strength}', False, (255,255,255)), (0,70))
        win.blit(my_font.render(f'Viscosity (e/d): {Config.viscosity_strength}', False, (255,255,255)), (0,90))
        win.blit(my_font.render(f'Density (r/f): {Config.target_density}', False, (255,255,255)), (0,110))
    win.blit(my_font.render('Enter to toggle debug mode', False, (255,255,255)), (0,0))

    

    

    pygame.display.update()
    clock.tick(15)

pygame.quit()