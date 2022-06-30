# PyBlock

This package helps to explore and examine your minecraft world. Find special blocks, get a graphical overview of your underworld, create any structures and copy areas from one world to another! 


- [Installation](#installation) — Install instructions
- [Usage](#usage) - Usage examples
  - [Listing all blocks](#listing-all-blocks) - How to list all blocks in an area
  - [Finding blocks](#finding-blocks) - Finding the locations of a specic block in an area
  - [Map Creation](#map-creation) - Create maps for each y level.
  - [Chest investigation](#chest-investigation) - Find chests and list their contents
  - [Copying blocks](#copying-blocks) - Copying areas of blocks at other locations
  - [Block Walker](#block-walker) - Walks you to the nearest location of a specific block
  - [Surface image creation](#surface-image-creation) - Creates a surface showing an image
- [Python API](#python-api) - Examples on how to use the API to edit your minecraft world in python
- [Details](#details) Some details on the internals of how minecraft organizes the blocks (regions, chunks and sections)
- [Acknowledgment](#acknowledgment) - Acknowledgements
- [Further Information](#further-information) - Links to further resources



## Installation

To install this tool clone the repository:

```
git clone https://github.com/alex4200/PyBlock.git
cd PyBlock
pip install .
```

## Usage

**Several tools that can help to enhance your Minecraft experience.**


In order to use the tools you have to specify the path to your minecraft world. You can do that either by specifying the argument `--world` or by specifying the environment variable `MINECRAFTWORLD`.

Example:

```
export MINECRAFTWORLD=/home/user/some/path/minecraft/saves/MyWorld
```

#### Important

**Always exit your minecraft game before doing any world manipulations. It could create undesired interferences!**

#### Hints

 * For each command you can set the verbosity to get more debug output, i.e. `pyblock -vv <command>`.

 * If you use large areas, the code might take some minutes to complete. Better to try a smaller area first. 

 * In case you see an error saying `Chunk x/y has not been generated yet` then this specific chunk has not been generated yet. You need to go/fly into this area so that minacraft is creating the world in that area.

Now here come the command line tools:

### Listing all blocks

```
pyblock list  --coords 100 -400 --radius 40 
```

This command lists all the blocks found in an cuboid area around the coordinates x=100, z=-400 within a box-'radius' of 40. The search area is a box with minimal coordinates (60, -64, -440) and maximal coordinates (140, 320, -360). Always the complete vertical rage is used.

To list blocks in the nether you can use the option `--dimension nether`.

### Finding blocks

`pyblock find --coords 100 -400 --radius 20 --block diamond_ore`

This command lists the exact block coordinates of each occurance of the block type `diamond_ore` that has been found in the specified search area.

To find blocks in the nether you can use the option `--dimension nether`.

### Map Creation

You also can use a tool to analyze a complete region file, e.g.

`pyblock plot --coords 100 200 --radius 100 --output Levels`

This command creates a very simple plot of each level around the coordinates x=100, z=200 within a 'radius' of 100 blocks, and stores it in the specified folder. Each block is colored according to the average color of the block's appearance. 

You can override the color for a block by specifying a json file with the color to use for a given block (example: `user_map.json`). That way, you can mark special blocks to stand out. 

### Chest investigation

You can check the content of chests by running the command

`pyblock chest --coords 100 200 --radius 100`

This will list the content of every chest in a  100 block 'radius' around the coordinates 100/200. If a chest has never been opened, the content is not defined and no content will be shown. 

### Copying blocks

This command can be used to copy some areas around. Be careful to use this command, as it can disrupt your landscapes!

To copy a 20x30x20 block area from 0/50/20 to 30/80/40, the command is

`pyblock copy --source 0 50 20 --dest 30 80 40 --size 20 30 20`

You can even use a completly different world as a source! Just use the argument `--world-source` to copy from a different world. 

```
pyblock copy --source 100 0 100 --dest 500 0 200 --size 40 200 40 --world-source /path/to/the/source/world
```


### Block Walker

You can 'help' yourself in survival mode to more easily find rare blocks. You just go to a place where you want to start your search, get your current location, and run the command

```
pyblock walker -p 100 20 200 -r 200 --dimension nether --block ancient_debris
```

and the coordinates of the nearest block is printed out, along with how to get there:

```
Go   dx: -3  dz: 5  dy: 2 for next location at (-3, 32, -13) with distance 3.  
Enter key: 
```

In that case, you have to go from your location 3 blocks in negative x direction 5 blocks in positive z direction and 2 blocks up to find the next block.

Just press `Enter` to see the information to get to the next block and `q` to end the command.

### Surface image creation

You can use the following command to create a surface in the minecraft world to represent any image. You just do e.g.

```
pyblock image -p 0 100 1000 --image examples/birds.jpg -s 1
```

which will re-create the image of the file `birds.jpg`  as a surface with start coordinates 0/100/1000. To creete the image, only solid blocks are being used as defined in `block_items.txt`.

The parameter `s` defines the scaling. (blocks per pixel). For `-s 1` the original scaling of the image will be used, i.e. if the image has a size of 400x300 pixels the resulting surface in minecraft will cover an area of 400x300 blocks. 

If the scale factor is e.g. `0.5`, then the resulting surface in minecraft will be 200x150 blocks.

No interpolation is done.


## Python API
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
 * Not all items are copied correctly; most notable frames.

### Maze Creation

You also can easily create **mazes** within your minecraft world. Each maze contains one path from an entry point to an exit point, without containing any loops. Each generated maze will be different, and you can use your own exterior shape. 

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

See also the example code in `examples`.


### Examples

The folder `examples` contains more examples on how to use the API.




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

### Links

- [NBT format](https://github.com/twoolie/NBT)
- [Region file format](https://minecraft.gamepedia.com/Region_file_format)
- [Chunk format](https://minecraft.fandom.com/wiki/Chunk_format)
- [Entity format](https://minecraft.fandom.com/wiki/Entity_format)
- [Block entity format](https://minecraft.fandom.com/wiki/Chunk_format#Block_entity_format)


### Compatibility

Last update was tested on Minecraft version **1.18.2** and **1.19** with python 3.8.7.


