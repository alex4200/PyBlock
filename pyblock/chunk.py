#!/usr/bin/env python3
"""
This module is a wrapper of the MCA chunk object.
"""

from io import BytesIO

from nbt import nbt
from nbt import chunk as achunk


class Chunk(object):

    # See https://minecraft.gamepedia.com/Chunk_format

    def __init__(self, offset, area, verbose):
        """Initialize this parser object.
        
        Args:
            offset (int): Specifies the location of this chunk within the MCA data.
            area (list): min/max block coordinates to be analyzed.
            verbose (int): verbosity.
        """

        # Offset in the current MCA file
        self.offset = offset
        
        # Search area
        self.area = area

        # verbosity
        self.verbose = verbose

        self.data = None
        self.nbt = nbt

        # The sections containsed in this chunk
        self.sections = []

    def set_timestamp(self, timestamp):
        """Sets the chunk timestamp.
        """
        self.timestamp = timestamp

    def add_data(self, data):
        """Reads the section data from the NBT file.
        """
        self.data =  data
        self.nbt = nbt.NBTFile(buffer = BytesIO(data))
        self.sections = self.nbt.tags[0].get("Sections")

    def get_coords(self):
        """Returns the coordinates of this chunk.
        """
        return (
            int(str(self.nbt.tags[0].get("xPos"))),
            int(str(self.nbt.tags[0].get("zPos")))
            )
    
    def in_area(self, x, y, z):
        """Returns True of the block coordinates are within the seaerch area,
        False otherwise.
        """
        if not self.area:
            return True
        cmin, cmax = self.area
        return x>=cmin[0] and x<cmax[0] and y>=cmin[1] and y<cmax[1] and z>=cmin[2] and z<cmax[2] 

    def get_blocks(self):
        """Returns a dictionary with exact locations for all blocks.
        Only returns blocks that are within 'self.area'.
        
        br = block_range = ((xmin, xmax),(zmin, zmax))
        """
        cx = 16*int(str(self.nbt.tags[0].get('xPos')))
        cz = 16*int(str(self.nbt.tags[0].get('zPos')))

        blocks = {}
        for index, section in enumerate(self.sections[1:]):
            if not 'Palette' in section and not 'Blocks' in section:
                if self.verbose>2:
                   print(f"Empty section found, skipping")
                continue
            if not section.get('Palette'):
                section_version = 0
            else:
                section_version = 1631

            # NBT code:
            ac = achunk.AnvilSection(section, section_version)
            cy = 16*int(str(section.get('Y')))

            for x in range(16):
                for y in range(16):
                    for z in range(16):
                        px = cx + x
                        py = cy + y
                        pz = cz + z
                        if self.in_area(px, py, pz):
                            b = ac.get_block(x,y,z)
                            if b in blocks:
                                blocks[b].append((px, py, pz))
                            else:
                                blocks[b] = [(px, py, pz)]

        return blocks
