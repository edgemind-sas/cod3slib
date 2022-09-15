import os
import Pycatshoo as pyc
import yaml
import pkg_resources
from .. import SystemModel
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401



class PycSystem(pyc.CSystem, SystemModel):

    def __init__(self, **kwargs):
        pyc.CSystem.__init__(self, kwargs.get("name"))
        SystemModel.__init__(self, **kwargs)


    def update_connection_bkd(self):

        SystemModel.update_connection_bkd(self)

        for connection in self.connections:
            connection.bkd = \
                self.connect(connection.origin_comp,
                             connection.origin_iface,
                             connection.target_comp,
                             connection.target_iface)


