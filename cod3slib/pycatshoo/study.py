import pandas as pd
import typing
import pydantic
import pkg_resources
import yaml
import uuid
#from lxml import etree
import subprocess
import os
import pathlib
import sys
import math
#import colored
from .. import StudyModel, MCSimulationParam
from . import PycVarIndicator

import logging

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: 401

PandasDataFrame = typing.TypeVar('pd.core.dataframe')

SystemModelType = typing.TypeVar('SystemModel')

# Utility functions
# -----------------
class PycMCSimulationParam(MCSimulationParam):
    pass


class PycStudy(StudyModel):

    system_model: SystemModelType = pydantic.Field(
        None, description="System model")
    
    simu_params: PycMCSimulationParam = pydantic.Field(
        None, description="Simulator parametters")

    indicators: typing.List[PycVarIndicator] = pydantic.Field(
        [], description="List of indicators")


    def prepare_simu(self, **kwargs):

        # Set instants
        instants_list = self.simu_params.get_instants_list()

        # Prepare indicators
        for indic in self.indicators:
            indic.instants = instants_list
            indic.bkd = \
                self.system_model.addIndicator(indic.name,
                                               indic.get_expr(),
                                               indic.get_type())
            indic.update_restitution()

        # Simulator configuration
        self.system_model.setTMax(instants_list[-1])
        
        for instant in instants_list:
            self.system_model.addInstant(instant)

        if self.simu_params.seed:
            self.system_model.setRNGSeed(self.simu_params.seed)

        if self.simu_params.nb_runs:
            self.system_model.setNbSeqToSim(self.simu_params.nb_runs)

            
    def run_simu(self, **kwargs):

        self.prepare_simu(**kwargs)

        self.system_model.simulate()

        self.postproc_simu(**kwargs)

    def postproc_simu(self, **kwargs):

        for indic in self.indicators:
            indic.update_values()

