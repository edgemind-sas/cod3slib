import yaml
# ipdb is a debugger (pip install ipdb)
import pkg_resources
import pydantic
import typing
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class StateModel(pydantic.BaseModel):
    name: str = pydantic.Field(..., description="State name")
    bkd: typing.Any = pydantic.Field(None, description="Backend handler")

class OccurrenceDistributionModel(pydantic.BaseModel):
    bkd: typing.Any = pydantic.Field(None, description="Backend handler")

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

        clsname = specs.pop("dist")
        clsname = clsname.capitalize() + "OccDistribution"
        cls = cls_sub_dict.get(clsname)

        if cls is None:
            raise ValueError(
                f"{clsname} is not a subclass of {basecls.__name__}")

        #ipdb.set_trace()
        return cls(**specs)

    
class DelayOccDistribution(OccurrenceDistributionModel):
    time: float = pydantic.Field(0, description="Delay time")

class ExpOccDistribution(OccurrenceDistributionModel):
    rate: float = pydantic.Field(0, description="Rate")

    
class TransitionModel(pydantic.BaseModel):
    name: str = pydantic.Field(..., description="transition name")
    source: str = pydantic.Field(..., description="Source state name")
    target: str = pydantic.Field(..., description="Target state name")
    occ_law: OccurrenceDistributionModel = pydantic.Field(..., description="Occurrence distribution")
    bkd: typing.Any = pydantic.Field(None, description="Backend handler")

    # @pydantic.validator('source', pre=True)
    # def check_source(cls, value, values, **kwargs):
    #     return {"name": value} if isinstance(value, str) \
    #         else value
    
    # @pydantic.validator('target', pre=True)
    # def check_target(cls, value, values, **kwargs):
    #     return {"name": value} if isinstance(value, str) \
    #         else value

    @pydantic.validator('occ_law', pre=True)
    def check_occ_law(cls, value, values, **kwargs):
        value = OccurrenceDistributionModel.from_dict(**value)

        return value

    
class AutomatonModel(pydantic.BaseModel):
    
    name: str = pydantic.Field(..., description="Automaton name")
    states: typing.List[StateModel] = pydantic.Field([], description="State list")
    transitions: typing.List[TransitionModel] = pydantic.Field([], description="Transition list")
    bkd: typing.Any = pydantic.Field(None, description="Backend handler")

    @pydantic.validator('states', pre=True)
    def check_states(cls, value, values, **kwargs):
        states_new = []
        for state in value:
            state_new = {"name": state} if isinstance(state, str) \
                else state
            states_new.append(state_new)
                
        return states_new
    
    @pydantic.root_validator(pre=False)
    def check_consistency(cls, values):
        states_name_list = [st.name for st in values.get("states", [])]
        for trans in values.get("transitions", []):
            st_source = trans.source
            if not(st_source in states_name_list):
                raise ValueError(f"Transition '{trans.name}' source state '{st_source}' not in automaton states list {states_name_list}")
            st_target = trans.target
            if not(st_target in states_name_list):
                raise ValueError(f"Transition '{trans.name}' target state '{st_target}' not in automaton states list {states_name_list}")

        # pw1, pw2 = values.get('password1'), values.get('password2')
        # if pw1 is not None and pw2 is not None and pw1 != pw2:
        #     raise ValueError('passwords do not match')
        return values

    def get_state_by_name(self, state_name):

        for state in self.states:
            if state.name == state_name:
                return state

        raise ValueError(f"State {state_name} is not part of automaton {self.name}")

    def get_transition_by_name(self, name):

        for elt in self.transitions:
            if elt.name == name:
                return elt

        raise ValueError(f"Transition {name} is not part of automaton {self.name}")

    
class ComponentModel(pydantic.BaseModel):

    name: str = pydantic.Field(..., description="Component name")
    automata: typing.List[AutomatonModel] = pydantic.Field([], description="Automata list")
    bkd: typing.Any = pydantic.Field(None, description="Component backend handler")
    
    # def __init__(self, **kwargs):
    #     self.name = kwargs.get("name")
        
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

        #ipdb.set_trace()
        return cls(**specs)

    def get_automaton_by_name(self, name):

        for elt in self.automata:
            if elt.name == name:
                return elt

        raise ValueError(f"Automaton {name} is not part of component {self.name}")


class FlowModel(pydantic.BaseModel):
    name: str = pydantic.Field(..., description="Flow name")
    port: str = pydantic.Field(..., description="Flow port types [in, out, io]")
    var_type: str = pydantic.Field('bool', description="Flow type")
    dafault: typing.Any = pydantic.Field(None, description="Flow default value")
    
class FlowComponentModel(ComponentModel):

    flows: typing.List[FlowModel] = pydantic.Field([], description="Flow list")


    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)

    #     self.flow = {}

    #     self.flow_in = {}
    #     self.flow_available_in = {}

    #     self.flow_out = {}
    #     self.flow_available_out = {}
