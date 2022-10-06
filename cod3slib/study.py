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
import plotly.express as px
import sys
import math
#import colored
from . import IndicatorModel
from . import SystemModel
import logging
import pathlib
import importlib

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


class HooksModel(pydantic.BaseModel):

    before_simu: typing.List[str] = pydantic.Field(
        None, description="Filenames to be executed before simulation")

    after_simu: typing.List[str] = pydantic.Field(
        None, description="Filenames to be executed after simulation")


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

    hooks: HooksModel = pydantic.Field(
        None, description="Hooks to be executed")

    working_dir: str = pydantic.Field(
        ".", description="Working dir for relative path")

    results_dir: str = pydantic.Field(
        ".", description="Result dir for storing result")

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
    def from_yaml(cls, yaml_filename, working_dir=".", results_dir=".", **kwrds):

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
                system_spec_path = os.path.join(working_dir, system_specs)
                study_specs["system_model"] = \
                    SystemModel.from_yaml(system_spec_path)
            else:
                study_specs["system_model"] = \
                    SystemModel.from_dict(**system_specs)
        study_specs["working_dir"] = working_dir
        study_specs["results_dir"] = results_dir

        return cls.from_dict(**{**study_specs, **kwrds})

    def get_indicator_from_id(self, id):
        for indic in self.indicators:
            if indic.id == id:
                return indic
        return None

    def run_hook(self, filename):
        absolute_filename = os.path.join(self.working_dir, filename)
        filename_path = pathlib.Path(absolute_filename)
        if filename_path.is_file():
            logging.info(
                "Executing hook file : {absolute_filename}")

            spec = importlib.util.spec_from_file_location(
                "hook", absolute_filename)
            module = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(module)
            module.execute_hook(self)

        else:
            raise ValueError(
                f"Hook file {filename} does not exist")

    def run_before_hook(self):
        if self.hooks.before_simu:
            for filename in self.hooks.before_simu:
                self.run_hook(filename)

    def run_after_hook(self):
        if self.hooks.after_simu:
            for filename in self.hooks.after_simu:
                self.run_hook(filename)

    def run_simu(self, **kwargs):
        pass

    def indic_to_frame(self):

        if len(self.indicators) == 0:
            return None
        else:
            return pd.concat([indic.values for indic in self.indicators],
                             axis=0, ignore_index=True)

    def indic_px_line(self,
                      x="instant",
                      y="value",
                      color="name",
                      markers=True,
                      layout={},
                      **px_conf):

        indic_df = self.indic_to_frame()

        if indic_df is None:
            return None

        idx_stat_sel = indic_df["stat"].isin(["mean"])

        indic_sel_df = indic_df.loc[idx_stat_sel]

        fig = px.line(indic_sel_df,
                      x=x, y=y,
                      color=color,
                      markers=markers,
                      **px_conf)

        fig.update_layout(**layout)

        return fig


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
