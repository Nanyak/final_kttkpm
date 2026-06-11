from .base import PRODUCTS, CATEGORY_PRODUCTS, ACTION_WEIGHT

from .tiny        import TinyDataset
from .standard    import StandardDataset
from .power_users import PowerUsersDataset
from .noisy       import NoisyDataset
from .categorical import CategoricalDataset

REGISTRY = {
    'tiny':        TinyDataset,
    'standard':    StandardDataset,
    'power_users': PowerUsersDataset,
    'noisy':       NoisyDataset,
    'categorical': CategoricalDataset,
}
