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

import logging

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb  # noqa: 401

PandasDataFrame = typing.TypeVar('pd.core.dataframe')

# Utility functions
# -----------------
class IndicatorValue(pydantic.BaseModel):
    time: float = pydantic.Field(..., description="Instant")
    mean: float = pydantic.Field(None, description="Mean")
    stddev: float = pydantic.Field(None, description="Standard deviation")
    

class IndicatorModel(pydantic.BaseModel):
    id: str = pydantic.Field(None, description="Indicator unique id")
    name: str = pydantic.Field(None, description="Indicator short name")
    description: str = pydantic.Field(
        None, description="Indicator description")
    unit: str = pydantic.Field(None, description="Indicator unit")
    stats: list = pydantic.Field([], description="Stats to be computed")
    values: typing.List[IndicatorValue] = pydantic.Field(
        [], description="Indicator estimates")
    metadata: dict = pydantic.Field(
        {}, description="Dictionary of metadata")
    bkd: typing.Any = pydantic.Field(None, description="Indicator backend handler")



    @pydantic.root_validator()
    def cls_validator(cls, obj):
        if obj.get('id') is None:
            obj['id'] = str(uuid.uuid4())

        if obj.get('name') is None:
            obj['name'] = obj['id']

        if obj.get('description') is None:
            obj['description'] = obj['name']

        return obj
