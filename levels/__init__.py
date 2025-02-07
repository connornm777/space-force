from .flat import LevelFlat
from .star import LevelStar
from .blackhole import LevelBlackHole

def get_all_levels():
    """
    Return a dictionary of all available level names -> level classes.
    If you create a new level file, just import and add it here.
    """
    return {
        "Flat": LevelFlat,
        "Star": LevelStar,
        "Hole": LevelBlackHole
    }

def create_level(name):
    """
    Create a new level instance by name. Fallback to Flat if unknown.
    """
    levels = get_all_levels()
    level_cls = levels.get(name, LevelFlat)
    return level_cls()
