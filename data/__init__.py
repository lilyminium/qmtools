import yaml
import os

from .clusters import *
from .templates import *
from .params import *


PATH = os.path.dirname(__file__)
SCALING_FACTORS = f"{PATH}/scaling_factors.yaml"


with open(SCALING_FACTORS, 'r') as f:
    scaling_factors = yaml.load(f)