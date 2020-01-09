import json
import os
import sys

from src.build_bff import BuildBff
from src.processor import Processor
from src.utils import *


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Load cache directory from command line (no injection, only cleanup,
        # handy for GMS1.4)
        build = None
        path_cpp = sys.argv[1]
    else:
        # Load or create config
        save_conf = False

        try:
            with open("config.json") as file:
                config = json.load(file)
            build_bff_dir = config["build_bff"]
            print("Loaded config.json")
        except:
            save_conf = True
            config = {}

        if not "build_bff" in config or not build_bff_dir:
            default = BuildBff.PATH_DEFAULT
            build_bff_dir = input(
                "Enter path to the build.bff file [{}]: ".format(default))
            if not build_bff_dir:
                build_bff_dir = default
            config["build_bff"] = build_bff_dir
            save_conf = True

        if save_conf:
            with open("config.json", "w") as file:
                json.dump(config, file, indent=2)
            print("Saved config")

        # Load build.bff
        try:
            build = BuildBff(build_bff_dir)
            print("Loaded build.bff")
        except:
            print("ERROR: Could not load build.bff!")
            exit(1)

        # Project info
        path_cpp = build.get_cpp_dir()
        print("Project:", build.get_project_name())
        print("Config:", build.get_config())
        print("Project directory:", build.get_project_dir())

    print("Target directory:", path_cpp)

    # Check for permission
    if input("Do you really want to modify the files? [Y/n] ") == "n":
        print("Canceled")
        exit()

    # Copy custom headers
    for f in os.listdir("./cpp"):
        copy_file(os.path.join("./cpp", f), path_cpp)

    # Modify C++ files
    try:
        for root, _, files in os.walk(path_cpp):
            for fname in files:
                if not file_is_cpp(fname):
                    continue
                print(fname, "... ", end="")
                cpp_path = os.path.join(root, fname)
                gml_path, is_script = reconstruct_gml_path(build, fname)
                if not gml_path:
                    print("cannot find GML source, skipping!")
                    continue
                try:
                    Processor.inject_types(cpp_path, gml_path)
                    if is_script:
                        Processor.handle_threading(cpp_path, gml_path)
                    print("processed")
                except FileNotFoundError:
                    pass

    except KeyboardInterrupt:
        # Ignore Ctrl+C
        print()
        pass

    print("Finished")
