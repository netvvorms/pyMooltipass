__all__ = []

def export(definition):
    """
    Decorator to export definitions from sub-modules to the top-level package

    :param definition: definition to be exported
    :return: definition
    """
    # Export the definition to the upper layer
    globals()[definition.__name__] = definition
    __all__.append(definition.__name__)
    return definition

export(export)

from . import hid
from . import mooltipass
