from .gaussian import GaussianInp as _g
from .molpro import MolProInp as _m
from .qchem import QChemInp as _qc
from .qmoutp import PKARef
from .gaussian_ import mass_read

qm_packages = dict(
    gaussian = _g,
    molpro   = _m,
    qchem    = _qc
    )