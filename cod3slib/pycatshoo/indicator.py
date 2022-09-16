import os
import pydantic
import Pycatshoo as pyc
import uuid
import yaml
import pandas as pd
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

    def to_pyc_stats(self, stat_name):

        if stat_name == "mean":
            return self.bkd.means
        elif stat_name == "stddev":
            return self.bkd.stdDevs
        else:
            raise ValueError(f"Statistic {stat_name} not supported")
        
            
        
    def update_values(self):

        data_list = []
        for stat in self.stats:
            data_list.append(pd.DataFrame({
                "instant": self.instants,
                "name": self.name,
                "stat": stat,
                "value": self.to_pyc_stats(stat)()}))
            
        self.values = pd.concat(data_list, axis=0, ignore_index=True)
            
class PycVarIndicator(PycIndicator):
    component: str = pydantic.Field(..., description="Component name")
    var: str = pydantic.Field(..., description="Variable name")

    def get_type(self):
        return "VAR"

    def get_expr(self):
        return f"{self.component}.{self.var}"


    @pydantic.root_validator()
    def cls_validator(cls, obj):

        if obj.get('id') is None:
            obj['id'] = str(uuid.uuid4())

        if obj.get('name') is None:
            obj['name'] = f"{obj['component']}.{obj['var']}"

        if obj.get('description') is None:
            obj['description'] = obj['name']

        return obj
