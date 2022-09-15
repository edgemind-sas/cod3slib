import yaml
# ipdb is a debugger (pip install ipdb)
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401




class ComponentModel:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")

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


class FlowComponentModel(ComponentModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.flow = {}

        self.flow_in = {}
        self.flow_available_in = {}

        self.flow_out = {}
        self.flow_available_out = {}
