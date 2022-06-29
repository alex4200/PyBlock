"""Example: Maze creation.

This example shows how to create a maze with arbitrary shape, walls, size etc. c
"""
import pyblock

# Set your path to the minecraft world
PATH = "path/to//minecraft/saves/YourWorld"


# Create the editor
editor = pyblock.Editor(PATH)

# Creates a logical 10x10 maze
mymaze = pyblock.Maze(10, 10)
mymaze.create()


# Create the maze within minecraft at the given location with the given materials.
# The first number tuple is the (x,y,z) coordinates of the lower edge.
# The next tuple defines the blocks to be used as (floor, wall, ceiling).
# The `mag` parameter specifies a magnification of the maze in each direction.
# If `mag=1`, each path has size 1, if `mag=2`, the size is 2 etc.
# 'height' is the height of the walls.
editor.create_maze(
    mymaze,
    (17, 70, 17),
    ("glowstone", "oak_log", "purple_stained_glass"),
    mag=2,
    height=10,
)

# The following example shows a custom shaped square maze ,
# which has a 10x10 inner area and the player has to find the way
# from the outer border to the inner border

# The general layout is something like
  
  #########
  #########
  ###   ###
  ###   ###
  #########
  #########

# Create a 30x30 size maze with exit point at 15/20
mymaze = pyblock.Maze(30, 30, exit_point=(15, 20))

# Create the new inner border surrounding the inner part
inner_x = 10
inner_z = 10
inner_d = 10

# Clear the inner part
for x in range(inner_x, inner_x + inner_d):
    for z in range(inner_z, inner_z + inner_d):
        mymaze.set_clear(x,z)

# Create the new inner border surrounding the inner part
for x in range(inner_x, inner_x + inner_d):
    mymaze.set_border(x, 10)
    mymaze.set_border(x, 20)
for z in range(inner_z, inner_z + inner_d):
    mymaze.set_border(10, z)
    mymaze.set_border(20, z)


# Create the actual maze
mymaze.create()

# Put the maze into blocks
editor.create_maze(
    mymaze,
    (50, 70, 50),
    ("glowstone", "oak_log", "purple_stained_glass"),
    mag=2,
    height=10,
)

editor.done()
