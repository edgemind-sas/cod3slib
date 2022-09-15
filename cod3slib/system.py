import os
import yaml
import pkg_resources
import pydantic
import typing
from . import ComponentModel

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class Connection(pydantic.BaseModel):
    origin_comp: str = pydantic.Field(..., description="Origin component")
    origin_iface: str = pydantic.Field(..., description="Origin interface")
    target_comp: str = pydantic.Field(..., description="Target component")
    target_iface: str = pydantic.Field(..., description="Target interface")
    bkd: typing.Any = pydantic.Field(None, description="Connection backend handler")

class SystemModel:

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")

        self.components = kwargs.get("components", {})

        self.connections = [Connection(**connection)
                            for connection in kwargs.get("connections", [])]

        for comp_name, comp_specs in self.components.items():
            comp_specs["bkd"] = \
                ComponentModel.from_dict(name=comp_name,
                                         **comp_specs)
        
        self.update_connection_bkd()

    @classmethod
    def get_subclasses(cls, recursive=True):
        """ Enumerates all subclasses of a given class.

        # Arguments
        cls: class. The class to enumerate subclasses for.
        recursive: bool (default: True). If True, recursively finds all sub-classes.

        # Return value
        A list of subclasses of `cls`.
        """
        sub = cls.__subclasses__()
        if recursive:
            for cls in sub:
                sub.extend(cls.get_subclasses(recursive))
        return sub

    @classmethod
    def from_dict(basecls, **specs):

        cls_sub_dict = {
            cls.__name__: cls for cls in basecls.get_subclasses()}

        clsname = specs.pop("cls")
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {basecls.__name__}")

        return cls(**specs)
    
    @classmethod
    def from_yaml(cls, filename):

        with open(filename) as file:
            specs = yaml.load(file, Loader=yaml.FullLoader)

        return cls.from_dict(**specs)

    def update_connection_bkd(self):
        pass
