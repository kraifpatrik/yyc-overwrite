import json
import os


class BuildBff:
    """ A wrapper around build.bff file, providing getters to its properties,
    as well as its default path on the disk.

    Args:
        path (str): Path to the build.bff file.
    """

    PATH_DEFAULT = os.path.expandvars("%LOCALAPPDATA%\\GameMakerStudio2\\GMS2TEMP\\build.bff")
    """ The default path to the build.bff file on Windows. """

    def __init__(self, path):
        self._path = path
        with open(path) as f:
            self._data = json.load(f)

    def get_project_name(self):
        """ Returns project's name. """
        return self._data["projectName"]

    def get_project_dir(self):
        """ Returns path to the project's directory. """
        return self._data["projectDir"]

    def get_config(self):
        """ Returns project's configuration (str). """
        return self._data["config"]

    def get_cache_dir(self):
        """ Returns path to the YYC cache directory. """
        return os.path.dirname(self._data["preferences"])

    def get_cpp_dir(self):
        """ Returns path the to directory with YYC C++ files. """
        return os.path.join(
            self.get_cache_dir(),
            self.get_project_name(),
            self.get_config(),
            "Scripts",
            "llvm-win")
