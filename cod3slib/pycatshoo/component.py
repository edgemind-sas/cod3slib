import yaml
import Pycatshoo as pyc
# ipdb is a debugger (pip install ipdb)
import pydantic
import typing
from .. import FlowComponentModel
from .. import DelayOccDistribution, ExpOccDistribution
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


class PycFlowComponent(FlowComponentModel):

 #   flow_in_intra: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow input internal")
    flow_in: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow input")
#    flow_available_in: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow available input")

    flow_prod: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow production")
    flow_fed: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Component flow fed")
    flow_available_fed: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow available fed")

#    flow_out_intra: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow fed internal")
    flow_out: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow output")
    flow_available_out: typing.Dict[str, typing.Any] = pydantic.Field({}, description="Flow available out")

    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)

        self.bkd = pyc.CComponent(self.name)

        self.set_flows()

        self.set_automata()


    def report_status(self):
        sys = self.bkd.system()
        comp_status = []
        comp_status.append(f"{self.name} at t={sys.currentTime()}")

        for flow_name, flow in self.flow_fed.items():
            comp_status.append(f"Flow {flow_name} fed = {flow.value()}")

        comp_status_str = "\n".join(comp_status)
        return comp_status_str

        
    def set_flows(self, flows_list=[]):

        for flow_specs in self.flows:

            flow_name = flow_specs.name
            
            self.add_flow_fed(**flow_specs.dict())

            port = flow_specs.port
            
            getattr(self, f"add_flow_{port}")(**flow_specs.dict())
            getattr(self, f"add_mb_{port}")(**flow_specs.dict())
            getattr(self, f"update_sensitive_methods_{port}")(flow_name)
            
    def get_pyc_type(self, var_type):
        if var_type == 'bool':
            return (bool, pyc.TVarType.t_bool)
        elif var_type == 'int':
            return (int, pyc.TVarType.t_integer)
        elif var_type == 'float':
            return (float, pyc.TVarType.t_double)
        else:
            raise ValueError(
                f"Type {var_type} not supported by PyCATSHOO")

    def add_flow_fed(self, name, var_type='bool',
                 default=False, **kwargs):

        py_type, pyc_type = self.get_pyc_type(var_type)

        if default is None:
            default = py_type()

        # self.flow_fed_intra[name] = \
        #     self.bkd.addVariable(f"{name}_fed_intra", pyc_type, py_type(default))

        self.flow_fed[name] = \
            self.bkd.addVariable(f"{name}_fed", pyc_type, py_type(default))

        self.flow_available_fed[name] = \
            self.bkd.addVariable(f"{name}_available_fed",
                             pyc.TVarType.t_bool, True)

        
    def add_flow_out(self, name, var_type='bool', **kwargs):

        py_type, pyc_type = self.get_pyc_type(var_type)
        
        self.flow_prod[name] = \
            self.bkd.addVariable(f"{name}_prod",
                             pyc_type, py_type())

        self.flow_out[name] = \
            self.bkd.addVariable(f"{name}_out",
                             pyc_type, py_type())

        self.flow_available_out[name] = \
            self.bkd.addVariable(f"{name}_available_out",
                             pyc.TVarType.t_bool, True)


    def add_flow_in(self, name, **kwargs):

        self.flow_in[name] = \
            self.bkd.addReference(f"{name}_in")
        

    def add_flow_io(self, name, **kwargs):
        py_type, pyc_type = self.get_pyc_type(var_type)

        self.flow_in[name] = \
            self.bkd.addVariable(f"{name}_in",
                                 pyc_type, py_type())

        self.flow_out[name] = \
            self.bkd.addVariable(f"{name}_out",
                             pyc_type, py_type())

        self.flow_available_out[name] = \
            self.bkd.addVariable(f"{name}_available_out",
                             pyc.TVarType.t_bool, True)


        
    def add_mb_out(self, name, var_type='bool', **kwargs):

        self.bkd.addMessageBox(f"{name}_out")
        self.bkd.addMessageBoxExport(f"{name}_out",
                                 self.flow_out[name], name)

    def add_mb_in(self, name, **kwargs):

        self.bkd.addMessageBox(f"{name}_in")
        self.bkd.addMessageBoxImport(f"{name}_in",
                                 self.flow_in[name], name)

    def add_mb_io(self, name, **kwargs):
        self.add_mb_in(name, **kwargs)
        self.add_mb_out(name, **kwargs)

        
    def create_sensitive_set_flow_fed_in(self, flow_name):

        def sensitive_set_flow_template():
            # print(self.report_status())
            # ipdb.set_trace()
            self.flow_fed[flow_name].setValue(
                self.flow_in[flow_name].andValue(False) and \
                self.flow_available_fed[flow_name].value())

        return sensitive_set_flow_template

    def create_sensitive_set_flow_fed_out(self, flow_name):

        def sensitive_set_flow_template():
            
            self.flow_fed[flow_name].setValue(
                self.flow_prod[flow_name].value() and \
                self.flow_available_fed[flow_name].value())

        return sensitive_set_flow_template


    def create_sensitive_set_flow_out(self, flow_name):

        def sensitive_set_flow_template():
            self.flow_out[flow_name].setValue(
                self.flow_fed[flow_name].value() and
                self.flow_available_out[flow_name].value())

        return sensitive_set_flow_template


    def update_sensitive_methods_in(self, flow_name):
        sens_meth_flow_fed = self.create_sensitive_set_flow_fed_in(flow_name)
        sens_meth_flow_fed_name = f"set_{flow_name}_fed"
        self.flow_in[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)

        self.flow_available_fed[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)
        
        self.bkd.addStartMethod(sens_meth_flow_fed_name, sens_meth_flow_fed)

        
    def update_sensitive_methods_out(self, flow_name):
        sens_meth_flow_fed = self.create_sensitive_set_flow_fed_out(flow_name)
        sens_meth_flow_fed_name = f"set_{flow_name}_fed"
        self.flow_prod[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)

        self.flow_available_fed[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)

        self.bkd.addStartMethod(sens_meth_flow_fed_name, sens_meth_flow_fed)

        sens_meth_flow_out = self.create_sensitive_set_flow_out(flow_name)
        sens_meth_flow_out_name = f"set_{flow_name}_out"

        self.flow_fed[flow_name].addSensitiveMethod(
            sens_meth_flow_out_name, sens_meth_flow_out)
        self.flow_available_out[flow_name].addSensitiveMethod(
            sens_meth_flow_out_name, sens_meth_flow_out)

        
    def update_sensitive_methods_io(self, flow_name):
        sens_meth_flow_fed = self.create_sensitive_set_flow_fed_in(flow_name)
        sens_meth_flow_fed_name = f"set_{flow_name}_fed"
        self.flow_in[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)

        self.flow_available_fed[flow_name].addSensitiveMethod(
            sens_meth_flow_fed_name, sens_meth_flow_fed)
        
        self.bkd.addStartMethod(sens_meth_flow_fed_name, sens_meth_flow_fed)

        sens_meth_flow_out = self.create_sensitive_set_flow_out(flow_name)
        sens_meth_flow_out_name = f"set_{flow_name}_out"

        self.flow_fed[flow_name].addSensitiveMethod(
            sens_meth_flow_out_name, sens_meth_flow_out)
        self.flow_available_out[flow_name].addSensitiveMethod(
            sens_meth_flow_out_name, sens_meth_flow_out)

    def get_pyc_occ_law(self, occ_law):

        if isinstance(occ_law, DelayOccDistribution):
            return pyc.IDistLaw.newLaw(
                self.bkd, pyc.TLawType.defer, occ_law.time)
        elif isinstance(occ_law, ExpOccDistribution):
            return pyc.IDistLaw.newLaw(
                self.bkd, pyc.TLawType.expo, occ_law.rate)
        else:
            raise ValueError(f"Class {type(occ_law)} is not supported by Pycatshoo")
        
    def set_automata(self, flows_list=[]):

        for automaton in self.automata:

            # Add states
            automaton.bkd = self.bkd.addAutomaton(automaton.name)
            for state_id, state in enumerate(automaton.states):
                state.bkd = automaton.bkd.addState(state.name,
                                                   state_id)

            automaton.bkd.setInitState(automaton.states[0].bkd)


            # Add transitions
            for trans in automaton.transitions:
                state_source = automaton.get_state_by_name(trans.source)
                trans.bkd = \
                    state_source.bkd.addTransition(trans.name)

                state_target = automaton.get_state_by_name(trans.target)
                trans.bkd.addTarget(state_target.bkd)
                trans.bkd.setDistLaw(self.get_pyc_occ_law(trans.occ_law))
                
