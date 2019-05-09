import getpass
import json
import os
from shutil import copyfile

if __name__ == "__main__":
    # Load or create config
    save_conf = False

    try:
        with open("config.json") as f:
            config = json.load(f)
        cpp_dir = config["cpp_dir"]
        build_bff_dir = config["build_bff"]
        print("Loaded config.json")
    except:
        save_conf = True
        config = {}

    if not "cpp_dir" in config or not cpp_dir:
        default = "Cpp"
        cpp_dir = input("Enter name of project subdirectory containing C++ files [{}]:".format(default))
        if not cpp_dir:
            cpp_dir = default
        config["cpp_dir"] = cpp_dir
        save_conf = True

    if not "build_bff" in config or not build_bff_dir:
        default = "C:\\Users\\{}\\AppData\\Local\\GameMakerStudio2\\GMS2TEMP\\build.bff".format(getpass.getuser())
        build_bff_dir = input("Enter path to the build.bff file [{}]: ".format(default))
        if not build_bff_dir:
            build_bff_dir = default
        config["build_bff"] = build_bff_dir
        save_conf = True

    if save_conf:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        print("Saved config")

    # Load build.bff
    try:
        with open(build_bff_dir) as f:
            build = json.load(f)
        print("Loaded build.bff")
    except:
        print("ERROR: Could not load build.bff!")
        exit(1)

    # Get project info
    project_name = build["projectName"]
    project_conf = build["config"]
    project_dir = build["projectDir"]
    cache_dir = os.path.dirname(build["preferences"])
    src_path = os.path.join(project_dir, cpp_dir)
    dest_path = os.path.join(cache_dir, project_name, project_conf, "Scripts")

    print("Project:", project_name)
    print("Config:", project_conf)
    print("Source directory:", src_path)
    print("Target directory:", dest_path)

    # Get files to copy
    try:
        print("Created", cpp_dir, "subdirectory")
        os.mkdir(src_path)
    except:
        pass

    def filter_cpp_files(f):
        ext = os.path.splitext(f)[1][1:]
        return ext in ["cpp", "h"]

    files = os.listdir(src_path)
    files = list(filter(filter_cpp_files, files))
    file_count = len(files)
    print("Found", file_count, "file(s) to copy")

    if files:
        # Check for permission
        if input("Do you really want to copy the files? [Y/n] ") == "n":
            print("Copying canceled")
            exit(1)

        # Copy files
        i = 1
        for f in files:
            fsrc = os.path.join(src_path, f)
            fdest = os.path.join(dest_path, f)
            print("Copying", f, "({}/{})".format(i, file_count))
            copyfile(fsrc, fdest)
            i += 1

    print("Finished")
