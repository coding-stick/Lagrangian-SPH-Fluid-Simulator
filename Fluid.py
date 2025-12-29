import Config
import pygame, math, random
import matplotlib.cm as cm
import numpy as np

positions = []
velocities = []

cmap = cm.get_cmap(Config.color_scheme)



frame_counter = 0

def update(win, acc_ext, mouse_pos):
    N = len(positions)

    #initialize and register grid
    grids = initialize_grid()
    for i in range(N):
        cell_belonging = look_up_grid(positions[i]) # cell in grid the particle belongs in
        grids = register_grid(cell_belonging, i, grids) # register the index into the 2d array

    densities = [calculate_density(i, grids) for i in range(N)]
    pressures = [pressure_from_density(i, densities) for i in range(N)]

    '''
    # diagnostics: print density / neighbor stats occasionally when debugging
    global frame_counter
    frame_counter += 1
    if Config.debug_mode and N>0 and frame_counter % 30 == 0:
        avg_rho = sum(densities)/N
        min_rho = min(densities)
        max_rho = max(densities)
        # estimate neighbor counts using grids
        neigh_counts = []
        for i in range(N):
            pos_i = positions[i]
            row, col = look_up_grid(pos_i)
            count = 0
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    r_cell = row + dr
                    c_cell = col + dc
                    if 0<= r_cell < grid_cols and 0<=c_cell < grid_rows:
                        for j in grids[r_cell][c_cell]:
                            if j==i: continue
                            if (pos_i - positions[j]).length() <= Config.smoothing_radius:
                                count += 1
            neigh_counts.append(count)
        avg_neigh = sum(neigh_counts)/N
        print(f"rho: avg={avg_rho:.4f} min={min_rho:.4f} max={max_rho:.4f} | neigh_avg={avg_neigh:.1f}")
        '''
    
    accelerations = []
    for i in range(N):
        a = acc_from_pressure(i, densities, pressures, grids)
        a += acc_from_viscosity(i, densities, velocities, grids)
        a += acc_ext # gravity
        if Config.interaction_strength != 0:
            a += interaction_force(mouse_pos, Config.interaction_radius, Config.interaction_strength, i)

        accelerations.append(a)

     # 2d array- each cell in grid will be a list containing particle's index in positions list
    

    # semi-implicit integration: compute candidate velocities, apply XSPH mixing, then update positions
    new_vels = []
    for i in range(N):
        v_new = velocities[i] + accelerations[i] * Config.delta
        v_new = clamp_velocity(v_new, Config.max_speed)
        new_vels.append(v_new)
        
    if Config.xsph_epsilon > 0 and N>0:
        xsph_corr = xsph_corrections(new_vels, densities, grids)
        for i in range(N):
            new_vels[i] += xsph_corr[i]

    for i in range(N):
        velocities[i] = new_vels[i]
        positions[i] += velocities[i] * Config.delta

        resolve_collisions(positions[i], velocities[i])
        draw_circle(win, get_color(velocities[i].length()), positions[i], Config.particle_size)
    #print_grids(grids)


def resolve_collisions(pos, vel):
    if pos.x + Config.particle_size > Config.WIDTH:
        pos.x = Config.WIDTH - Config.particle_size
        vel.x *= -Config.collision_damping
    elif pos.x - Config.particle_size < 0:
        pos.x = Config.particle_size
        vel.x *= -Config.collision_damping
    elif pos.y + Config.particle_size > Config.HEIGHT:
        pos.y = Config.HEIGHT - Config.particle_size
        vel.y *= -Config.collision_damping
    elif pos.y - Config.particle_size < 0:
        pos.y = Config.particle_size
        vel.y *= -Config.collision_damping

def draw_circle(win, color, pos, radius):
    pygame.draw.circle(win, color, pos, radius)

def start_cells(starting_pos=(Config.particle_size,Config.particle_size), spacing=2):
    spacing = spacing + Config.particle_size*2 # from spacing b/ween edges to spacing b/ween centers
    n_rows = int(math.sqrt(Config.num_particles))
    for rows in range(n_rows):
        x = starting_pos[0] + rows*spacing
        for cols in range(n_rows):
            y = starting_pos[1] + cols*spacing
            velocities.append(pygame.Vector2(0,0))
            positions.append(pygame.Vector2(x,y))

def start_single(starting_pos = (100,100), vel=(0,0)):
    velocities.append(pygame.Vector2(vel))
    positions.append(pygame.Vector2(starting_pos))

def start_random():
    for n in range(Config.num_particles):
        x = random.randint(Config.particle_size, Config.WIDTH-Config.particle_size)
        y = random.randint(Config.particle_size, Config.HEIGHT- Config.particle_size)
        velocities.append(pygame.Vector2(0,0))
        positions.append(pygame.Vector2(x,y))



def calculate_density(particle_index:int, grids):
    density = 0
    pos_i = positions[particle_index]
    row, col = look_up_grid(pos_i)
    '''
    for position in positions:
        dst = (position - positions[particle_index]).length()
        if dst < Config.smoothing_radius:
            influence = smoothing_kernel(dst, Config.smoothing_radius)
            density += Config.mass*influence
    return density
    '''
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            r_cell = row + dr
            c_cell = col + dc
            if 0<= r_cell < grid_cols and 0<=c_cell < grid_rows:
                for j in grids[r_cell][c_cell]:
                    dst = (pos_i - positions[j]).length()
                    density += Config.mass * smoothing_kernel(dst, Config.smoothing_radius)
    return density


def pressure_from_density(particle_index:int, densities:list):
    return Config.stiffness_constant * (densities[particle_index] - Config.target_density)


def acc_from_pressure(particle_index:int, densities:list, pressures:list, grids):
    a = pygame.Vector2((0,0))
    pos_i = positions[particle_index]
    rho_i = densities[particle_index]
    p_i = pressures[particle_index]
    
    row, col = look_up_grid(positions[particle_index])
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            r_cell = row + dr
            c_cell = col + dc
            if 0<= r_cell < grid_cols and 0<=c_cell < grid_rows:
                for j in grids[r_cell][c_cell]:
                    if particle_index==j: continue
                    pos_j = positions[j]
                    r_vec = pos_i - pos_j

                    rho_j = densities[j]
                    p_j = pressures[j]

                    grad = kernel_gradient(r_vec, Config.smoothing_radius)

                    shared_pressure = ((p_i / (rho_i*rho_i)) + (p_j / (rho_j*rho_j)))

                    # SPH pressure acceleration: a_i = - \nabla W weighted sum
                    a -= Config.mass * shared_pressure * grad
    return a

def acc_from_viscosity(particle_index:int, densities:list, velocities:list, grids):
    a = pygame.Vector2((0,0))
    vi = velocities[particle_index]
    pos_i = positions[particle_index]

    row, col = look_up_grid(positions[particle_index])
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            r_cell = row + dr
            c_cell = col + dc
            if 0<= r_cell < grid_cols and 0<=c_cell < grid_rows:
                for j in grids[r_cell][c_cell]:
                    if particle_index==j: continue
                    r = (pos_i - positions[j]).length()
                    vj = velocities[j]
                    rho_j = densities[j]
                    v_rel = vi-vj
                    a += Config.mass * v_rel/rho_j * laplacian_kernel(r, Config.smoothing_radius)
    
    return a*Config.viscosity_strength

# poly6: (315/64*math.pi*h^9 * (h^2 - r^2)^3) if 0 <=r <= h else 0
# spiky: (15/ math.pi*h^6) * (h - r)^3 if 0<= r <= h else 0
# all these equations: from scientific paper

def smoothing_kernel(r,h):
    #spiky
    if 0 <= r <= h:
        return (15 / (math.pi * h**6)) * (h - r)**3
    return 0

def laplacian_kernel(r_len,h):
    # for viscosity, DO NOT use spiky laplacian. this is separate kernel
    if r_len>=h:
        return 0
    return (45/(math.pi * h**6)) * (h - r_len)

def kernel_gradient(r_vec:pygame.Vector2,h):
    # spiky gradient
    r = r_vec.length()
    if r>=h or r==0:
        return r_vec*0.0
    k = -45 / (math.pi * h**6) 
    return k * (h-r)**2 * (r_vec/r)
    


def get_color(vel):
    
    #print(vel)
    speed = min(vel/Config.max_speed, 1)
    #print(speed)
    r, g, b, a = cmap(speed)

    return (int(255*r), int(255*g), int(255*b))


def clamp_velocity(v, max_speed):
    speed = v.length()
    if speed > max_speed:
        return v.normalize() * max_speed
    return v

def look_up_grid(particle_pos):
    x = int(particle_pos.x // Config.grid_size)
    y = int(particle_pos.y // Config.grid_size)

    # CLAMP
    x = max(0, min(x, grid_rows - 1))
    y = max(0, min(y, grid_cols - 1))
    #print(x,y)
    return y,x


grid_cols = (Config.HEIGHT//Config.grid_size) + 1
grid_rows = (Config.WIDTH//Config.grid_size) + 1

def initialize_grid():
    return [[[] for _ in range(grid_rows)] for _ in range(grid_cols)]

def register_grid(cell_belonging, i, grids):
    x, y = cell_belonging
    grids[x][y].append(i)
    return grids


def print_grids(grids):
    print("[ ----")
    for row in grids:
        for cell in row:
            print(cell, end=",")
        print()
    print(" ----]\n")

def draw_grid(win):
    for x in range(0, Config.WIDTH, Config.grid_size):
        pygame.draw.line(win, (0,100,0), (x,0), (x,Config.HEIGHT), 1)
    for y in range(0, Config.HEIGHT, Config.grid_size):
        pygame.draw.line(win, (0,100,0), (0,y), (Config.WIDTH,y), 1)


def interaction_force(input_pos, radius, strength, particle_index):
    interaction_force = pygame.Vector2((0,0))
    offset = input_pos - positions[particle_index]
    sqr_dst = offset.dot(offset)

    # if inside radius, calc. force to point
    if (sqr_dst < radius*radius):
        dst = math.sqrt(sqr_dst)
        dir_to_point = offset/dst
        # value is 1 when exactly at input point, 0 when at radius
        centerT = 1-dst/radius
        interaction_force += (dir_to_point * strength - velocities[particle_index] * centerT)
        #print(interaction_force)
    return interaction_force


def xsph_corrections(candidate_vels, densities, grids):
    """Compute XSPH velocity mixing corrections for candidate velocities.
    Returns a list of Vector2 corrections to add to each candidate velocity.
    """
    N = len(candidate_vels)
    eps = Config.xsph_epsilon #getattr(Config, 'xsph_epsilon', 0.0)
    if eps <= 0 or N == 0:
        return [pygame.Vector2(0,0) for _ in range(N)]

    corrections = [pygame.Vector2(0,0) for _ in range(N)]
    for i in range(N):
        pos_i = positions[i]
        vi = candidate_vels[i]
        contrib = pygame.Vector2(0,0)
        row, col = look_up_grid(pos_i)
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                r_cell = row + dr
                c_cell = col + dc
                if 0<= r_cell < grid_cols and 0<=c_cell < grid_rows:
                    for j in grids[r_cell][c_cell]:
                        if j == i: continue
                        r = (pos_i - positions[j]).length()
                        if r > Config.smoothing_radius: continue
                        w = smoothing_kernel(r, Config.smoothing_radius)
                        contrib += (candidate_vels[j] - vi) * (Config.mass / max(densities[j], 1e-8)) * w
        corrections[i] = contrib * eps
    return corrections
