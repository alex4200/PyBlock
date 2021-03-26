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
from pyblock import mapper, tools

L = logging.getLogger("pyblock")
L.setLevel(logging.DEBUG)
log_format = logging.Formatter(
    "%(levelname)s  %(msecs)03d:%(asctime)s  %(message)s", "%H%M%S"
)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(log_format)
L.addHandler(handler)


def get_world_path(world, dimension):
    """Returns the path to the world, either from an environment variable
    or from an argument.

    Args:
        world (string): Optional path to the world to be used.
        dimension (string): The dimension to use (overworld, nether)

    Returns:
        string: Path to the world to be used.
    """
    if dimension == "nether":
        dim_path = "DIM-1/region"
    else:
        dim_path = "region"

    if world:
        return Path(world) / dim_path

    if "MINECRAFTWORLD" in os.environ:
        return Path(os.environ["MINECRAFTWORLD"]) / dim_path
    else:
        raise ValueError("Path to world must be defined. Or set MINECRAFTWORLD.")


def get_area(region, coords, radius):
    """Returns the area in absolute coordinates that is searched.
    Either coordinates and radius is defined, or the region.

    Args:
        region (list): region to use (x/z coordinates)
        coords (list): absolute coordinates of the center point
        radius (int): radius around the center point

    Returns:
        int, int: area
    """
    # Define the search area
    if region:
        area = None
    else:
        coord_min = [c - radius for c in coords]
        coord_max = [c + radius for c in coords]
        area = (coord_min, coord_max)
    L.debug("Search area: %s" % str(area))
    return area


def get_chunk_area(x, z, dx, dz):
    """Returns a dict of the regions and the chunks in the specified area.

    Args:
        x (int): x coordinate of the start point.
        z (int): z coordinate of the start point.
        dx (int): size in x direction.
        dz (int): size in z direction.

    Returns:
        dict: Dictionary containing the source chunks
        int, int: Chunk-rounded source coordinates
        int, int: Chunk-rounded size to be copied
    """
    # Calculate the minimum and maximum chunks for the edges
    chunk_x_min = tools.block_to_chunk(x, z)[0]
    chunk_x_max = tools.block_to_chunk(x + dx, z)[0]
    chunk_z_min = tools.block_to_chunk(x, z)[1]
    chunk_z_max = tools.block_to_chunk(x, z + dz)[1]
    L.debug(f"chunk range: {chunk_x_min}/{chunk_z_min} to {chunk_x_max}/{chunk_z_max}")

    xmin = chunk_x_min * tools.CHUNK_SIZE
    zmin = chunk_z_min * tools.CHUNK_SIZE
    xmax = chunk_x_max * tools.CHUNK_SIZE
    zmax = chunk_z_max * tools.CHUNK_SIZE

    number_chunks = 0
    regions = {}
    for chunk_x in range(chunk_x_min, chunk_x_max + 1):
        for chunk_z in range(chunk_z_min, chunk_z_max + 1):
            chunk = (chunk_x, chunk_z)
            rel_chunk = (chunk_x % 32, chunk_z % 32)
            number_chunks += 1

            reg = tools.chunk_to_region(*chunk)
            if reg in regions:
                regions[reg].append(rel_chunk)
            else:
                regions[reg] = [rel_chunk]

    # Now we have the regions to be analyzed
    L.info("Analyzing %d regions and %d chunks" % (len(regions.keys()), number_chunks))
    L.info("Minimum %d/%d to Maximum %d/%d" % (xmin, zmin, xmax, zmax))
    return (
        regions,
        (xmin, zmin),
        (xmax - xmin + tools.CHUNK_SIZE, zmax - zmin + tools.CHUNK_SIZE),
    )


def get_copy_area(source, dest, size):
    """Returns information related to copying chunks. The source and dest coordinates
    will be rounded to the next chunk coordinates. So the source and the dest coordinates
    as well as the sizes will be a multiple of 16 always.

    Args:
        source (int, int): x and z coordinates of the absolute starting block coordinates
        dest (int, int): x and z coordinates of the absolute destination block coordinates
        size (int, int): Size of area to copy in block coordinates

    Returns:
        dict: Dictionary containing the dest chunks, and their respective sources
        int, int: Chunk-rounded source coordinates
        int, int: Chunk-rounded dest coordinates
        int, int: Chunk-rounded size to be copied
    """
    # Find the chunks for the source
    source_regions, source_start, source_size = get_chunk_area(*source, *size)

    # Find the shift from the source to the destination in chunk sizes, and get the dest coords.
    shift_x = (dest[0] - source[0]) // tools.CHUNK_SIZE
    shift_z = (dest[1] - source[1]) // tools.CHUNK_SIZE
    dest_start = (
        source_start[0] + shift_x * tools.CHUNK_SIZE,
        source_start[1] + shift_z * tools.CHUNK_SIZE,
    )
    L.debug(
        f"shift (in chunk units): "
        f"{shift_x} x {shift_z} = {dest_start[0]} x {dest_start[1]} blocks"
    )

    # For each source chunk,
    absolute_source_chunks = []
    dest_regions = {}
    for region, chunks in source_regions.items():
        for chunk in chunks:
            # Calculate absolute source chunk coordinates
            abs_chunk_x = region[0] * tools.CHUNKS_REGION + chunk[0]
            abs_chunk_z = region[1] * tools.CHUNKS_REGION + chunk[1]

            # Add shift from source to dest
            dest_x = abs_chunk_x + shift_x
            dest_z = abs_chunk_z + shift_z

            # And get back region and relative chunks
            dest_region, dest_chunk = tools.abs_chunk_to_region_chunk(dest_x, dest_z)

            # Store the source region and source chunk
            source_item = {"source_region": region, "source_chunk": chunk}
            # Store the source information for each destination chunk, ordered by destination region
            if dest_region in dest_regions:
                dest_regions[dest_region][dest_chunk] = source_item
            else:
                dest_regions[dest_region] = {dest_chunk: source_item}

    return dest_regions, source_start, dest_start, source_size


def get_regions(region, coords, radius):
    """Returns a dictionary containing all related regions (key)
    and the list of relative chunks (values)

    Args:
        region (list): region to use (x/z coordinates)
        coords (list): absolute coordinates of the center point
        radius (int): radius around the center point

    Returns:
        rdict: Dictionary containing all chunks (values) and related regions (keys)
    """
    if region:
        regions = {(region[0], region[1]): "all"}
        check_range = None
    else:
        regions, _, _ = get_chunk_area(
            coords[0] - radius, coords[1] - radius, 2 * radius, 2 * radius
        )

    return regions


option_verbose = click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="-v for DEBUG",
)
option_world = click.option(
    "--world",
    help="Path to the minecraft world. Or define MINECRAFTWORLD.",
)
option_dimension = click.option(
    "--dimension",
    default="overworld",
    help="Specify the dimension to look at (overworld, nether).",
)
option_coordinates = click.option(
    "-c",
    "--coords",
    nargs=2,
    type=int,
    help="Basic absolute Minecraft coordinates (x/z).",
)
option_radius = click.option(
    "-r",
    "--radius",
    type=int,
    help="The search radius (in block units, max 200).",
)
option_region = click.option(
    "--region",
    nargs=2,
    type=int,
    help="Region file coordinates (x/z).",
)


# Define the command group with common verbose settings
@click.group()
@option_verbose
def cli(verbose):
    # Set the logging level
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    L.setLevel(level)


@cli.command("list")
@option_world
@option_dimension
@option_coordinates
@option_radius
@option_region
def mclist(world, dimension, coords, radius, region):
    """Listing all blocks in a specified area."""
    worldpath = get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = get_regions(region, coords, radius)

    # prepare variables
    blocks = {}
    locations = []
    number_chunks = 0

    # check all regions
    for region_coords, chunk_list in regions.items():

        # Read the region
        region = pyblock.Region(worldpath, *region_coords)
        L.debug(
            "Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list))
        )

        blocks_region = region.list_blocks(chunk_list)
        blocks = pyblock.tools.combine_dicts(blocks, blocks_region)

    # Create final sorted output for console
    sorted_tuples = sorted(blocks.items(), key=operator.itemgetter(1))
    sorted_dict = OrderedDict()
    for k, v in sorted_tuples[::-1]:
        sorted_dict[k] = v

    for name, number in sorted_dict.items():
        print(f"{name:15s}: {number:,d}")


@cli.command("find")
@option_world
@option_dimension
@option_coordinates
@option_radius
@option_region
@click.option(
    "-b",
    "--block",
    help="The name of the block to be located.",
)
def mcfind(world, dimension, coords, radius, region, block):
    """Finding block locations in a specified area."""
    worldpath = get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = get_regions(region, coords, radius)

    # Search over all involved regions
    locations = []
    for region_coords, chunk_list in regions.items():

        # Read the region
        region = pyblock.Region(worldpath, *region_coords)
        L.debug(
            "Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list))
        )

        locations.extend(region.find_blocks(chunk_list, block))

    print(f"Found {block} at the following coordinates:")
    print("    x      y      z")
    for loc in locations:
        print(f"{loc[0]:5d}  {loc[1]:5d}  {loc[2]:5d}")
    print(f"\nFound {len(locations)} locations.")


@cli.command("plot")
@option_world
@option_dimension
@option_coordinates
@option_radius
@option_region
@click.option(
    "--output",
    help="Output folder for the level plots.",
)
def mcplot(world, dimension, coords, radius, region, output):
    """Generate rough plots for each level in a specified area."""
    worldpath = get_world_path(world, dimension)

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

    pymap = mapper.PyMap(area, output)
    for region_coords, chunk_list in regions.items():
        # Read the region
        region = pyblock.Region(worldpath, *region_coords)
        L.debug(
            "Analyzing region %d/%d with %d chunks" % (*region_coords, len(chunk_list))
        )

        # parse the data in this region
        pymap = region.set_blocks_for_map(pymap, chunk_list)

    # Draw the final map
    pymap.draw()

    # List the unknown blocks
    L.warning("Unknown blocks:")
    for block in pymap.unknown_blocks:
        L.warning(block)


@cli.command("copy")
@option_world
@click.option(
    "--source",
    nargs=2,
    type=int,
    help="Absolute Minecraft coordinates (x/z) specifying the start point of the source.",
)
@click.option(
    "--dest",
    nargs=2,
    type=int,
    help="Absolute Minecraft coordinates (x/z) specifying the start point of the destination.",
)
@click.option(
    "--size",
    nargs=2,
    type=int,
    help="The size of the area to be copied (in (x/z) block units, max 200).",
)
@click.option(
    "--world-source",
    default=None,
    help="Path to the minecraft world the source chunks are taken from",
)
@click.option(
    "--test/--no-test",
    default=True,
    help="If TRUE, the copy parameters are tested without performing any copying.",
)
def mccopy(world, source, dest, size, world_source, test):
    """Copy chunks from one place to another, even from a different world."""
    worldpath = get_world_path(world)

    # Use a different world as the source
    if world_source:
        world_source = Path(world_source) / "region"
    else:
        world_source = worldpath

    # Get the source and destination regions and sizes to be copied
    dest_regions, start_coord, dest_coord, size_coord = get_copy_area(
        source, dest, size
    )

    if not test:
        # Loop over all regions that are affected
        for dest_region, chunks_to_copy in dest_regions.items():
            region = pyblock.Region(worldpath, *dest_region)
            copy_chunks = region.read_chunks_to_copy(chunks_to_copy, world_source)
            region.write(copy_chunks)
    else:
        L.warning(
            f"This would copy a size of {size_coord[0]}x{size_coord[1]} "
            f"blocks from coordinates {start_coord[0]}/{start_coord[1]} "
            f"to {dest_coord[0]}/{dest_coord[1]}"
        )
        L.warning(
            "This is a dry run. If you are happy with the coordinates, add '--no-test' to the command."
        )
