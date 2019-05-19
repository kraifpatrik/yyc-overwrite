import getpass
import json
import os
import re
from shutil import copyfile

REGEX_STACKTRACE_LINE = r"YY_STACKTRACE_LINE\((\d+)\);\n?"

NATIVE_TYPES = {
    "bool": "bool",
    "char": "char",
    "int": "int",
    "longlong": "long long",
    "float": "float",
    "double": "double",
}


def remove_stacktrace_lines(string):
    return re.sub(REGEX_STACKTRACE_LINE, "", string)


def get_blocks(string, block_start, block_end):
    blocks = []
    line_count = 0
    block = None

    for line in string.splitlines(1):
        line_count += 1

        idx_start = line.find(block_start)
        if idx_start != -1:
            line = line[idx_start+len(block_start):]
            block = {
                "line": line_count,
                "code": ""
            }

        if block:
            idx_end = line.find(block_end)
            if idx_end != -1:
                line = line[:idx_end]
                block["code"] = (block["code"] + line).strip()
                blocks.append(block)
                block = None
            else:
                block["code"] += line

    return blocks


def get_native_types(string):
    types = []

    rgx = r"((?:(?:static|const)\s+)*)(u?)({})_t\s+(\w+)\s*=".format("|".join(NATIVE_TYPES.keys()))

    for m in re.finditer(rgx, string):
        g1 = m.group(1)
        types.append({
            "static": "static" in g1,
            "const": "const" in g1,
            "unsigned": "u" in m.group(2),
            "type": NATIVE_TYPES[m.group(3)],
            "name": m.group(4),
        })

    return types


def inject_native_types(types, string):
    for t in types:
        name = t["name"]
        static = t["static"]
        const = t["const"]
        unsigned = t["unsigned"]
        val = ""

        if static or const:
            for m in re.finditer(r"local_{}=([^;])+;\n*".format(name), string):
                val = " = {}".format(m.group(1))
                span = m.span()
                string = string[:span[0]] + string[span[1]:]

        original = "YYRValue local_{};".format(name)
        new = "{static}{const}{unsigned}{type} local_{name}{val};".format(
            static="static " if static else "",
            const="const " if const else "",
            unsigned="unsigned " if unsigned else "",
            type=t["type"],
            name=name,
            val=val)
        string = string.replace(original, new)
    return string


def reconstruct_gml_path(cpp_path):
    path_src = ""
    prefix = cpp_path[:11]
    is_script = False

    # Reconstruct path of object event
    if prefix == "gml_Object_":
        split = cpp_path.split("_")
        file_name = split[-2:]
        if file_name[0] != "PreCreate":
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

    return path_src, is_script


def inject_blocks(string, blocks):
    """ Injects blocks into the string, using YY_STACKTRACE_LINE calls to
    determine position. """

    # Get indices
    lut = {}
    for m in re.finditer(REGEX_STACKTRACE_LINE, string):
        line = int(m.group(1))
        start = m.start(0)
        if not line in lut or lut[line] > start:
            lut[line] = start

    if not lut:
        raise Exception("No YY_STACKTRACE_LINE found")

    keys = sorted(lut.keys(), reverse=True)

    # Reconstruct lines
    code = {}
    end = len(string)
    for k in keys:
        start = lut[k]
        code[k] = string[start:end]
        end = start
    code[keys[-1]-1] = string[0:end]

    keys = sorted(code.keys())

    def _get_line_number(block):
        line = block["line"]
        idx = None
        for r in range(1, len(keys)):
            if keys[r] > line:
                idx = keys[r-1]
                break
        return idx

    # Inject blocks
    for b in blocks:
        l = _get_line_number(b)
        if l:
            code[l] += b["code"] + "\n"
        else:
            k = keys[-1]
            last = code[k]
            idx = last.rfind("return _result")
            if idx != -1:
                last = last[:idx] + b["code"] + "\n" + last[idx:]
            else:
                last += b["code"]
            code[k] = last

    # Join back and return
    result = ""
    for k in keys:
        result += code[k]

    return result


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
    if input("Do you really want to modify the files? [Y/n] ") == "n":
        print("Canceled")
        exit(1)

    # Inject C++
    for file in os.listdir(dest_path):
        path_dest = os.path.join(dest_path, file)
        path_src, is_script = reconstruct_gml_path(file)

        # File is not a script or event
        if not path_src:
            continue

        # Read C++ blocks from GML
        cpp_blocks = []
        cpp_types = []
        try:
            with open(path_src) as f:
                fcontent = f.read()
                cpp_blocks = get_blocks(fcontent, "/*cpp", "*/")
                cpp_types = get_native_types(fcontent)
        except:
            continue

        # No C++ block found
        if not cpp_blocks and not cpp_types:
            print("Skipping", path_dest, "(no C++ blocks found)")
            continue

        # Overwrite C++
        print("Processing", path_dest)

        with open(path_dest) as f:
            func_name = file[:-8]
            signature = "{}{}".format(
                "YYRValue& " if is_script else "void ", func_name)
            code_cpp = f.read()
            func_start = code_cpp.find(signature)

            if func_start == -1:
                print("Function {} not found, skipping!".format(func_name))
                continue

            func_start = code_cpp.find("{", func_start + len(signature))
            func_end = code_cpp.rfind("}")

            body = code_cpp[func_start+1:func_end]
            body_new = body

            prefix = ""
            suffix = ""

            if cpp_blocks:
                prefix = "\n"
                suffix = "\n"

                block_first = cpp_blocks[0]
                block_first_code = block_first["code"]
                overwrite_prefix = "-overwrite"
                overwrite = block_first_code.startswith(overwrite_prefix)

                if overwrite:
                    block_first["code"] = block_first_code[len(
                        overwrite_prefix):].lstrip()
                    if is_script:
                        prefix = "\nYY_STACKTRACE_FUNC_ENTRY(\"{}\", 0);\n_result = 0;\n".format(
                            func_name)
                        suffix = "\nreturn _result;\n"
                    body_new = "\n".join(
                        list(map(lambda b: b["code"], cpp_blocks)))
                else:
                    try:
                        body_new = inject_blocks(body, cpp_blocks)
                    except Exception as e:
                        print(e)
                        continue

            body_new = inject_native_types(cpp_types, body_new)
            body_new = remove_stacktrace_lines(body_new)

            new_code = code_cpp[:func_start+1] + prefix + \
                body_new + suffix + code_cpp[func_end:]

        with open(path_dest, "w") as f:
            f.write(new_code)

    print("Finished")
