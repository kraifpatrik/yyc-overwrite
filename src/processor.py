import os
import re

REGEX_STACKTRACE_LINE = r"YY_STACKTRACE_LINE\((\d+)\);\n?"

# var varName /* :type */
REGEX_VAR = r"var\s+([_\w]+)\s*/\*\s*:\s*(.+)\s*\*/"

MACRO_THREAD = "YYC_THREAD"


class Processor(object):
    @staticmethod
    def remove_stacktrace_lines(string):
        return re.sub(REGEX_STACKTRACE_LINE, "", string)

    @staticmethod
    def inject_types(cpp_path, gml_path):
        with open(gml_path, "r") as f:
            gml_content = f.read()

        with open(cpp_path, "r") as f:
            cpp_content = f.read()

        matches = re.findall(REGEX_VAR, gml_content)

        if matches:
            for m in matches:
                name = m[0]
                type_ = m[1].strip()

                # Replace type
                cpp_content = cpp_content.replace(
                    "YYRValue local_{}".format(name),
                    "{} local_{}".format(type_, name))

                # Replace var.asReal() with var
                cpp_content = re.sub(
                    r"local_{}\.asReal\(\)".format(name),
                    "local_{}".format(name),
                    cpp_content)

        cpp_content = Processor.remove_stacktrace_lines(cpp_content)

        with open(cpp_path, "w") as f:
            f.write(cpp_content)

    @staticmethod
    def handle_threading(cpp_path, gml_path):
        run_in_thread = False

        with open(gml_path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if line.strip()[:len(MACRO_THREAD)] == MACRO_THREAD:
                    run_in_thread = True
                    break

        if not run_in_thread:
            return

        with open(cpp_path, "r") as f:
            cpp_content = f.read()

        if cpp_content.find("threading.h") != -1:
            return

        name = os.path.basename(cpp_path)[:-8]
        thread_funcname = "{}_thread".format(name)
        signature = "DWORD WINAPI {}(LPVOID lpParam)".format(thread_funcname)

        idx = cpp_content.find(name)
        if idx == -1:
            return

        start = cpp_content.find("{", idx) + 1
        end = cpp_content.rfind("}")

        body_old = cpp_content[start:end]

        thread_body = body_old.replace(
            "return _result;", "FREE_ARGS();\nreturn _result;")

        body_new = (
            "\n"
            "ThreadArgs* threadArgs = new ThreadArgs(pSelf, pOther, _count, _args);\n"
            "HANDLE thread = CreateThread(NULL, 0, {}, threadArgs, 0, NULL);\n"
            "_result = 0;\n"
            "return _result;\n"
        ).format(thread_funcname)

        func = (
            "\n"
            "{}\n"
            "{{\n"
            "UNPACK_ARGS(lpParam);\n"
            "{}"
            "}}\n"
        ).format(signature, thread_body)

        cpp_content = cpp_content[:start] + body_new + cpp_content[end:]
        cpp_content = "#include \"threading.h\"\n" + \
            signature + ";\n" + cpp_content + func

        with open(cpp_path, "w") as f:
            f.write(cpp_content)
