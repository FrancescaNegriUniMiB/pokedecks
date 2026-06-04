import importlib


def import_phase(subpath: str):
    '''Import a numbered phase module, e.g. "5_storing.modules.db".'''
    return importlib.import_module(f"pipeline.{subpath}")
