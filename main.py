from PIL import Image
import numpy as np
import math
import pygame

scene = [
    (0,-5.5,0,20,10,20,0x1,(128,255,128)),
    (1.5,0,0,1,0x0,0x0,0x2,(255,0,0)), # X,Y,Z sizeX,sizeY,sizeZ, 0x1 - Square, 0x2 - Sphere, (R,G,B)
    (-1.5,0,0,1,0x0,0x0,0x2,(0,255,0)), # X,Y,Z sizeX,sizeY,sizeZ, 0x1 - Square, 0x2 - Sphere, (R,G,B)
    (0,0,-1,1,0x0,0x0,0x2,(0,0,255)), # X,Y,Z sizeX,sizeY,sizeZ, 0x1 - Square, 0x2 - Sphere, (R,G,B)
]

lightpos = (10,10,10)

#AFEEEE
bgcol = (175,238,238)

preciseness = 0.02

def collide(x,y,z,scene):
    for obj in scene:
        if (obj[6] == 0x1 and
            x >= obj[0]-(obj[3]/2) and x < obj[0]+(obj[3]/2) and
            y >= -obj[1]-(obj[4]/2) and y < -obj[1]+(obj[4]/2) and
            z >= obj[2]-(obj[5]/2) and z < obj[2]+(obj[5]/2)):
            return obj
        if (obj[6] == 0x2 and math.hypot(x - obj[0], y - obj[1], z - obj[2]) < (obj[3]/2)):
            
            return obj

def normalize(x,y,z):
    dis = math.hypot(x,y,z)
    return x / dis, y / dis, z / dis

def raycast(fromx,fromy,fromz,tox,toy,toz,scene):
    dx, dy, dz = tox - fromx, toy - fromy, toz - fromz
    dist = math.hypot(dx, dy, dz)
    steps = int(dist / preciseness)

    x, y, z = fromx, fromy, fromz
    dx /= steps
    dy /= steps
    dz /= steps

    for _ in range(steps):
        x += dx
        y += dy
        z += dz

        obj = collide(x, y, z, scene)

        if obj:
            dist_light = math.hypot(x - lightpos[0], y - lightpos[1], z - lightpos[2])
            dist_from = math.hypot(x - fromx, y - fromy, z - fromz)
            return obj, dist_light, dist_from, (x,y,z)

    return None, None, None, None

def raycast_faster(fromx,fromy,fromz,tox,toy,toz,scene):
    dx, dy, dz = tox - fromx, toy - fromy, toz - fromz
    dist = math.hypot(dx, dy, dz)
    steps = int(dist / preciseness)

    x, y, z = fromx, fromy, fromz
    dx /= steps
    dy /= steps
    dz /= steps

    for _ in range(steps):
        x += dx
        y += dy
        z += dz

        obj = collide(x, y, z, scene)

        if obj:
            return obj, (x,y,z)

    return None, None

def process(obj, dist_light, dist_from, hitpos):
    r,g,b = obj[7]   
    depth = (dist_light/dist_from)/70
    r = int(r * depth)
    g = int(g * depth)
    b = int(b * depth)
    distfromlight = math.hypot(hitpos[0] - lightpos[0], hitpos[1] - lightpos[1], hitpos[2] - lightpos[2])
    # check if theres nothing in the way to light
    lightray = raycast_faster(hitpos[0], hitpos[1], hitpos[2], hitpos[0]-lightpos[0], (hitpos[1]-lightpos[1]), hitpos[2]-lightpos[2], scene)
    if lightray[0]:
        r -= distfromlight / 6
        g -= distfromlight / 6
        b -= distfromlight / 6
        r *= 7
        g *= 7
        b *= 7
        # calculate normal
        nx, ny, nz = obj[0] - hitpos[0], obj[1] - hitpos[1], obj[2] - hitpos[2]
        normal = normalize(nx, ny, nz)
        normal = normal[0] * -5, normal[1] * -5, normal[2] * -5
        # bounce
        bounceray = raycast_faster(hitpos[0], -hitpos[1], hitpos[2], normal[0], normal[1], normal[2], scene)

        if bounceray[0]:
            r = lerp(r, bounceray[0][7][0], 0.3)
            g = lerp(g, bounceray[0][7][1], 0.3)
            b = lerp(b, bounceray[0][7][2], 0.3)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


    if obj[6] == 0x2:
        # calculate normal
        nx, ny, nz = obj[0] - hitpos[0], obj[1] - hitpos[1], obj[2] - hitpos[2]
        normal = normalize(nx, ny, nz)
        normal = normal[0] * -5, normal[1] * -5, normal[2] * -5
        # bounce
        bounceray = raycast_faster(hitpos[0], -hitpos[1], hitpos[2], normal[0], normal[1], normal[2], scene)

        if bounceray[0]:
            r = lerp(r, bounceray[0][7][0], 0.3)
            g = lerp(g, bounceray[0][7][1], 0.3)
            b = lerp(b, bounceray[0][7][2], 0.3)


    e = max(0, 30 - distfromlight)*20
    r1,g1,b1 = obj[7]
    r1 = r1 * (e/400)
    g1 = g1 * (e/400)
    b1 = b1 * (e/400)
    m = e / 5
    r,g,b = r+r1, g+g1, b+b1
    r,g,b = r+m, g+m, b+m

    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

def lerp(a, b, t):
    return a + (b - a) * t

def postprocess(processed):
    r,g,b = processed
    # Right now, it just adds bgcol.
    r = lerp(r, bgcol[0], 0.15)
    g = lerp(g, bgcol[1], 0.15)
    b = lerp(b, bgcol[2], 0.15)
    return (r,g,b)

null=None # for... idk

def render():
    array = [[null for x in range(150)] for y in range(150)]

    for y in range(150):
        for x in range(150):
            fromx, fromy, fromz = 1,0,-8

            tox = fromx + (((x / 15)-7.5)*1.3)
            toy = fromy + (((y / 15)-7.5)*1.3)
            toz = fromz + 20
            tox, toy, toz = normalize(tox, toy, toz)
            tox, toy, toz = tox * 10, (toy * 10)+1, toz * 10

            obj, dist_light, dist_from, hitpos = raycast(fromx, fromy, fromz, tox, toy, toz, scene)

            if obj:
                processed = process(obj, dist_light, dist_from, hitpos)
                postprocessed = postprocess(processed)
                array[y][x] = postprocessed
   
    for y in range(150): # Turn sky into a gradient, so that it wouldnt be a single color
        for x in range(150):
            if array[y][x] == null:
                # make a gradient
                r,g,b = bgcol
                r /= ((y+1)/900)*13
                g /= ((y+1)/900)*13
                b /= ((y+1)/900)*13
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                array[y][x] = (int(r),int(g),int(b))

    return array
   


pygame.init()

print("Rendering...")

array = render()

screen = pygame.display.set_mode((300,300))

screen.fill((0,0,0))


for x in range(150):
    for y in range(150):
        r,g,b = array[y][x]
        pygame.draw.rect(screen, (int(r),int(g),int(b)), (x*2,y*2,2,2))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    pygame.display.update()


