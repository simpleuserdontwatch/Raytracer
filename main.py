from PIL import Image
import numpy as np
import math
import pygame, random

scene = [
    (0,-5.5,0,20,10,20,0x3,"floor2.png"), # 0x3 - Texture (Facing up)
    (1.5,0,0,1,0x0,0x0,0x2,(255,0,0)), # X,Y,Z sizeX,sizeY,sizeZ, 0x1 - Square, 0x2 - Sphere, (R,G,B)
    (-1.5,0,0,1,0x0,0x0,0x4,(128,128,128)), # 0x4 - mirror ball. cool, right?
    (0,0,-1,1,0x0,0x0,0x2,(0,0,255)), # X,Y,Z sizeX,sizeY,sizeZ, 0x1 - Square, 0x2 - Sphere, (R,G,B)
]

lightpos = (10,10,10) # Direction of light
#AFEEEE
ambcol = (175,238,238) # Ambient color
preciseness = 0.01 # more = faster, but more choppy, and buggy with images
texturesize = (512,512) # less = faster, for some computers.
skytexture = "sky.jpg"



print("Loading sky...")
skyimg = Image.open(skytexture).resize((200,200), Image.NEAREST)


def readimg(path):
    print("Opening " + path)
    print("Resizing to " + str(texturesize))
    return Image.open(path).resize(texturesize, Image.NEAREST) # nearest is the fastest way

textures = {}
for i in scene:
    if i[6] == 0x3 or i[6] == 0x5:
        textures[i[7]] = readimg(i[7])
print("Texture json: "+str(textures))

def normals(pos,obj,scene):
    x,y,z = pos
    if collide(x,y+0.01,z,scene) != obj:
        return (0,1,0)
    if collide(x,y-0.01,z,scene) != obj:
        return (0,-1,0)
    if collide(x+0.01,y,z,scene) != obj:
        return (1,0,0)
    if collide(x-0.01,y,z,scene) != obj:
        return (-1,0,0)
    if collide(x,y,z+0.01,scene) != obj:
        return (0,0,1)
    if collide(x,y,z-0.01,scene) != obj:
        return (0,0,-1)

    raise Exception("No normal found for obj " + str(obj))

def collide(x,y,z,scene):
    for obj in scene:
        if (obj[6] == 0x1 or obj[6] == 0x3 and
            x >= obj[0]-(obj[3]/2) and x < obj[0]+(obj[3]/2) and
            y >= -obj[1]-(obj[4]/2) and y < -obj[1]+(obj[4]/2) and
            z >= obj[2]-(obj[5]/2) and z < obj[2]+(obj[5]/2)):
            return obj
        if (obj[6] == 0x5 and
            x >= obj[0]-(obj[3]/2) and x < obj[0]+(obj[3]/2) and
            y >= -obj[1]-(obj[4]/2) and y < -obj[1]+(obj[4]/2) and
            z >= obj[2]-(obj[5]/2) and z < obj[2]+(obj[5]/2)):
            return obj
        if (obj[6] in (0x2,0x4) and math.hypot(x - obj[0], y - obj[1], z - obj[2]) < (obj[3]/2)):
            
            return obj

def normalize(x,y,z):
    try:
        dis = math.hypot(x,y,z)
        return x / dis, y / dis, z / dis
    except ZeroDivisionError:
        return 0,0,0

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
            if obj[6] == 0x3 or obj[6] == 0x5:
                # get pixel
                localimgx = int(((x - obj[0])/obj[3])*texturesize[0])+(texturesize[0]//2)
                if obj[6] == 0x3:
                    localimgy = int(((z - obj[2])/obj[5])*texturesize[1])+(texturesize[1]//2)
                else:
                    localimgy = int(((y - obj[1])/obj[4])*texturesize[1])+(texturesize[1]//2)
                pixcol = textures[obj[7]].getpixel((localimgx,localimgy))
                # create a fake object
                return (x,y,z,0.1,0.1,0.1,0x1,(pixcol[0],pixcol[1],pixcol[2])), dist_light, dist_from, (x,y,z)
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
            if obj[6] == 0x3 or obj[6] == 0x5:
                # get pixel
                localimgx = int(((x - obj[0])/obj[3])*texturesize[0])+(texturesize[0]//2)
                if obj[6] == 0x3:
                    localimgy = int(((z - obj[2])/obj[5])*texturesize[1])+(texturesize[1]//2)
                else:
                    localimgy = int(((y - obj[1])/obj[4])*texturesize[1])+(texturesize[1]//2)
                pixcol = textures[obj[7]].getpixel((localimgx,localimgy))
                # create a fake object
                return (x,y,z,0.1,0.1,0.1,0x1,(pixcol[0],pixcol[1],pixcol[2])), (x,y,z)
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
        normal = normal[0] * -10, normal[1] * -10, normal[2] * -10
        # bounce
        bounceray = raycast_faster(hitpos[0], -hitpos[1], hitpos[2], normal[0], normal[1], normal[2], scene)

        if bounceray[0]:
            factor = 0.3
            if obj[6] == 0x4:
                factor = 1
            r = lerp(r, bounceray[0][7][0], factor)
            g = lerp(g, bounceray[0][7][1], factor)
            b = lerp(b, bounceray[0][7][2], factor)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


    if obj[6] == 0x2:
        # calculate normal
        nx, ny, nz = obj[0] - hitpos[0], obj[1] - hitpos[1], obj[2] - hitpos[2]
        normal = normalize(nx, ny, nz)
        normal = normal[0] * -10, normal[1] * -10, normal[2] * -10
        # bounce
        bounceray = raycast_faster(hitpos[0], -hitpos[1], hitpos[2], random.randint(-10,10)/20 + normal[0], random.randint(-10,10)/20 + normal[1], random.randint(-10,10)/20 + normal[2], scene)

        if bounceray[0]:
            factor = 0.3
            if obj[6] == 0x4:
                factor = 1
            r = lerp(r, bounceray[0][7][0], factor)
            g = lerp(g, bounceray[0][7][1], factor)
            b = lerp(b, bounceray[0][7][2], factor)

    if obj[6] == 0x1:
        # calculate normal
        nx,ny,nz = normals(hitpos, obj, scene)
        nx = nx * -10
        ny = ny * -10
        nz = nz * -10
        # bounce
        bounceray = raycast_faster(hitpos[0], hitpos[1], hitpos[2], random.randint(-10,10)/20 + nx, random.randint(-10,10)/20 + ny, random.randint(-10,10)/20 + nz, scene)
        if bounceray[0]:
            r = lerp(r, bounceray[0][7][0], 0.5)
            g = lerp(g, bounceray[0][7][1], 0.5)
            b = lerp(b, bounceray[0][7][2], 0.5)
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

def postprocess(processed, *args):
    r,g,b = processed
    # Mix with ambient color depending on how far it is
    dist_from = args[0]
    dist_from /= 35
    r = lerp(r, ambcol[0], dist_from)
    g = lerp(g, ambcol[1], dist_from)
    b = lerp(b, ambcol[2], dist_from)
    return (r,g,b)

null=None # for... idk

def render(scene):
    """
    Heres a usage for it:
    You put the scene, and it spits out a extremely large array of rendered scene.
    """
    array = [[null for x in range(200)] for y in range(200)]

    for y in range(200):
        for x in range(200):
            fromx, fromy, fromz = 0,-1,-8

            tox = fromx + (((x / 20)-5)*1.3)
            toy = fromy + (((y / 20)-5)*1.3)
            toz = fromz + 20
            tox, toy, toz = normalize(tox, toy, toz)
            tox, toy, toz = tox * 20, (toy * 20)+1, toz * 20

            obj, dist_light, dist_from, hitpos = raycast(fromx, fromy, fromz, tox, toy, toz, scene)

            if obj:
                processed = process(obj, dist_light, dist_from, hitpos)
                postprocessed = postprocess(processed, dist_from, hitpos)
                array[y][x] = postprocessed
            else:
                # draw the sky
                array[y][x] = skyimg.getpixel((int((tox/20)*200)+100,int((toy/20)*200)+100))
   

    return array
   


pygame.init()

print("Rendering...")

array = render(scene)

screen = pygame.display.set_mode((400,400))

screen.fill((0,0,0))


for x in range(200):
    for y in range(200):
        r,g,b = array[y][x]
        pygame.draw.rect(screen, (int(r),int(g),int(b)), (x*2,y*2,2,2))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    pygame.display.update()



