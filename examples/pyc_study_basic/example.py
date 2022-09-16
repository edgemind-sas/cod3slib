import os
import pkg_resources
import pathlib
#import cod3slib
import cod3slib.pycatshoo 

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb


# system_filename = os.\
#     path.join(".", "system_specs.yaml")

# system = cod3slib.SystemModel.from_yaml(system_filename)

# system_param_filename = os.\
#     path.join(".", "system_param.xml")
# system_results_filename = os.\
#     path.join(".", "system_results.xml")

# system.dumpParameters(system_param_filename, False)
# system.dumpResults(system_results_filename, False)


study_filename = os.path.join(".", "study.yaml")

study = cod3slib.StudyModel.from_yaml(study_filename)

study.run_simu()

indic_fig = study.indic_px_line()

indic_filename = \
    os.path.join(".", "indic.html")
indic_fig.write_html(indic_filename)
