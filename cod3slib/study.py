import pandas as pd
import numpy as np
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
from . import IndicatorModel
from . import SystemModel
import logging

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: 401

PandasDataFrame = typing.TypeVar('pd.core.dataframe')

SystemModelType = typing.TypeVar('SystemModel')


class InstantLinearRange(pydantic.BaseModel):
    """Linear Range"""
    start: float = pydantic.Field(..., description="Range start")
    end: float = pydantic.Field(..., description="Range end")
    nvalues: int = pydantic.Field(..., description="Range nb values")

    def get_instants_list(self):
        return list(np.linspace(self.start, self.end, self.nvalues))
    

class MCSimulationParam(pydantic.BaseModel):
    nb_runs: int = pydantic.Field(
        1, description="Number of simulation to run")
    schedule: typing.List[InstantLinearRange | float] = pydantic.Field(
        [], description="Measure instant")
    seed: typing.Any = pydantic.Field(
        None, description="Seed of the simulator")

    def get_instants_list(self):

        instants = []
        for sched in self.schedule:
            if isinstance(sched, InstantLinearRange):
                instants.extend(sched.get_instants_list())
            else:
                instants.append(sched)

        return sorted(instants)


class StudyModel(pydantic.BaseModel):

    name: str = pydantic.Field(
        None, description="Name of the study")

    description: str = pydantic.Field(
        None, description="Study description")

    system_model: SystemModelType = pydantic.Field(
        None, description="System model")
    
    indicators: typing.List[IndicatorModel] = pydantic.Field(
        [], description="List of indicators")

    simu_params: MCSimulationParam = pydantic.Field(
        None, description="Simulator parametters")

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
    def from_yaml(cls, yaml_filename, **kwrds):

        with open(yaml_filename, 'r',
                  encoding="utf-8") as yaml_file:
            try:
                study_specs = yaml.load(yaml_file,
                                        Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                logging.error(exc)
        if study_specs.get("system_model"):
            system_specs = study_specs.get("system_model")
            if isinstance(system_specs, str):
                study_specs["system_model"] = \
                    SystemModel.from_yaml(system_specs)
            else:
                study_specs["system_model"] = \
                    SystemModel.from_dict(**system_specs)
                
        return cls.from_dict(**{**study_specs, **kwrds})

    def get_indicator_from_id(self, id):
        for indic in self.indicators:
            if indic.id == id:
                return indic
        return None

    def run_simu(self, **kwargs):
        pass



# class STOStudyResults(pydantic.BaseModel):

#     meta_data: STOMetaData = pydantic.Field(
#         STOMetaData(), description="Study meta-line")

#     mission: STOMissionResult = pydantic.Field(
#         STOMissionResult(), description="Performance fitting parametters")

#     indicators: typing.Dict[str, STOIndicator] = pydantic.Field(
#         {}, description="Dictionary of simulation indicators")

#     @staticmethod
#     def get_simu_csv_result_sep(raw_lines):
#         if ";" in raw_lines[1]:
#             return ";"
#         else:
#             return "\t"

#     @classmethod
#     def from_result_csv(cls, filename, **kwrds):

#         with open(filename, 'r',
#                   encoding="utf-8") as file:

#             file_lines = file.readlines()

#         simu_csv_sep = cls.get_simu_csv_result_sep(file_lines)

#         obj = cls.from_raw_lines(file_lines, sep=simu_csv_sep)
#         # obj = cls(**{**study_specs, **kwrds})

#         # obj.load_data()
#         # obj.build_models_perf()

#         return obj

#     @classmethod
#     def from_raw_lines(cls, raw_lines, sep="\t"):

#         cls_specs = {}

#         cls_specs["meta_data"] = STOMetaData.from_raw_lines(raw_lines,
#                                                             sep=sep)
#         cls_specs["mission"] = STOMissionResult.from_raw_lines(raw_lines,
#                                                                sep=sep)
#         cls_specs["indicators"] = cls.indicators_from_raw_lines(raw_lines,
#                                                                 sep=sep)

#         # Update indicator block information
#         for indic_id, indic in cls_specs["indicators"].items():
#             if not(cls_specs["meta_data"].main_block is None):
#                 indic.block = cls_specs["meta_data"].main_block

#         obj = cls(**cls_specs)

#         return obj

#     @classmethod
#     def indicators_from_raw_lines(cls, raw_lines, sep="\t"):

#         indics_dict = {}

#         start = len(raw_lines)
#         for i, line in enumerate(raw_lines):
#             line_split = line.split(sep)
#             key = line_split[0].strip()
#             if key == "Indicators":
#                 start = i + 2
#                 break

#         indic_def_lines = raw_lines[start:]
#         for i, line in enumerate(indic_def_lines):

#             line_split = line.split(sep)

#             if len(line_split) <= 1:
#                 start = i + 1
#                 break

#             indic_id = line_split[0].strip()
#             observer = line_split[1].strip()
#             # TODO: TO BE IMPROVED BUT NEED MORE TESTS
#             # value = line_split[2].strip()
#             # measure = line_split[3].strip()
#             indics_dict[indic_id] = \
#                 STOIndicator(
#                     id=indic_id,
#                     name=indic_id,
#                     observer=observer)
#             # value=value,
#             # type="Boolean" if value in ["true", "false"] else "Real",
#             # measure=measure)
#         indic_id = None
#         indic_data_lines = indic_def_lines[start:]
#         for i, line in enumerate(indic_data_lines):

#             line_split = line.strip().split(sep)

#             if line_split[0] == "Indicator":
#                 indic_id = line_split[1]
#                 indics_dict[indic_id].data = []

#             elif is_float(line_split[0]) and not(indic_id is None):

#                 data_cur = dict(
#                     date=float(line_split[0]),
#                     sample_size=int(line_split[1]),
#                     mean=float(line_split[2])
#                     if len(line_split) >= 3 else float("NaN"),
#                     std=float(line_split[3])
#                     if len(line_split) >= 4 else float("NaN")
#                 )
#                 # Compute IC95%
#                 if "std" in data_cur.keys():
#                     data_cur["ic95"] = 1.96*data_cur["std"] / \
#                         math.sqrt(data_cur["sample_size"])

#                 indics_dict[indic_id].data.append(data_cur)

#             # indics_dict[indic_id]
#         for indic_id in indics_dict:
#             indics_dict[indic_id].data = \
#                 pd.DataFrame(indics_dict[indic_id].data)

#         return indics_dict

#     def to_excel(self, filename):

#         writer = pd.ExcelWriter(filename, engine='xlsxwriter')

#         for indic_id, indic in self.indicators.items():
#             indic.data.to_excel(writer,
#                                 sheet_name=indic_id,
#                                 index=False)

#         writer.save()


