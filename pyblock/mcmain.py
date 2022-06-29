#!/usr/bin/env python3
"""
Application to analyze and find block in minecraft.
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203

import os
import logging
from pathlib import Path

import click

import pyblock
from pyblock import mapper, tools

L = logging.getLogger("pyblock")


option_verbose = click.option(
    "-v", "--verbose", count=True, default=0, help="-v for DEBUG"
)
option_world = click.option(
    "--world", help="Path to the minecraft world. Or define MINECRAFTWORLD."
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
option_position = click.option(
    "-p",
    "--position",
    nargs=3,
    type=int,
    help="Complete 3-dimensional position (x/y/z).",
)
option_radius = click.option(
    "-r", "--radius", type=int, help="The search radius (in block units, max 200)."
)
option_region = click.option(
    "--region", nargs=2, type=int, help="Region file coordinates (x/z)."
)


# Define the command group with common verbose settings
@click.group()
@option_verbose
def cli(verbose):
    """Set the logging level."""
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
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the 3D area to analzye
    y_section_range = tools.Y_SECTION_RANGE[dimension]
    ymin = 16 * y_section_range[0]
    ymax = 16 * y_section_range[1]
    x, z = coords
    start = [x - radius, ymin, z - radius]
    end = [x + radius, ymax, z + radius]

    editor = pyblock.Editor(worldpath)
    blocks = editor.list_blocks(start, end)

    for name, number in blocks.items():
        print(f"{name:15s}: {number:,d}")


@cli.command("find")
@option_world
@option_dimension
@option_coordinates
@option_radius
@option_region
@click.option("-b", "--block", help="The name of the block to be located.")
def mcfind(world, dimension, coords, radius, region, block):
    """Finding block locations in a specified area."""
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the 3D area to analzye
    y_section_range = tools.Y_SECTION_RANGE[dimension]
    ymin = 16 * y_section_range[0]
    ymax = 16 * y_section_range[1]
    x, z = coords
    start = [x - radius, ymin, z - radius]
    end = [x + radius, ymax, z + radius]

    mcblock = pyblock.Block(block)

    editor = pyblock.Editor(worldpath)
    locations = editor.find_blocks(start, end, mcblock)

    print(f"Found '{block}'' at the following locations:")
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
    "--output", help="Output folder for the level plots.", default="MinecraftPlot"
)
@click.option("--colormap", help="Optional colormap to use (JSON file).")
def mcplot(world, dimension, coords, radius, region, output, colormap):
    """Generate rough plots for each level in a specified area."""
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = tools.get_regions(region, coords, radius)
    area = tools.get_area(region, coords, radius)

    pymap = mapper.PyMap(area, output, colormap)
    for region_coords, chunk_list in regions.items():
        # Read the region
        region = pyblock.Region(worldpath, region_coords)
        L.debug(
            f"Analyzing region {region_coords[0]}/{region_coords[1]} with {len(chunk_list)} chunks"
        )

        # parse the data in this region
        pymap.set_blocks_for_map(region, chunk_list)

    # Draw the final map
    if not os.path.exists(output):
        os.makedirs(output)
    pymap.draw()

    # List the unknown blocks
    L.warning("Unknown blocks:")
    for block in pymap.unknown_blocks:
        L.warning(block)


@cli.command("copy")
@option_world
@click.option(
    "--source",
    nargs=3,
    type=int,
    help="Absolute Minecraft coordinates (x/z) specifying the start point of the source.",
)
@click.option(
    "--dest",
    nargs=3,
    type=int,
    help="Absolute Minecraft coordinates (x/z) specifying the start point of the destination.",
)
@click.option(
    "--size",
    nargs=3,
    type=int,
    help="The size of the area to be copied (in (x/z) block units, max 200).",
)
@click.option(
    "--world-source",
    default=None,
    help="Path to the minecraft world the source chunks are taken from",
)
def mccopy(world, source, dest, size, world_source):
    """Copy chunks from one place to another, even from a different world."""
    worldpath = tools.get_world_path(world)

    # Use a different world as the source
    if world_source:
        world_source = Path(world_source) / "region"
    else:
        world_source = worldpath

    # Create the editor instance and copy the blocks
    editor = pyblock.Editor(worldpath)
    editor.copy_blocks(
        source, dest, size, rep=None, world_source=world_source
    )
    editor.done()


@cli.command("chest")
@option_world
@option_dimension
@option_coordinates
@option_radius
@option_region
def mcchest(world, dimension, coords, radius, region):
    """Listing all blocks in a specified area."""
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not coords and not region:
        raise ValueError("Coordinates or region must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the regions and chunks to analyze
    regions = tools.get_regions(region, coords, radius)

    # Create the editor instance and copy the blocks
    editor = pyblock.Editor(worldpath)
    editor.analyze_chest(regions)
    editor.done()


@cli.command("walker")
@option_world
@option_dimension
@option_position
@option_radius
@click.option("-b", "--block", help="The name of the block to be located.")
def mcwalk(world, dimension, position, radius, block):
    """Finding block locations in a specified area and walk the player through."""
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not radius:
        raise ValueError("Radius must be defined.")
    if not position:
        raise ValueError("Position of the player must be defined.")
    if radius > 200:
        raise ValueError("Radius must be below 200.")

    # Get the 3D area to analzye
    y_section_range = tools.Y_SECTION_RANGE[dimension]
    ymin = 16 * y_section_range[0]
    ymax = 16 * y_section_range[1]
    x, _, z = position
    start = [x - radius, ymin, z - radius]
    end = [x + radius, ymax, z + radius]

    mcblock = pyblock.Block(block)

    editor = pyblock.Editor(worldpath)
    editor.wayfinder(position, start, end, mcblock)


@cli.command("image")
@option_world
@option_dimension
@option_position
@click.option("-i", "--image", help="The path to the image to be used.")
@click.option(
    "-s",
    "--scale",
    type=float,
    help="The scale for the image, in (minecraft)meters per (image)pixel.",
)
def mcimage(world, dimension, position, image, scale):
    """Creating a two-dimensional surface image with solid blocks."""
    worldpath = tools.get_world_path(world, dimension)

    # Check input parameters
    if not position:
        raise ValueError("Position of the player must be defined.")

    editor = pyblock.Editor(worldpath)
    editor.surface(image, scale, *position)


if __name__ == "__main__":
    cli()
