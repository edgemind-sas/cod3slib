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

if study.hooks:
    if study.hooks.before_simu:
        for filename in study.hooks.before_simu:
            filename_path = pathlib.Path(filename)
            if filename_path.is_file():
                logging.info("Executing before simulation file : {filename}")
                exec(open(filename).read())
            else:
                raise ValueError(f"Before simulation hook file {filename} does not exist")
                

study.run_simu()

if study.hooks:
    if study.hooks.after_simu:
        for filename in study.hooks.after_simu:
            filename_path = pathlib.Path(filename)
            if filename_path.is_file():
                logging.info("Executing after simulation file : {filename}")
                exec(open(filename).read())
            else:
                raise ValueError(f"After simulation hook file {filename} does not exist")

sys.exit(0)
