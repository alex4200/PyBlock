"""
Main Code for editing blocks
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203,R1732,W1514,R0912,R0903,R0902,R0911
# pylint: disable=R1716,R0915,R1702

import os
import sys
import copy
import json
import logging
import operator
from pathlib import Path
from collections import OrderedDict
from collections import defaultdict

from PIL import Image
import numpy as np

import pyblock
from pyblock import tools


L = logging.getLogger("pyblock")
L.setLevel(logging.DEBUG)
log_format = logging.Formatter(
    "%(levelname)s  %(asctime)s.%(msecs)03d  %(message)s", "%H%M%S"
)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(log_format)
L.addHandler(handler)


class Editor:
    """Minecraft Editor."""

    def __init__(self, path: str):
        """Initialize the editor with the path to the world.

        Args:
                path: Path to the world folder.
        """
        # Set the world path
        if str(path).endswith("region"):
            self.path = Path(path)
        else:
            self.path = Path(path) / "region"

        # Dict for the blocks to be set
        # key: region index (x,z)
        # value: dict of blocks for this region:
        #        key: chunk coordinates (x,z)
        #        value: list of (block, x, y, z)
        self.blocks_map = {}

        # Dictionary holding local section data for 'get_block'
        self.sections = {}
        self.chunks = {}

        # Dictionary holding local section data for 'set_block'
        self.write_sections = {}
        # self.write_chunks = {}

        # Dictionary to hold entities when copying blocks
        self.entities = {}

    @staticmethod
    def set_verbosity(verbose: int):
        """Sets the verbosity level. Possible values are 0, 1 or 2"""
        level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
        L.setLevel(level)

    def set_block(self, block: pyblock.Block, x: int, y: int, z: int):
        """
        Records position and block to be modified.

        Args:
                block: Minecraft block
                x, y, z: Absolute coordinates
        """
        # Get the region and the chunk coordinates where to set the block
        region_coord, chunk_coord, ylevel, block_index = tools.block_to_id_index(
            x, y, z
        )
        section_id = (region_coord, chunk_coord, ylevel)

        # Create the location to change (block and coordinates inside the chunk)
        change = (block, block_index)

        if section_id in self.blocks_map:
            self.blocks_map[section_id].append(change)
        else:
            self.blocks_map[section_id] = [change]

    def get_block(self, x: int, y: int, z: int) -> pyblock.Block:
        """Returns the block at the given absolute coordinates.

        Args:
            x, y, z: Absolute coordinates
        """
        # Get the ID of the section and the index of the block for that section
        region_coord, chunk_coord, ylevel, block_index = tools.block_to_id_index(
            x, y, z
        )
        section_id = (region_coord, chunk_coord, ylevel)

        # Check if the chunk is already in the local cache
        if section_id not in self.sections:
            section = self.get_section(section_id)
            self.sections[section_id] = section

        # Return the block from the section
        return self.sections[section_id].get_block(block_index)

    def get_section(self, section_id) -> pyblock.Section:
        """Reads a section from file.

        Args:
            section_id: ID of region_index, chunk_index and ylevel
        """
        region_coord, chunk_coord, ylevel = section_id
        chunk_id = (region_coord, chunk_coord)

        # Check if we have read the chunk already
        if chunk_id in self.chunks:
            L.info(f"Cached chunk from region {region_coord} | chunk {chunk_coord}")
            chunk = self.chunks[chunk_id]
        else:
            # return self.chunks[chunk_id].get_section(ylevel)
            L.info(f"Reading chunk from region {region_coord} | chunk {chunk_coord}")

            # Read the region
            region = pyblock.Region(self.path, region_coord)

            # Read the chunk
            chunk = region.read_chunk(chunk_coord)
            self.chunks[chunk_id] = chunk

        # Return the section
        return chunk.get_section(ylevel)

    def place_piece(
        self,
        x1: int,
        y1: int,
        z1: int,
        block_floor: pyblock.Block,
        block_fill: pyblock.Block,
        block_ceil: pyblock.Block,
        height: int = 4,
        mag: int = 1,
    ):
        """Places an element of the maze.

        Args:
            x1: x coordinate
            y1: y coordinate
            z1: z coordinate
            block_floor: minecraft block for the floor
            block_fill:  minecraft block to fill
            block_ceil:  minecraft block for the ceiling
            height: The height of the walls
            mag: Magnifier of the maze. 1 means 1:1 size, 2 means all walls, ways
                 are double size etc.
        """
        for dx in range(mag):
            for dz in range(mag):
                x = x1 + dx
                z = z1 + dz
                self.set_block(block_floor, x, y1, z)
                for y in range(y1, y1 + height):
                    self.set_block(block_fill, x, y + 1, z)
                self.set_block(block_ceil, x, y1 + height + 1, z)

    def create_maze(
        self, maze: list, coord: list, blocks: list, height: int = 4, mag: int = 1
    ):
        """Creates and places a maze with given width and height.
        start_coord is the starting coorinates (x,y,z) and
        blocks is a list of the three blocks for the floow, the wall and the ceiling.

        Args:
            size (int, int): Size of the maze in x/z direction
            coord (int, int, int): Start coordinates of the maze
            blocks (string, string, string): Names for the blocks for floor, wall and ceiling
            height (int): Height of the inside of the maze (default: 4)
            mag (int): Magnifier number of the maze (thickness of path/walls)
        """
        # Get the maze as a simple 0/1 matrix
        matrix = maze.get_matrix()

        # Define the blocks
        block_floor = pyblock.Block(blocks[0])
        block_wall = pyblock.Block(blocks[1])
        block_ceil = pyblock.Block(blocks[2])
        block_air = pyblock.Block("air")

        # Get the start coordinates
        x0 = coord[0]
        y0 = coord[1]
        z0 = coord[2]

        # Place the walls, floor and ceiling
        for row, lines in enumerate(matrix):
            for col, block in enumerate(lines):
                x = x0 + mag * row
                z = z0 + mag * col

                if block:
                    self.place_piece(
                        x,
                        y0,
                        z,
                        block_floor,
                        block_wall,
                        block_ceil,
                        height=height,
                        mag=mag,
                    )
                else:
                    self.place_piece(
                        x,
                        y0,
                        z,
                        block_floor,
                        block_air,
                        block_ceil,
                        height=height,
                        mag=mag,
                    )

    def copy_blocks(
        self,
        source: list,
        dest: list,
        size: list,
        rep: list = None,
        world_source: str = None,
    ):
        """Copy an area of given size from source to dest (by blocks).

        Args:
            source: x,y,z coordinates of the source.
            dest: x,y,z coordinate of the destination.
            size: x,y,z size of the area top copy
            world_source: Defines the world to copy from. Default is same world.
        """
        if world_source:
            source_world = Editor(world_source)
        else:
            source_world = self

        sx, sy, sz = source
        tx, ty, tz = dest
        wx, wy, wz = size

        for dx in range(wx):
            for dy in range(wy):
                for dz in range(wz):
                    block = source_world.get_block(sx + dx, sy + dy, sz + dz)

                    if rep:
                        for repetition in rep:
                            rx, ry, rz = repetition
                            self.set_block(
                                block, tx + dx + rx, ty + dy + ry, tz + dz + rz
                            )
                    else:
                        self.set_block(block, tx + dx, ty + dy, tz + dz)

        ## Handle the block entities

        # Get the shift for the copy
        shift_x = tx - sx
        shift_y = ty - sy
        shift_z = tz - sz

        # Extract all entities from the source chunks
        self.entities = defaultdict(list)
        for chunk_coord, chunk in source_world.chunks.items():
            for entity in chunk.nbt_data["block_entities"]:
                x = entity["x"].value
                y = entity["y"].value
                z = entity["z"].value

                # Check if the entity is part of the area to copy
                if x >= sx and x < sx + wx:
                    if y >= sy and y < sy + wy:
                        if z >= sz and z < sz + wz:
                            #print("testtest")
                            L.info(
                                f"Found entity of type {entity['id'].value} at {x}/{y}/{z}"
                            )
                            # Modify the destination coordinates
                            x += shift_x
                            y += shift_y
                            z += shift_z

                            # Get coordinates for the destination
                            (
                                region_coord,
                                chunk_coord,
                                _,
                                _,
                            ) = tools.block_to_id_index(x, y, z)
                            key = (region_coord, chunk_coord)

                            # Set the new coordinates for the entity
                            entity["x"].value = x
                            entity["y"].value = y
                            entity["z"].value = z
                            L.info(f"   -> changed coordinates to {x}/{y}/{z}")

                            # Record the entity at the destination's coordinates
                            self.entities[key].append(entity)

        # Handle repetitions for entities
        if rep:
            copy_entities = copy.deepcopy(self.entities)

            self.entities = defaultdict(list)
            # Loop over all primary copies of the entities
            for key, entities in copy_entities.items():
                for orig_entity in entities:
                    # Save the original entity
                    self.entities[key].append(orig_entity)

                    # Loop over the repetition
                    for repetition in rep:
                        # Make a deepcopy of the entity for each repetition
                        entity = copy.deepcopy(orig_entity)

                        # Calculate the new location of the repeated entity
                        rx, ry, rz = repetition
                        x = entity["x"].value + rx
                        y = entity["y"].value + ry
                        z = entity["z"].value + rz

                        # Get the new key for the new location
                        (
                            region_coord,
                            chunk_coord,
                            _,
                            _,
                        ) = tools.block_to_id_index(x, y, z)
                        key = (region_coord, chunk_coord)

                        # Set the new coordinates for the entity
                        entity["x"].value = x
                        entity["y"].value = y
                        entity["z"].value = z
                        L.info(f"   -> changed repeated coordinates to {x}/{y}/{z}")

                        # Save entity
                        self.entities[key].append(entity)

    def analyze_chest(self, regions: dict):
        """Analyzes all chests found in the areas."""

        # Loop over all regions and chunks to analyze
        for region_coords, chunk_list in regions.items():

            # Read the region
            region = pyblock.Region(self.path, region_coords)
            L.debug(
                f"Analyzing region {region_coords[0]}/{region_coords[1]} "
                f"with {len(chunk_list)} chunks"
            )

            # region.analyze_chest(chunk_list)
            for chunk_coord in chunk_list:

                # Read the chunk
                chunk = region.read_chunk(chunk_coord)

                base_x = 512 * region.x + 16 * chunk_coord[0]
                base_z = 512 * region.z + 16 * chunk_coord[1]
                L.debug(f"Analyzing {base_x}/{base_z} to {base_x+15}/{base_z+15}")

                if "block_entities" not in chunk.nbt_data:
                    continue

                for entity in chunk.nbt_data["block_entities"]:
                    eid = entity["id"].value

                    # Check if we have a chest
                    if eid == "minecraft:chest":
                        x = entity["x"].value
                        y = entity["y"].value
                        z = entity["z"].value

                        # Print the coordinates and the content
                        print(f"Chest at {x=}  {y=}  {z=} contains:")
                        try:
                            for item in entity["Items"]:
                                iid = item["id"].value
                                n = item["Count"].value
                                print(f"    {n} {iid}")
                        except KeyError:
                            print("Unknown content")

    def list_blocks(self, start: list, end: int) -> dict:
        """List all blocks in the given region of radius around coordinates

        Args:
            start: x,y,z start coordinates
            end: x,y,z end coordinates
        """
        blocks = {}
        for x in range(start[0], end[0]):
            for z in range(start[2], end[2]):
                for y in range(start[1], end[1]):
                    block = self.get_block(x, y, z)

                    if block.id in blocks:
                        blocks[block.id] += 1
                    else:
                        blocks[block.id] = 1

        # Create final sorted output for console
        sorted_tuples = sorted(blocks.items(), key=operator.itemgetter(1))
        sorted_dict = OrderedDict()
        for k, v in sorted_tuples[::-1]:
            sorted_dict[k] = v

        return sorted_dict

    def find_blocks(
        self, start: list, end: int, block: pyblock.Block, exact: bool = False
    ) -> dict:
        """List all blocks in the given region of radius around coordinates

        Args:
            start: x,y,z start coordinates
            end: x,y,z end coordinates
            block: Block to search for
            exact: True, if an exakt match is required including the properties
        """

        def comp_exact(block, myblock):
            return block == myblock

        def comp_name(block, myblock):
            return block.id == myblock.id

        if exact:
            fun_compare = comp_exact
        else:
            fun_compare = comp_name

        locations = []
        for x in range(start[0], end[0]):
            for z in range(start[2], end[2]):
                for y in range(start[1], end[1]):
                    #print(f"{x=}  {y=}  {z=}   {self.get_block(x,y,z)}")
                    if fun_compare(block, self.get_block(x, y, z)):
                        locations.append((x, y, z))

        return locations

    def wayfinder(self, position: list, start: list, end: int, block: pyblock.Block):
        """Prints the next location of the given block in that area."""
        def dist(a, b):
            """Returns the taxicab distance between two points"""
            dx = abs(a[0] - b[0])
            dy = abs(a[1] - b[1])
            dz = abs(a[2] - b[2])
            return dx + dy + dz

        locations = self.find_blocks(start, end, block)
        print(locations)

        while True:

            # calculate distances
            distances = [dist(position, location) for location in locations]
            index = distances.index(min(distances))

            next_coord = locations[index]
            next_dist = distances[index]
            dx = next_coord[0] - position[0]
            dy = next_coord[1] - position[1]
            dz = next_coord[2] - position[2]

            print(
                f"Go   dx: {dx}  dz: {dz}  dy: {dy} "
                f"for next location at {next_coord} with distance {next_dist}.  "
            )

            key = input("Enter key: ")
            if key == "q":
                sys.exit(0)

            # remove the coordinate
            locations.remove(next_coord)
            position = next_coord

    @staticmethod
    def search_closest_color(colormap: dict, color: list) -> str:
        """Searches the item from the colormap with the color closest to 'color'.

        Args:
            colormap: dict with item as key and color as value
            color: the RGB tuple defining a color
        """
        mindist = 10000
        minitem = None
        for item, col in colormap.items():
            dr = col[0] - color[0]
            dg = col[1] - color[1]
            db = col[2] - color[2]
            dist = np.sqrt(dr * dr + dg * dg + db * db)
            if dist < mindist:
                mindist = dist
                minitem = item
        return minitem

    def surface(
        self, imagefile: str, scale: float, start_x: int, start_y: int, start_z: int
    ):
        """Create a 2-dimensional surface based on a real image.

        Args:
            imagefile: Name of the file for the image
            scale: scaling factor, meters per pixel.
            start_x, start_y, start_z: Start coordinates to place the surface
        """
        # Read image and get image size
        img = Image.open(imagefile)
        width, height = img.size

        # Get the size of the minecraft area in meters (or blocks)
        width_meter = int(width * scale)
        height_meter = int(height * scale)

        L.info(
            f"Image of size {width}x{height} will create a minecraft surface of "
            f"{width_meter}x{height_meter} blocks"
        )

        # Load default color map
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/color_map.json", encoding="UTF-8") as json_file:
            all_colors = json.load(json_file)

        # Read the list of blocks to use and create the colormap from these blocks only
        with open(path + "/block_items.txt") as filein:
            blocks_to_use = [word.split(":")[1] for word in filein.read().splitlines()]
        colormap = {
            item: color for item, color in all_colors.items() if item in blocks_to_use
        }

        # Define a reverse map (to retrieve a block for a known color; performance increase)
        reversemap = {}

        # define stone block (on which the surface will be created) and air block
        # to remove all above the surface
        air = pyblock.Block("air")
        stone = pyblock.Block("stone")

        # Loop over the minecraft surface
        for index_x in range(width_meter):
            for index_z in range(height_meter):

                # Get the corresponding location of the pixel on the original image
                # No interpolation will be done!
                pixel_x = int(index_x / scale)
                pixel_y = int(index_z / scale)
                color = img.getpixel((pixel_x, pixel_y))

                # Check if the color is in the reverse map
                if color in reversemap:
                    block = reversemap[color]
                else:
                    # Otherwise find the item with the closest color and get the block
                    item = self.search_closest_color(colormap, color)
                    block = pyblock.Block(item)
                    reversemap[color] = block

                # Get the plot coordinates
                plot_x = start_x + index_x
                plot_y = start_y
                plot_z = start_z + index_z

                L.debug(
                    f"index: {index_x}/{index_z}  pixel: {pixel_x}/{pixel_y} "
                    f"plot: {plot_x}/{plot_z}  {color=}   {item=}"
                )
                # Set the block at this position above a stone block, and remove all above it
                self.set_block(stone, plot_x, plot_y - 1, plot_z)
                self.set_block(block, plot_x, plot_y, plot_z)
                for y in range(plot_y + 1, 320):
                    self.set_block(air, plot_x, y, plot_z)

        # write the blocks
        self.done()

    def done(self):
        """
        Modify the world with the recorded blocks.
        """
        regions = {}
        # Update the blocks in each affected destination section
        for section_id, updates in self.blocks_map.items():
            region_coord, chunk_coord, ylevel = section_id

            L.info(f"Modifying chunk for region {region_coord} | chunk {chunk_coord}")
            if section_id not in self.write_sections:
                section = self.get_section(section_id)
                self.write_sections[section_id] = section

            for update in updates:
                self.write_sections[section_id].set_block(*update)

            # Store regions that needs to be updated
            if region_coord in regions:
                regions[region_coord].append((chunk_coord, ylevel))
            else:
                regions[region_coord] = [(chunk_coord, ylevel)]

        # Handle all modified regions
        for region_coord, chunk_id in regions.items():
            # Read the region
            region = pyblock.Region(self.path, region_coord)

            # Create the chunk indices
            chunks = {}
            for chunk_coord, ylevel in chunk_id:
                if chunk_coord in chunks:
                    chunks[chunk_coord].append(ylevel)
                else:
                    chunks[chunk_coord] = [ylevel]

            # Handle all modified chunks
            updated_chunks = {}
            for chunk_coord, ylevels in chunks.items():
                key = (region_coord, chunk_coord)
                if key in self.entities:
                    entities_to_update = self.entities[key]
                else:
                    entities_to_update = []
                chunk = region.get_chunk(chunk_coord)

                for ylevel in ylevels:
                    # print(chunk_coord, ylevel)

                    section_id = (region_coord, chunk_coord, ylevel)
                    section = self.write_sections[section_id]
                    chunk.set_section(ylevel, section.get_nbt())

                # Store the manipulated chunk
                updated_chunks[chunk_coord] = chunk.get_bytes(entities_to_update)

            # write the region with the updated chunks
            region.write(updated_chunks)
