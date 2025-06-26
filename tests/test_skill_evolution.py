import os
import sys
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'src'))

import pytest
from src import player, world


def test_evolve_skill_success():
    w = world.World()
    p = player.Player()
    p.skills = ["駭客術"]
    p.growth_points = 5
    assert p.evolve_skill("駭客術", w)
    assert p.skills == ["資料探勘"]
    assert p.growth_points == 2


def test_evolve_skill_insufficient_gp():
    w = world.World()
    p = player.Player()
    p.skills = ["火球術"]
    p.growth_points = 2
    assert not p.evolve_skill("火球術", w)
    assert p.skills == ["火球術"]



