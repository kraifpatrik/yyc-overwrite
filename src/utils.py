import os
import shutil

from termcolor import cprint


def file_is_cpp(file):
    return file[-8:] == ".gml.cpp"


def cpp_is_script(file):
    return file[:11] == "gml_Script_"


def cpp_is_event(file):
    return file[:11] == "gml_Object_"


def cpp_is_room(file):
    return file[:9] == "gml_Room_"


def reconstruct_gml_path(build_bff, cpp_path):
    project_dir = build_bff.get_project_dir()
    path_src = ""
    is_script = False

    # Reconstruct path of object event
    if cpp_is_event(cpp_path):
        split = cpp_path.split("_")
        file_name = split[-2:]
        if file_name[0] != "PreCreate":
            file_name[-1] = file_name[-1][:-4]
            file_name = "_".join(file_name)
            object_name = "_".join(split[:-2][2:])
            path_src = os.path.join(project_dir, "objects",
                                    object_name, file_name)
    # Reconstruct path of script
    elif cpp_is_script(cpp_path):
        is_script = True
        name = os.path.basename(cpp_path)[11:-8]
        path_src = os.path.join(project_dir, "scripts",
                                name, "{}.gml".format(name))

    return path_src, is_script


def copy_file(src, path_cpp):
    dest = os.path.join(path_cpp, os.path.basename(src))
    print("Copying", src, "...", end="")
    try:
        os.remove(dest)
    except:
        pass
    shutil.copyfile(src, dest)
    cprint("done", "green")
