import pygame, Config#, Fluid
from Fluid import *
from Controls import *

win = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
pygame.display.set_caption("fluid simulation")

start_cells()

pygame.init()
running = True
my_font = pygame.font.SysFont('Comic Sans MS', 15)
clock = pygame.time.Clock()
# store a safe default timestep so pause/unpause restores it
stored_delta = Config.delta if Config.delta > 0 else 0.02

drawing_outlet = False
outlet_pos = None

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
            if event.key==pygame.K_c:
                Config.outlet_spray = not Config.outlet_spray
            if event.key==pygame.K_v:
                Config.outlets_paused = not Config.outlets_paused
            if event.key==pygame.K_b:
                Config.drains_paused = not Config.drains_paused
            if event.key==pygame.K_n:
                Config.env_interact_drain = not Config.env_interact_drain
            if event.key==pygame.K_m:
                Config.delete_particles_in_drain = not Config.delete_particles_in_drain
    (leftcl, mid, rightcl) = pygame.mouse.get_pressed()
    if leftcl:
        Config.interaction_strength = 500
    elif rightcl:
        Config.interaction_strength = -500
    else:
        Config.interaction_strength = 0

    if mid:
        if not drawing_outlet:
            drawing_outlet = True
            outlet_pos = mouse_pos
        else:
            if Config.env_interact_drain:
                col = (100,100,100)
            else:
                col = (255,255,255)
            pygame.draw.circle(win, col, outlet_pos, 10, 1)
            pygame.draw.line(win, col, outlet_pos, mouse_pos,1)
    else:
        
        if drawing_outlet:
            if not Config.env_interact_drain:
                drawing_outlet = False
                add_outlet(pygame.Vector2(outlet_pos), pygame.Vector2(mouse_pos))
            else:
                drawing_outlet = False
                add_drain(pygame.Vector2(outlet_pos), pygame.Vector2(mouse_pos))


    #print(Config.delta)
    keys = pygame.key.get_pressed()
    handle_controls(keys)
    
    update(win, pygame.Vector2(Config.gravity), mouse_pos)

    update_outlets(win)
    update_drains(win)

    if Config.debug_mode:
        draw_debug_options(win, my_font, mouse_pos)
        
    win.blit(my_font.render('Enter to toggle debug mode', False, (255,255,255)), (0,0))


    

    pygame.display.update()
    clock.tick(15)

pygame.quit()