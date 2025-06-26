import os
import sys
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'src'))

import types

fake = types.ModuleType("narrator")
fake.Narrator = object
sys.modules["narrator"] = fake

from src import player, world, game


def test_passive_heal_and_corruption():
    w = world.World()
    p = player.Player()
    # add items to inventory and equip them
    p.inventory = ["月神護符", "低語匕首"]
    p.equip_item("月神護符", w)
    p.equip_item("低語匕首", w)
    # reduce hp to test heal
    p.hp = p.get_max_hp(w) - 10
    game.end_of_turn_effects(p, w)
    assert p.hp == p.get_max_hp(w) - 5
    assert p.corruption == 1 + 5  # initial equip added 5, passive adds 1


