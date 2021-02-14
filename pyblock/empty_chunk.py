from typing import List
from io import BytesIO
import zlib
from .block import Block
from .empty_section import EmptySection
from .errors import OutOfBoundsCoordinates, EmptySectionAlreadyExists
from nbt import nbt

class EmptyChunk:
    """
    Used for making own chunks

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    sections: List[:class:`anvil.EmptySection`]
        List of all the sections in this chunk
    version: :class:`int`
        Chunk's DataVersion
    """
    __slots__ = ('x', 'z', 'sections', 'version')
    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.sections: List[EmptySection] = [None]*16
        self.version = 1976

    def add_section(self, section: EmptySection, replace: bool = True):
        """
        Adds a section to the chunk

        Parameters
        ----------
        section
            Section to add
        replace
            Whether to replace section if one at same Y already exists
        
        Raises
        ------
        anvil.EmptySectionAlreadyExists
            If ``replace`` is ``False`` and section with same Y already exists in this chunk
        """
        if self.sections[section.y] and not replace:
            raise EmptySectionAlreadyExists(f'EmptySection (Y={section.y}) already exists in this chunk')
        self.sections[section.y] = section

    def get_block(self, x: int, y: int, z: int) -> Block:
        """
        Gets the block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of 0 to 255

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        Returns
        -------
        block : :class:`anvil.Block` or None
            Returns ``None`` if the section is empty, meaning the block
            is most likely an air block.
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < 0 or y > 255:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[y // 16]
        if section is None:
            return
        return section.get_block(x, y % 16, z)

    def set_block(self, block: Block, x: int, y: int, z: int):
        """
        Sets block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of 0 to 255

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < 0 or y > 255:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[y // 16]
        if section is None:
            section = EmptySection(y // 16)
            self.add_section(section)
        section.set_block(block, x, y % 16, z)

    # New added method to get the actual 4096-sized data bytes to be added
    # Extracted from the region save method
    def get_data(self):
        chunk_data = BytesIO()

        # Get the chunk data as NBT data and write it to 'chunk_data'
        nbt_data = self.save()
        nbt_data.write_file(buffer=chunk_data)

        # Compress the data
        chunk_data.seek(0)
        chunk_data = zlib.compress(chunk_data.read())

        # Create the byte block
        bytes_data = (len(chunk_data)+1).to_bytes(4, 'big') + b'\x02' + chunk_data

        #     # offset in 4KiB sectors
        #sector_offset = 0 #len(chunks_bytes) // 4096
        #sector_count = math.ceil(len(to_add) / 4096)
        #     offsets.append((sector_offset, sector_count))

        # Padding to be a multiple of 4KiB long
        bytes_data += bytes(4096 - (len(bytes_data) % 4096))
        assert len(bytes_data) % 4096 == 0

        return bytes_data


    def save(self) -> nbt.NBTFile:
        """
        Saves the chunk data to a :class:`NBTFile`

        Notes
        -----
        Does not contain most data a regular chunk would have,
        but minecraft stills accept it.
        """
        root = nbt.NBTFile()
        root.tags.append(nbt.TAG_Int(name='DataVersion',value=self.version))
        level = nbt.TAG_Compound()
        # Needs to be in a separate line because it just gets
        # ignored if you pass it as a kwarg in the constructor
        level.name = 'Level'
        level.tags.extend([
            nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='TileEntities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='LiquidTicks', type=nbt.TAG_Compound),
            nbt.TAG_Int(name='xPos', value=self.x),
            nbt.TAG_Int(name='zPos', value=self.z),
            nbt.TAG_Long(name='LastUpdate', value=0),
            nbt.TAG_Long(name='InhabitedTime', value=0),
            nbt.TAG_Byte(name='isLightOn', value=1),
            nbt.TAG_String(name='Status', value='full')
        ])
        sections = nbt.TAG_List(name='Sections', type=nbt.TAG_Compound)
        for s in self.sections:
            if s:
                p = s.palette()
                # Minecraft does not save sections that are just air
                # So we can just skip them
                if len(p) == 1 and p[0].name() == 'minecraft:air':
                    continue
                sections.tags.append(s.save())
        level.tags.append(sections)
        root.tags.append(level)
        return root
