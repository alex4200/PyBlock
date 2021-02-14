#!/usr/bin/env python3
"""
Application to analyze and find block in minecraft.
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103

import os
import sys
import click
import pprint
import logging
from pathlib import Path
import operator
from collections import OrderedDict

import pyblock
#from pyblock import converter as conv
from pyblock import mapper, tools

L = logging.getLogger("pyblock")
L.setLevel(logging.DEBUG)
log_format = logging.Formatter('%(levelname)s  %(msecs)03d:%(asctime)s  %(message)s', "%H%M%S")                                                  
handler = logging.StreamHandler(sys.stdout)                             
handler.setLevel(logging.DEBUG)                                        
handler.setFormatter(log_format)
L.addHandler(handler)  


def get_world_path(world):
    """Returns the path to the world, either from an environment variable
    or from an argument.
    """
    if world:
        return Path(world) / "region"

    if 'MINECRAFTWORLD' in os.environ:
        return  Path(os.environ['MINECRAFTWORLD']) / "region"
    else:
        raise ValueError("Path to world must be defined. Or set MINECRAFTWORLD.")


def get_area(region, coords, radius, vertical=True):
    """Returns the area in absolute coordinates that is to be searched.
    Either coordinates and radius is defined, or the region. 
    If vertical is True, the whole vertical column is used.
    
    Args:
        region (list): region to use (x/z coordinates)
        coords (list): absolute coordinates of the center point
        radius (int): radius around the center point
        vertical (bool): If True, the whole vertical column is used.
    """
    # Define the search area
    if region:
        area = None
    else:
        coord_min = [c - radius for c in coords]
        coord_max = [c + radius for c in coords]

        # If 'vertical' is True, the whole vertical column is being searched
        if vertical:
            coord_min[1] = -1
            coord_max[1] = 256
        area = (coord_min, coord_max)
    L.debug("Search area: %s" % str(area))
    return area

# TODO: Needs cleanup and documentation
def get_regions(region, coords, radius, vertical=True):
    """Returns a dict of all regions used, with a list of related chunks.

    Args:
        region (list): region to use (x/z coordinates)
        coords (list): absolute coordinates of the center point
        radius (int): radius around the center point
        vertical (bool): If True, the whole vertical column is used.       
    """
    if region:
        regions = {(region[0], region[1]): 'all'}
        check_range = None
    else:
        # Center coordinates
        x_c = coords[0]
        z_c = coords[2]

        # Calculate absolute chunk coordinates
        chunk = tools.block_to_chunk(x_c, z_c)
        L.debug("Middle chunk: %s" % str(chunk))

        # calculate the minimum and maximum chunks for the edges
        chunk_x_min = tools.block_to_chunk(x_c - radius, z_c)[0]
        chunk_x_max = tools.block_to_chunk(x_c + radius, z_c)[0]
        chunk_z_min = tools.block_to_chunk(x_c, z_c - radius)[1]
        chunk_z_max = tools.block_to_chunk(x_c, z_c + radius)[1]

        # x_min = conv.chunk_to_block(chunk_x_min, z_c)[0][0]
        # x_max = conv.chunk_to_block(chunk_x_max, z_c)[0][1]
        # z_min = conv.chunk_to_block(x_c, chunk_z_min)[1][0]
        # z_max = conv.chunk_to_block(x_c, chunk_z_max)[1][1]
        # L.debug("Analyzing blocks: x: %d to %d  z: %d to %d" % (x_min, x_max, z_min, z_max))

        number_chunks = 0
        regions = {}
        for chunk_x in range(chunk_x_min, chunk_x_max+1):
            for chunk_z in range(chunk_z_min, chunk_z_max+1):
                chunk = (chunk_x, chunk_z)
                rel_chunk = (chunk_x % 16, chunk_z % 16)
                number_chunks += 1

                reg = tools.chunk_to_region(*chunk)
                if reg in regions:
                    regions[reg].append(rel_chunk)
                else:
                    regions[reg] = [rel_chunk]

    # Now we have the regions to be analyzed
    L.info("Analyzing %d regions and %d chunks" % (len(regions.keys()), number_chunks))
    return regions


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="-v for DEBUG",
)
@click.option(
    "--world",
    help="Path to the minecraft world. Or define MINECRAFTWORLD.",
)
@click.option(
    "-c",
    "--coords",
    nargs=3,
    type=int,
    help="Basic absolute Minecraft coordinates (x/y/z).",
)
@click.option(
    "-r",
    "--radius",
    type=int,
    help="The search radius (in block units, max 200).",
)
@click.option(
    "--region",
    nargs=2,
    type=int,
    help="Region file coordinates (x/z).",
)
@click.option(
    '--vertical/--no-vertical', 
    default=False,
    help="The whole vertical area is being searched.",
)
def mclist(verbose, world, coords, radius, region, vertical):
    """Command to list the blocks in the specified area.
    """
    # Set the logging level
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    L.setLevel(level)

    worldpath = get_world_path(world)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = get_regions(region, coords, radius, vertical)

    # prepare variables
    blocks = {}
    locations = []
    number_chunks = 0

    # check all regions
    for region_coords, chunk_list in regions.items():

        # Read the region 
        region = pyblock.Region(worldpath, *region_coords)
        L.debug("Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list)))

        blocks_region = region.list_blocks(chunk_list)
        blocks = pyblock.tools.combine_dicts(blocks, blocks_region)
       
    # Create final sorted output for console
    sorted_tuples = sorted(blocks.items(), key=operator.itemgetter(1))
    sorted_dict = OrderedDict()
    for k, v in sorted_tuples[::-1]:
        sorted_dict[k] = v

    for name, number in sorted_dict.items():
        print(f"{name:15s}: {number:,d}")

@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="-v for DEBUG",
)
@click.option(
    "--world",
    help="Path to the minecraft world. Or define MINECRAFTWORLD.",
)
@click.option(
    "-c",
    "--coords",
    nargs=3,
    type=int,
    help="Basic absolute Minecraft coordinates (x/y/z).",
)
@click.option(
    "-r",
    "--radius",
    type=int,
    help="The search radius (in block units, max 200).",
)
@click.option(
    "--region",
    nargs=2,
    type=int,
    help="Region file coordinates (x/z).",
)
@click.option(
    "--vertical/--no-vertical", 
    default=False,
    help="The whole vertical area is being searched.",
)
@click.option(
    "-b",
    "--block", 
    help="The name of the block to be located.",
)
def mcfind(verbose, world, coords, radius, region, vertical, block):
    """Command to find block locations in the specified area.
    """
    # Set the logging level
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    L.setLevel(level)

    worldpath = get_world_path(world)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = get_regions(region, coords, radius, vertical)

    # Search over all involved regions
    locations = []
    for region_coords, chunk_list in regions.items():

        # Read the region 
        region = pyblock.Region(worldpath, *region_coords)
        L.debug("Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list)))

        locations.extend(region.find_blocks(chunk_list, block))

    print(f"Found {block} at the following coordinates:")
    print("    x      y      z")
    for loc in locations:
        print(f"{loc[0]:5d}  {loc[1]:5d}  {loc[2]:5d}")
    print(f"\nFound {len(locations)} locations.")
   
@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="-v for DEBUG",
)
@click.option(
    "--world",
    help="Path to the minecraft world. Or define MINECRAFTWORLD.",
)
@click.option(
    "-c",
    "--coords",
    nargs=3,
    type=int,
    help="Basic absolute Minecraft coordinates (x/y/z).",
)
@click.option(
    "-r",
    "--radius",
    type=int,
    help="The search radius (in block units, max 200).",
)
@click.option(
    "--region",
    nargs=2,
    type=int,
    help="Region file coordinates (x/z).",
)
@click.option(
    "--output",
    help="Output folder for the level plots.",
)
def mcplot(verbose, world, coords, radius, region, output):
    """Command to find block locations in the specified area.
    """
    # Set the logging level
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    L.setLevel(level)

    worldpath = get_world_path(world)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = get_regions(region, coords, radius)
    area = get_area(region, coords, radius)


    # TODO: Old code located in Archive/PyBlock/pyblock
    pymap = mapper.PyMap(area, output)
    for region_coords, chunk_list in regions.items():        
        # Read the region 
        region = pyblock.Region(worldpath, *region_coords)
        L.debug("Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list)))
        
        # parse the data in this region
        pymap = region.set_blocks_for_map(pymap, chunk_list)
    
    # Draw the final map
    pymap.draw()

    # List the unknown blocks
    L.warning("Unknown blocks:")
    for block in pymap.unknown_blocks:
        L.warning(block)

def mccopy():
    L.warning("Not yet implemented")
