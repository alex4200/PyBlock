#!/usr/bin/env python3
"""Defines a minecraft block."""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,R0401

from nbt import nbt
from frozendict import frozendict


class Block:
    """
    Represents a minecraft block.

    Attributes:
    namespace (str) : Namespace of the block, normally this is `minecraft`
    id (str): Name of the block, for example: `stone`, `diamond_block`, etc.
    properties (dict): Optional Block properties as a dict
    compound (nbt.TAG_Compound): The block as nbt compound tag
    """

    def __init__(
        self,
        name: str = None,
        properties: dict = None,
        compound: nbt.TAG_Compound = None,
        namespace: str = "minecraft",
    ):
        """Defines a block as NBT tag with its properties.

        Args:
            name: Name of the block (or the ID)
            properties: Block properties as dict
            compound: NBT compound containing the block details
            namespace: Namespace of the block. Default: `minecraft`
        """
        if properties is None:
            properties = {}
        if compound:
            # Extracts name, stores compound
            self.id = compound["Name"].value
            self.compound = compound
            self.properties = {}
            if "Properties" in compound:
                self.properties = {
                    k: v.value for k, v in compound["Properties"].items()
                }
        else:
            # Creates name, and compound
            self.id = namespace + ":" + name
            self.compound = nbt.TAG_Compound()
            self.properties = {}
            if properties:
                # Transform block properties from a simple dict to the NBT dict
                nbt_properties = nbt.TAG_Compound(name="Properties")
                for prop_name, prop_value in properties.items():
                    nbt_properties.tags.append(
                        nbt.TAG_String(name=prop_name, value=prop_value)
                    )
                    self.properties[prop_name] = prop_value
                self.compound.tags.append(nbt_properties)
            self.compound.tags.append(nbt.TAG_String(name="Name", value=self.id))

    def name(self) -> str:
        """
        Returns the block name (or the ID) in the ``minecraft:block_id`` format
        """
        return self.id

    def __repr__(self):
        """Representation of this object."""
        return f"Block({self.id} {self.properties})"

    def __eq__(self, other):
        """Equality operator."""
        if not isinstance(other, Block):
            return False

        return self.id == other.id and self.properties == other.properties

    def __hash__(self):
        return hash(self.name()) ^ hash(frozendict(self.properties))
