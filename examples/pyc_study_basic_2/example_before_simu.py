def create_aut_sensitive_method(system_model, comp_name, aut_name, var_name, state_name):
    
    comp = system_model.components[comp_name]
    automaton = comp.get_automaton_by_name(aut_name)
    state = automaton.get_state_by_name(state_name)
    method_name = f"set_{comp_name}_{aut_name}_{var_name}_{state_name}"

    def sensitive_method():
        comp.flow_prod[var_name].setValue(state.bkd.isActive())

    setattr(comp.bkd, method_name, sensitive_method)
    automaton.bkd.addSensitiveMethod(method_name, sensitive_method)


def create_aut_cond_method(system_model,
                           comp_name,
                           aut_name,
                           trans_name,
                           var_name):

    comp = system_model.components[comp_name]
    aut = comp.get_automaton_by_name(aut_name)
    trans = aut.get_transition_by_name(trans_name)
    cond_method_name = f"cond_{comp_name}_{aut_name}_{trans_name}_{var_name}"
    def cond_method():
        return comp.flow_fed[var_name].value()

    trans.bkd.setCondition(cond_method_name, cond_method)


create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="CBTC",
                        aut_name="mr_mouv",
                        var_name="cmd_ouverture_pt",
                        state_name="mr_quai")

create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="CBTC",
                        aut_name="mr_mouv",
                        var_name="cmd_ouverture_pp",
                        state_name="mr_quai")

create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="CBTC",
                        aut_name="mr_mouv",
                        var_name="cmd_fermeture_pt",
                        state_name="mr_départ")

create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="CBTC",
                        aut_name="mr_mouv",
                        var_name="cmd_fermeture_pp",
                        state_name="mr_départ")

create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="MF19",
                        aut_name="cycle_pt",
                        var_name="cmd_départ_mr",
                        state_name="pt_fermées")

create_aut_sensitive_method(system_model=study.system_model,
                        comp_name="FQ",
                        aut_name="cycle_pp",
                        var_name="cmd_départ_mr",
                        state_name="pp_fermées")


create_aut_cond_method(
    system_model=study.system_model,
    comp_name="MF19",
    aut_name="cycle_pt",
    trans_name="fermées_ouvertes",
    var_name="cmd_ouverture_pt")

create_aut_cond_method(
    system_model=study.system_model,
    comp_name="MF19",
    aut_name="cycle_pt",
    trans_name="ouvertes_fermées",
    var_name="cmd_fermeture_pt")


create_aut_cond_method(
    system_model=study.system_model,
    comp_name="FQ",
    aut_name="cycle_pp",
    trans_name="fermées_ouvertes",
    var_name="cmd_ouverture_pp")

create_aut_cond_method(
    system_model=study.system_model,
    comp_name="FQ",
    aut_name="cycle_pp",
    trans_name="ouvertes_fermées",
    var_name="cmd_fermeture_pp")

create_aut_cond_method(
    system_model=study.system_model,
    comp_name="CBTC",
    aut_name="mr_mouv",
    trans_name="mr_départ_absent",
    var_name="cmd_départ_mr")


study.system_model.bkd.loadParameters("study.xml")
