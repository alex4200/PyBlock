# PyBlock

This tool helps to explore and examine your minecraft world. Find special blocks or get some overview of what you can find in your region/area of interest!

## Details

The world in minecraft is divided into regions (making up the files the world is stored in), and each region is divided into chunks.
The coordinates of a minecraft block (block coordinates) is given by the tuple (x,y,z) where x and z are the coordinates on the minecraft plane, and y is the height. In a normal minecraft world x and z can take values from -31000000 to !31000000 and y can be between 0 and 255.

### Regions and Chunks

Each region is a 512x512 block area of the map (region coordinates). Each region is stored in a seperate file (named `r.x.z.mca`, e.g. `r.-5.11.mca`). When we define  

s<sub>r</sub>=512

as the region size, the region a block belongs to is

![block region](doc/images/Tex2Img_1575490739.jpg)

In the other way around you might ask the range of a region in block coordinates, then you can calculate it via

![block chunk](doc/images/Tex2Img_1575489552.jpg)

### Chunks

Each region is further divided into chunks, which are 16x16 blocks. So when we define 

s<sub>c</sub>=16 as the chunk size, then the chunk coordinates a block belongs to is

![block chunk](doc/images/Tex2Img_1575490796.jpg)

and similar

![block chunk](doc/images/Tex2Img_1575489907.jpg)

------

I refere to this as chunk coordinates.

In the other way around you might ask the range of a region in block coordinates, then you can calculate it via

![block chunk](doc/images/Tex2Img_1575489552.jpg)

and similar

![block chunk](doc/images/Tex2Img_1575489907.jpg)

## Usage

This tool can be used in two ways: List all blocks in a certain area or find the location of blocks in a certain area.

### Listing all blocks

mycraft.py  --coords 100 40 -400 --radius 40 --list

This command lists all the blocks found in an cuboid area around the block at coordinates (100,40,-400) within a box-'radius' of 40. The search area is a box with minimal coordinates (60, 0, -440) and maximal coordinates (1400, 80, -360).

### Finding a block

mycraft.py  --coords 100 40 -400 --radius 20 --find diamond_ore

This command lists the exact block coordinates of each occurance of the block type that has been found in the specified search area.

## Further information


Current specification is on the official [Minecraft Wiki](https://minecraft.gamepedia.com/NBT_format).


Last update was tested on Minecraft version **1.13.4**.


## Dependencies

The library, the tests and the examples are only using the Python core library,
except `curl` for downloading some test reference data and `PIL` (Python
Imaging Library) for the `map` example.

Supported Python releases: 2.7, 3.4 to 3.7

