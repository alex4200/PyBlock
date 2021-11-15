# PyBlock

This package helps to explore and examine your minecraft world. Find special blocks or get some overview of what you can find in your region/area of interest!

## Usage

Five tools can help to enhance your Minecraft experience. 
`pyblock list` lists all blocks found in an area, `pyblock find` lists the coordinates of a block in a certain area, `pyblock plot` creates overview plots of each level across the y direction and `pyblock copy` can be used to copy whole areas from one place to another place (even across different worlds!). 

The fifth tool is a module that enables editing existing worlds with python code. You can build your house, a wall, a maze or whatever you like using python!

In order to use the tools you have to specify the path to your minecraft world. You can do that either by specifying the argument `--world` or by specifying the environment variable `MINECRAFTWORLD`.

Example:

```
export MINECRAFTWORLD=/home/user/some/path/minecraft/saves/MyWorld
```

#### Important

**Always exit your minecraft game before doing any world manipulations. It could create undesired interferences!**

#### Hints

 * For each command you can set the verbosity to get more debug output, i.e. `pyblock -vv <command>`.

 * If you specify a certain area, the actual search area can differ a bit, as the code is using chunks as the search area.

 * If you find/list/plot or edit larger areas, this can take some minutes to complete. Better to try a smaller area first. Copying chunks around is much faster.

### Listing all blocks

`pyblock list  --coords 100 -400 --radius 40 `

This command lists all the blocks found in an cuboid area around the coordinates x=100, z=-400 within a box-'radius' of 40. The search area is a box with minimal coordinates (60, 0, -440) and maximal coordinates (1400, 255, -360). Always the complete vertical rage is used.

To list blocks in the nether you can use the option `--dimension nether`.

### Finding a block

`pyblock find --coords 100 -400 --radius 20 --block diamond_ore`

This command lists the exact block coordinates of each occurance of the block type 'diamond_ore' that has been found in the specified search area.

To find blocks in the nether you can use the option `--dimension nether`.

### Plotting all levels in an area

You also can use a tool to analyze a complete region file, e.g.

`pyblock plot --coords 100 200 --radius 100 --output Levels`

This command creates a very simple plot of each level around the coordinates x=100, z=200 within a 'radius' of 100 blocks, and stores it in the specified folder. Each block gets a color according to the mapping in the file `block_colors.py`. Please update this file to color the blocks to your needs.

Blocks for which a color is undefined are colored in red. When running this command with `-v` a list of all undefined blocks are listed in the terminal.  

### Copying chunks

This command can be used to copy some areas around. Be careful to use this command, as it can disrupt your landscapes!

To copy a 40x40 block area from 100/100 to 500/200, the command is

`pyblock copy --source 100 100 --dest 500 200 --size 40 40`

This command will give you the following output:

```
This would copy a size of 48x48 blocks from coordinates 96/96 to 496/192
This is a dry run. If you are happy with the coordinates, add '--no-test' to the command.
```

As only complete chunks will be copied, the final coordinates might differ slightly from the given coordinates. They have to be a multiple of 16 (which is the size of a chunk). 

If you are satisfied with the actual choice of coordinates, you need to add the option `--no-test` to make the actual changes:

```
pyblock copy --source 100 100 --dest 500 200 --size 40 40 --no-test
```

You can even use a completly different world as a source! Just use the argument `--world-source` to copy from a different world. 

```
pyblock copy --source 100 100 --dest 500 200 --size 40 40 --world-source /path/to/the/source/world --no-test
```


### Manipulating blocks

It is possible to manipulate blocks in the specified world with a python script. The following example creates a wall of `bedrock` around a 500x500 area:

```
import pyblock

# Define the block(s) to use
bedrock = pyblock.Block('minecraft', 'bedrock')

# Define the path to the world
path = "/path/to/minecraft/saves/MyWorld"

# Initialize the editor
editor = pyblock.MCEditor(path)

# Begin setting blocks
for y in range(250):
	for x in range(500, 1000):
		editor.set_block(bedrock, x, y, 2000)
		editor.set_block(bedrock, x, y, 1500)
	for z in range(1500, 2000):
		editor.set_block(bedrock, 500, y, z)
		editor.set_block(bedrock, 1000, y, z)

# Only here the actual regions are loaded and the changes applied.
editor.done()
```

The editor also enables to get the blocks are a given location with

```
block = editor.get_block(x,y,z)
```

which returns an instance of a Block. You can then get the name of the block using

```
print(block.id)
```

or you can get the block properties, for example:

```
print(block.id, block.properties)
> spruce_planks {'hinge': right, 'half': upper, 'powered': false, 'facing': south, 'open': false}
```

On contrast, to create an instance of a block with some properties, use `states` instead of `properties`: 

```
button = pyblock.Block('minecraft', 'warped_button', states = {"face": "floor", "facing": "north"})
```

#### Hints

 * With the above receipt, it is easy to copy things around. 
 * Not all items are copied correctly; most notable beds, signs and chests.

### Maze Creation

You also can easily create **mazes** within your minecraft world. Each maze contains one path from an entry point to an exit point, without containing any loops. Each generated maze will be different, and you can use your own exterior shape. 

Here is an example on how to use it:


```
import pyblock

# Define the path to the world
path = "/path/to/minecraft/saves/MyWorld"

# Creates the logical 10x10 maze
height = 10
width = 10
mymaze = pyblock.Maze(height, width)
mymaze.create()

# Initialize the editor
editor = pyblock.MCEditor(path)

# Create the maze within minecraft at the given location with the given materials.
# The first number tuple is the (x,y,z) coordinates of the most negative edge.
# The next tuple defines the blocks to be used as (floor, wall, ceiling).
# The `mag` parameter specifies a magnification of the maze in each direction.
# If `mag=1`, each path has size 1, if `mag=2`, the size is 2 etc.
editor.create_maze(mymaze, (800, 75, 1312), ("dirt_block", "oak_log", "air"), mag=2)
editor.done()
```

The maze creation works in two steps.

1. You create a logical maze of your desired size.
2. You pass that logical maze to `MCEditor.create_maze` to generate the maze in minecraft with proper blocks.

The internal representation of the initial maze is like following:

```
BBBBBeBBBB
B########B
B########B
B########B
B########B
B########B
B########B
B########B
B########B
BBBBBeBBBB
```

* `B` means the outside border
* `#` means the area where a path will be created
* `e` are the entry and exit points.

After creating the logical maze, it looks e.g. something like this:

```
BBBBBeBBBB
B     #  B
B## #  # B
B   ##   B
B ## ## #B
B #      B
B #### # B
B     ## B
B # # #  B
BBBBBeBBBB
```

Now the path is clearly visible.

#### Commands

For `pyblock.Maze` you have the following command:

```
pyblock.Maze(width = 10, height = 10, entry_point = None, exit_point = None, debug = False)
```

* `width`: The width of the maze (z-dimension).
* `height`: The height of the maze (x-dimension).
* `entry_point`: The location of the entry point of the maze. If no point is given, the middle point on the lower x dimension is choosen.
* `exit_point`: The location of the exit point of the maze. If no point is given, the middle point on the upper x dimension is choosen.
* `debug`: If set to `True`, the creation of the maze can be seen in the terminal.


For the `MCEditor.create_maze` you have the following command:

```
MCEditor.create_maze(maze, coord, blocks, height = 4, mag=1)
```

* `maze`: The logical maze from the first step.
* `coord`: The coordinates of the start point of the maze (x,y,z).
* `blocks`: Specifies the blocks to be used for the floor, the wall and the ceiling.
* `height`: Specifies the height of the walls (in units of blocks).
* `mag`: Magnifier for the maze itself, gives the width of the paths and the walls.


#### Maze shape

With the two-step procedure, you can give the maze any 2-dimensional shape you want. In the following example, the maze is a 30x30 large maze, but with a clear 10x10 area in the middle of the maze, and the exit point on the lower part of that clear inner area:

```
height = 30
width = 30
exit_point = (15, 20)
mymaze = pyblock.Maze(height, width, exit_point=exit_point, debug=True)

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
```

With that custom-shape of the maze, the final logical maze looks e.g. something like this:


```
BBBBBBBBBBBBBBBeBBBBBBBBBBBBBB
B  # #       #  #  #         B
B#   # # ### # # #   ####### B
B# #   #    #  #   ##       #B
B  #### ###  # # #    ##### #B
B #        #   ### # #    #  B
B  ### # #  ###   ###  ##  # B
B#   #  ### # # #  #  ## #   B
B ##  #  #       #   #   # # B
B   #  #  ###########  # #  #B
B #  #   #BBBBBBBBBBB # ###  B
B  #  ## #B         B    ### B
B#  #    #B         B ##  ## B
B  # # # #B         B   #    B
B #   #  #B         B ## ####B
B # #  # #B         B    #   B
B#  ##  ##B         B# #  # #B
B# #  # ##B         B  # #  #B
B  # #   #B         B #   #  B
B #   # ##B         B#  #  # B
B  ## #   BBBBBeBBBB   ### # B
B# #   ##  #    ##   ## #  # B
B  ## #  #  # ##   # #    ## B
B #    #  #   #####  # # #   B
B  # #   # ### #    ##  #  # B
B#  #  #     #   #### #  # # B
B  #  # ## ##  ##      #   # B
B # # #  # #  # # # ### ###  B
B       #    #    #         #B
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
```




## Installation

To install this tool clone the repository:

```
git clone https://github.com/alex4200/PyBlock.git
cd PyBlock
pip install .
```



## Details

The world in minecraft is divided into regions (making up the files the world is stored in), and each region is divided into chunks.
The coordinates of a minecraft block (block coordinates) is given by the tuple (x,y,z) where x and z are the coordinates on the minecraft plane, and y is the height. In a normal minecraft world x and z can take values from -31'000'000 to +31'000'000 and y can range between 0 and 255.

### Regions and Chunks

Each region is a 512x512 block area of the map (region coordinates). Each region is stored in a seperate file (named `r.x.z.mca`, e.g. `r.-5.11.mca`). 

When we define  

s<sub>r</sub>=512

as the region size, the region a block belongs to is

![block region](doc/images/Tex2Img_1575490739.jpg)

where the brackets denote the `floor` funtion, which returns the closest integer value which is less than or equal to the specified expression or value.


In the other way around you might ask the range of a region in block coordinates, then you can calculate it via

![block chunk](doc/images/Tex2Img_1575489552.jpg)

### Chunks

Each region is divided into 32x32 chunks, which consist of 16x16 blocks each. So when we define 

s<sub>c</sub>=16

as the chunk size, then the chunk coordinates a block belongs to is

![block chunk](doc/images/Tex2Img_1575490796.jpg)

and similar the range of a chunk in block coordinates is calculated as 

![block chunk](doc/images/Tex2Img_1575489907.jpg)


### Sections

Each chunk itself is further divided into 'sections' which represent a 16x16x16 cuboid block area. Each chunk has 16 vertical stacked sections.


## Acknowledgment

This tool is based on the package [anvil-parser](https://github.com/matcool/anvil-parser).

## Further information

Last update was tested on Minecraft version **1.16.5** with python 3.8.7.


