import math

def squarespiral(side1, side2, pitch, turns):
    """Generate square spiral"""
    x = side1 + pitch
    y = side2
    yield (x - pitch, y)
    for ii in range(turns):
        x = pitch - x
        yield (x, y)
        y = -y
        yield (x, y)
        x = -x
        yield (x, y)
        y = -pitch - y
        yield (x, y)

def ellipticalspiral(side1, side2, pitch, turns, vertices_per_turn):
    cosines = [math.cos(2 * math.pi * ii / vertices_per_turn) 
            for ii in range(vertices_per_turn)]
    sines = [math.sin(2 * math.pi * ii / vertices_per_turn) 
            for ii in range(vertices_per_turn)]
    for turn in range(turns):
        yield from zip(
                (cos * (side1 - ii * pitch / vertices_per_turn)
                    for ii, cos in enumerate(cosines)),
                (sin * (side2 - ii * pitch / vertices_per_turn)
                    for ii, sin in enumerate(sines)))
        side1 -= pitch
        side2 -= pitch
    yield (side1, 0)
