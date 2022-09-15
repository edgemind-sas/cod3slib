import os
import pydantic
import Pycatshoo as pyc
import yaml
import pkg_resources
from .. import IndicatorModel
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401



class PycIndicator(IndicatorModel):

    def get_type(self):
        raise ValueError("Method get_type must be implemented")

    def get_expr(self):
        raise ValueError("Method get_expr must be implemented")

    def update_restitution(self):

        restitution = 0
        for stat in self.stats:
            if stat == "mean":
                restitution |= pyc.TIndicatorType.mean_values
            elif stat == "stddev":
                restitution |= pyc.TIndicatorType.std_dev
            else:
                raise ValueError(f"Stat {stat} not supported for Pycatshoo indicator restitution")

        self.bkd.setRestitutions(restitution)

class PycVarIndicator(PycIndicator):
    component: str = pydantic.Field(..., description="Component name")
    var: str = pydantic.Field(..., description="Variable name")

    def get_type(self):
        return "VAR"

    def get_expr(self):
        return f"{self.component}.{self.var}"

