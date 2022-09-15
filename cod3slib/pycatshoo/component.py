import yaml
import Pycatshoo as pyc
# ipdb is a debugger (pip install ipdb)
from .. import FlowComponentModel
import pkg_resources
installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: F401


def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
        return func  # returning func means func can still be used normally
    return decorator


class PycFlowComponent(pyc.CComponent, FlowComponentModel):

    def __init__(self, **kwargs):
        FlowComponentModel.__init__(self, **kwargs)
        pyc.CComponent.__init__(self, self.name)

        self.set_flows(kwargs.get("flows", []))

    def set_flows(self, flows_list=[]):

        for flow_specs in flows_list:

            flow_name = flow_specs.get("name")
            
            self.add_flow(**flow_specs)

            port = flow_specs.get("port")
            if port is None:
                raise ValueError(
                    f"Flow port must be specified")
            
            getattr(self, f"add_flow_{port}")(**flow_specs)
            getattr(self, f"add_mb_{port}")(**flow_specs)
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

    def add_flow(self, name, var_type='bool',
                 var_default=False, **kwargs):

        py_type, pyc_type = self.get_pyc_type(var_type)
        self.flow[name] = \
            self.addVariable(f"{name}", pyc_type, py_type(var_default))

    def add_flow_out(self, name, var_type='bool',
                     var_default=False, **kwargs):

        py_type, pyc_type = self.get_pyc_type(var_type)
        self.flow_out[name] = \
            self.addVariable(f"{name}_out",
                             pyc_type, py_type(var_default))

        self.flow_available_out[name] = \
            self.addVariable(f"{name}_available_out",
                             pyc.TVarType.t_bool, True)

    def add_mb_out(self, name, **kwargs):

        self.addMessageBox(f"{name}_out")
        self.addMessageBoxExport(f"{name}_out",
                                 self.flow_out[name], name)

    def add_flow_in(self, name, **kwargs):

        self.flow_in[name] = \
            self.addReference(f"{name}_in")

        self.flow_available_in[name] = \
            self.addVariable(f"{name}_available_in", pyc.TVarType.t_bool, True)

    def add_mb_in(self, name, **kwargs):

        self.addMessageBox(f"{name}_in")
        self.addMessageBoxImport(f"{name}_in",
                                 self.flow_in[name], name)

    def add_flow_io(self, name, **kwargs):
        self.add_flow_in(name, **kwargs)
        self.add_flow_out(name, **kwargs)

    def add_mb_io(self, name, **kwargs):
        self.add_mb_in(name, **kwargs)
        self.add_mb_out(name, **kwargs)


    def create_sensitive_set_flow(self, flow_name):

        def sensitive_set_flow_template():
            self.flow[name].setValue(
                self.flow_in[name].andValue(True) and
                self.flow_available_in[name].value())

        return sensitive_set_flow_template


    def create_sensitive_set_flow_out(self, flow_name):

        def sensitive_set_flow_template():
            self.flow_out[name].setValue(
                self.flow[name].andValue(True) and
                self.flow_available_out[name].value())

        return sensitive_set_flow_template


    def update_sensitive_methods_in(self, flow_name):

        self.flow_in[flow_name].addSensitiveMethod(
            f"set_{flow_name}_flow",
            self.create_sensitive_set_flow(flow_name))

        
    def update_sensitive_methods_out(self, flow_name):
        self.flow[flow_name].addSensitiveMethod(
            f"set_{flow_name}_out",
            self.create_sensitive_set_flow_out(flow_name))

        
    def update_sensitive_methods_io(self, flow_name):
        self.update_sensitive_methods_in(flow_name)
        self.update_sensitive_methods_out(flow_name)
        
class AbstractComponent(pyc.CComponent):

    def __init__(self):
        # Instantiation of an ATM2S List
        self.failure_modes = {}
        # Indique si les flux sont présents à l'instant t
        self.fed_flows = {}
        # Indique si les flux sont disponibles à l'instant t
        self.flows_available = {}

        # Indique si le composant est en defaillance
        self.f_is_occurring = self.addVariable(
            "f_is_occurring", pyc.TVarType.t_bool, False)
        self.f_is_occurring.addSensitiveMethod(
            "set_flows_available", self.set_flows_available)

        self.addStartMethod("init_component_method",
                            self.init_component_method)

    def init_component_method(self):
        # Failures modes init methods for lambda_t and mu_t
        for frun in self.failure_modes.values():
            frun.po_lambda_t.setValue(frun.po_lambda.value())
            frun.po_mu_t.setValue(frun.po_mu.value())

        # Automaton sensitive methods
        for frun in self.failure_modes.values():
            frun.automaton.addSensitiveMethod(
                "set_f_is_occurring", self.set_f_is_occurring)

        # Fed flow sensitive methods
        for fed_flow in self.fed_flows.values():
            fed_flow.addSensitiveMethod(
                "set_flows_available", self.set_flows_available)

        # Condition Flux Is Up sensitive methods
        for flow_available in self.flows_available.values():
            flow_available.addSensitiveMethod(
                "setConditionFluxIsUp", self.setConditionFluxIsUp)

    def set_f_is_occurring(self):
        frun_value = False
        for frun in self.failure_modes.values():
            frun_value = frun_value or frun.stateKO.isActive()

        self.f_is_occurring.setValue(frun_value)

    def set_flows_available(self):
        for key in self.flows_available.keys():
            if key == "expl":
                self.flows_available[key].setValue(self.fed_flows[key] and not(
                    self.f_is_occurring.value()) and self.expl_out_available.andValue())
            else:
                self.flows_available[key].setValue(
                    self.fed_flows[key] and not(self.f_is_occurring.value()))

    def setConditionFluxIsUp(self):
        is_fed_with_flows = True
        for flow in self.flows_available.values():
            if not(flow.value()):
                is_fed_with_flows = False
                break

        for frun in self.failure_modes.values():
            if is_fed_with_flows:
                frun.ev_true_enable.setValue(True)
                frun.ev_false_enable.setValue(True)
            else:
                frun.ev_true_enable.setValue(True)
                frun.ev_false_enable.setValue(False)
