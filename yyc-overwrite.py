import json
import os
import sys
import time

from termcolor import cprint
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.build_bff import BuildBff
from src.processor import Processor
from src.utils import *


class EventHandler(FileSystemEventHandler):
    def __init__(self, build):
        super(EventHandler, self).__init__()
        self.build = build
        self.modified = {}

    def on_create(self, event):
        self._process(event)

    def on_modified(self, event):
        self._process(event)

    def _process(self, event):
        fpath = event.src_path
        if not fpath in self.modified:
            self.modified[fpath] = False
        if self.modified[fpath]:
            self.modified[fpath] = False
            return
        process_file(fpath, build)
        self.modified[fpath] = True


def process_file(cpp_path, build):
    if not file_is_cpp(cpp_path):
        return
    print(cpp_path, "... ", end="")
    fname = os.path.basename(cpp_path)
    gml_path, is_script = reconstruct_gml_path(build, fname)
    if not gml_path:
        cprint("cannot find GML source, skipping!", "yellow")
        return
    try:
        Processor.inject_types(cpp_path, gml_path)
        if is_script:
            Processor.handle_threading(cpp_path, gml_path)
        cprint("processed", "green")
    except FileNotFoundError:
        pass


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

    try:
        # Check for permission
        if input("Do you really want to modify the files? [Y/n] ") == "n":
            cprint("Canceled", "magenta")
            exit()

        # Copy custom headers
        for f in os.listdir("./cpp"):
            copy_file(os.path.join("./cpp", f), path_cpp)

         # Modify C++ files
        for root, _, files in os.walk(path_cpp):
            for fname in files:
                cpp_path = os.path.join(root, fname)
                process_file(cpp_path, build)

        event_handler = EventHandler(build)
        observer = Observer()
        observer.schedule(event_handler, path_cpp, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    except KeyboardInterrupt:
        # Ignore Ctrl+C
        print()
        pass
