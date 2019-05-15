import getpass
import json
import os
import re
from shutil import copyfile

def get_cpp_blocks(file):
    blocks = []
    line_count = 0
    block = None

    with open(file) as f:
        for line in f:
            line_count += 1

            cpp_start = line.find("/*cpp")
            if cpp_start != -1:
                line = line[cpp_start+5:]
                block = {
                    "line": line_count,
                    "code": ""
                }

            if block:
                cpp_end = line.find("*/")
                if cpp_end != -1:
                    line = line[:cpp_end]
                    block["code"] = (block["code"] + line).strip()
                    blocks.append(block)
                    block = None
                else:
                    block["code"] += line

    return blocks

if __name__ == "__main__":
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
        default = "C:\\Users\\{}\\AppData\\Local\\GameMakerStudio2\\GMS2TEMP\\build.bff".format(
            getpass.getuser())
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
        with open(build_bff_dir) as file:
            build = json.load(file)
        print("Loaded build.bff")
    except:
        print("ERROR: Could not load build.bff!")
        exit(1)

    # Get project info
    project_name = build["projectName"]
    project_conf = build["config"]
    project_dir = build["projectDir"]
    cache_dir = os.path.dirname(build["preferences"])
    dest_path = os.path.join(cache_dir, project_name, project_conf, "Scripts")

    print("Project:", project_name)
    print("Config:", project_conf)
    print("Project directory:", project_dir)
    print("Target directory:", dest_path)

    # Check for permission
    if input("Do you really want to overwrite the files? [Y/n] ") == "n":
        print("Canceled")
        exit(1)

    # Inject C++
    for file in os.listdir(dest_path):
        path_dest = os.path.join(dest_path, file)
        path_src = ""
        prefix = file[:11]
        is_script = False

        # Reconstruct path of object event
        if prefix == "gml_Object_":
            split = file.split("_")
            file_name = split[-2:]
            if file_name[0] == "PreCreate":
                continue
            file_name[-1] = file_name[-1][:-4]
            file_name = "_".join(file_name)
            object_name = "_".join(split[:-2][2:])
            path_src = os.path.join(project_dir, "objects",
                                 object_name, file_name)
        # Reconstruct path of script
        elif prefix == "gml_Script_":
            is_script = True
            name = file[11:-8]
            path_src = os.path.join(project_dir, "scripts",
                                 name, "{}.gml".format(name))

        # File is not a script or event
        if not path_src:
            continue

        # Read C++ block from GML
        cpp_str = ""
        try:
            with open(path_src) as f:
                code_gml = f.read()

                cpp_start = code_gml.find("/*cpp")
                if cpp_start != -1:
                    cpp_end = code_gml.find("*/", cpp_start)
                    if cpp_end != -1:
                        cpp_str = code_gml[cpp_start+5:cpp_end].strip()
        except:
            continue

        # No C++ block found
        if not cpp_str:
            print("Skipping", path_dest, "(no C++ blocks found)")
            continue

        # Overwrite C++
        print("Overwriting", path_dest)

        with open(path_dest) as f:
            code_cpp = f.read()

            func_start = code_cpp.find("{}{}".format("YYRValue &" if is_script else "void ", file[:-8]))
            func_start = code_cpp.find("{", func_start)
            func_end = code_cpp.rfind("}")

            prefix = "\n"
            suffix = "\n"

            if is_script:
                prefix = "\n_result = 0;\n"
                suffix = "\nreturn _result;\n"

            new_code = code_cpp[:func_start+1] + prefix + cpp_str + suffix + code_cpp[func_end:]

        with open(path_dest, "w") as f:
            f.write(new_code)

    print("Finished")
