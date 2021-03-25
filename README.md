# PyBlock

This package helps to explore and examine your minecraft world. Find special blocks or get some overview of what you can find in your region/area of interest!

## Usage

Five tools can help to enhance your Minecraft experience. 
`mc-list` lists all blocks found in an area, `mc-find` lists the coordinates of a block in a certain area, `mc-plot` creates overview plots of each level across the y direction and `mc-copy` can be used to copy whole areas from one place to another place (even across different worlds!). 

The fifth tool is a module `mc-edit` that enables editing existing worlds with python code. You can build your house, a wall, a maze, whatever you like. 

In order to use the tools you have to specify the path to your minecraft world. You can do that either by specifying the argument `--world` or by specifying the environment variable `MINECRAFTWORLD`.

Example:

```
export MINECRAFTWORLD=/home/user/some/path/minecraft/saves/MyWorld
```

For each command you can also set a verbosity to get more debug output, i.e. `-vvv`

### Listing all blocks

`mc-list  --coords 100 40 -400 --radius 40 `

This command lists all the blocks found in an cuboid area around the coordinates (100,40,-400) within a box-'radius' of 40. The search area is a box with minimal coordinates (60, 0, -440) and maximal coordinates (1400, 80, -360).

You can specify the argument `--vertical` to search the complete vertical column. In the example that would be a box with minimal coordinates (60, 0, -440) and maximal coordinates (1400, 255, -360).

To list blocks in the nether you can use the option `--dimension nether`.

### Finding a block

`mc-block --coords 100 40 -400 --radius 20 --block diamond_ore`

This command lists the exact block coordinates of each occurance of the block type 'diamond_ore' that has been found in the specified search area.

To find blocks in the nether you can use the option `--dimension nether`.

### Plotting all levels in an area

You also can use a tool to analyze a complete region file, e.g.

`mc-plot --coords 100 40 200 --radius 100 --output Levels`

This command creates a very simple plot of each level around the coordinates (100,40,200) within a 'radius' of 100 blocks, and stores it in the specified folder. Each block gets a color according to the mapping in the file `block_colors.py`. 

Blocks for which a color is undefined are colored in red. When running this command with `-v` a list of all undefined blocks are listed on the terminal.  

### Copying chunks

This command can be used to copy some areas around. Be careful to use this command, as it can disrupt your landscapes!

To copy a 40x40 block area from 100/100 to 500/200, the command is

`mc-copy --source 100 100 --dest 500 200 --size 40 40`

This command will give you the following output:

```
This would copy a size of 48x48 blocks from coordinates 96/96 to 496/192
This is a dry run. If you are happy with the coordinates, add '--no-test' to the command.
```

As only complete chunks can be copied, the final coordinates might differ slightly from the given coordinates. They have to be a multiple of 16 (which is the size of a chunk). 

If you are satisfied with the actual choice of coordinates, you need to add the option `--no-test` to make the actual changes:

```
mc-copy --source 100 100 --dest 500 200 --size 40 40 --no-test
```

You can even use a completly different world as a source! Just use the argument `--world-source` to copy from a different world. 

```
mc-copy --source 100 100 --dest 500 200 --size 40 40 --world-source /path/to/the/source/world --no-test
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


