import os
import Pycatshoo as pyc
import yaml
import pkg_resources
from .. import SystemModel
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401



class PycSystem(SystemModel):

    def __init__(self, **kwargs):

        # We need to initialize Pycatshoo system before all !
        pycsys = pyc.CSystem(kwargs.get("name"))
        super().__init__(**kwargs)
        self.bkd = pycsys
        #SystemModel.__init__(self, **kwargs)

        self.update_connection_bkd()


    def update_connection_bkd(self):

        for connection in self.connections:
            connection.bkd = \
                self.bkd.connect(connection.origin_comp,
                                 connection.origin_iface,
                                 connection.target_comp,
                                 connection.target_iface)


