import sys
import os
import pkg_resources
import pathlib
#import cod3slib
import cod3slib.pycatshoo
import Pycatshoo as pyc
import types
import logging

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb


study_filename = os.path.join(".", "study.yaml")

study = cod3slib.StudyModel.from_yaml(study_filename)

study.run_simu()

sys.exit(0)
