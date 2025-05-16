import re
import sys
import os
import platform
from printmods import fprint, Fore, Back
import printmods
import math
import psutil

try:
    import cpuinfo

    for key, item in cpuinfo.get_cpu_info().items():
        if key == "brand_raw":
            cpudata = item
except:
    cpudata = "No Module 'py-cpuinfo'"


__version__ = '8a32c0'
__compat__ = '12w5-pre'


from logdata import bytes_to_custom_pairs
errors = True
unknowns = True
os.system('')


print(f"Running on {Fore.CYAN}{platform.system()} {platform.release()} {Fore.YELLOW}{platform.version()}{Fore.RESET} // {Fore.GREEN}{platform.machine()}{Fore.RESET} ({Fore.BLUE}{platform.node()}{Fore.RESET}) // "
      f"\n{cpudata} \n"
      f"RAM: {round((psutil.virtual_memory().total)/1000000)} MB")
print(f"Interpreter Version {__version__}-SP{__compat__}")
if platform.system() == "Windows":
    os.system('')  # Enables ANSI escape codes

import random


try:
    basepath = os.path.dirname(os.path.abspath(sys.argv[0]))
except Exception as e:
    fprint(f"Failed to get the base interpreter path: {e} {Back.RESET}", "FATAL", Fore.BLACK, Back.WHITE)
    _ = input("Press ENTER to exit.")
    sys.exit(1)


rtid = random.randrange(65536)
print(f"RTID: {rtid}")

class ReturnSignal(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


class BaseInterpreter:
    """Abstract base for LogLang mode interpreters."""

    def __init__(self):
        self.filetype = None

    def expand_vars(self, text):
        """Replace !var! with its value, including py: variables."""
        # Matches !array[something]! where "something" may contain param:... or py:...
        text = re.sub(
            r'!(\w+)\[(.+?)\]!',
            lambda m: str(self.get_array_element(
                m.group(1),
                int(self.expand_vars(m.group(2)))  # recursively expand the index
            )),
            text
        )
        text = re.sub(r'!py:(.+?)!', lambda m: str(self.eval_python(m.group(1))), text)
        # Handle parameters
        text = re.sub(r'param:(\w+)', lambda m: str(self.current_params.get(m.group(1), '')), text)
        # Handle py:expr anywhere
        text = re.sub(r'py:([^\s!]+)', lambda m: str(self.eval_python(m.group(1))), text)
        # Handle simple variables
        return re.sub(r'!(\w+)!', lambda m: str(self.vars.get(m.group(1), '')), text)

    def get_array_element(self, name, idx):
        arr = self.vars.get(name)
        if isinstance(arr, list) and 0 <= idx < len(arr):
            return arr[idx]
        return ''

    def eval_python(self, code):
        try:
            return eval(code, {}, self.python_context)
        except Exception:
            try:
                exec(code, {}, self.python_context)
                return None
            except Exception as e:
                if errors:
                    fprint(f"Python error in py: {e}", "ERROR", Fore.RED)
                return None

    def run(self, lines):
        raise NotImplementedError("Must implement run() in subclass")


class LogicInterpreter(BaseInterpreter):
    """Interpreter for LogLang 'logic' mode with return, loop, and dynamic vars support."""

    def __init__(self):
        super().__init__()
        self.vars = {}
        self.current_params = {}
        self.types = {}
        self.linecount = 0
        self.python_context = {
            "MVAR": vars(math),
            "__builtins__": __builtins__,
            "rtid": rtid,
            "linecount": self.linecount,
            "vars": self.vars,
            "sys": sys,
            "os": os,
            "printmods": printmods,
            "util": psutil,
            "chr": chr,
            "ord": ord,
            "self": self,
            "bin": bin,
        }
        self.python_context["linecount"] = self.linecount
        self.python_context["py"] = self.eval_python  # Register py function globally

    def py(self, code):
        return self.eval_python(code)

    def expand_vars(self, text):
        """Replace !var! with its value, including py: variables."""
        # Matches !array[something]! where "something" may contain param:... or py:...
        try:
            text = re.sub(
                r'!(\w+)\[(.+?)\]!',
                lambda m: str(self.get_array_element(
                    m.group(1),
                    int(self.expand_vars(m.group(2)))  # recursively expand the index
                )),
                text
            )
        except Exception as e:
            if errors:
                fprint(f"Algebraic set eval error: {e}", "WARNING", Fore.YELLOW)
        text = re.sub(r'!py:(.+?)!', lambda m: str(self.eval_python(m.group(1))), text)
        # Handle parameters
        text = re.sub(r'param:(\w+)', lambda m: str(self.current_params.get(m.group(1), '')), text)
        # Handle py:expr anywhere
        text = re.sub(r'py:([^\s!]+)', lambda m: str(self.eval_python(m.group(1))), text)
        # Handle simple variables
        return re.sub(r'!(\w+)!', lambda m: str(self.vars.get(m.group(1), '')), text)

    def match_type(self, value, typename):
        rule = self.types.get(typename)
        if not rule:
            return False

        # Preprocess type rule
        rule = rule.strip().lower()

        # Common type checks
        if '0..9' in rule:
            if re.fullmatch(r'\d+', str(value)):
                return True

        if 'float' in rule or '0..9.0..9' in rule:
            if re.fullmatch(r'\d+\.\d+', str(value)):
                return True

        if '*reg' in rule and '\\w+' in rule:
            if re.fullmatch(r'\w+', str(value)):
                return True

        if '*v' in rule and isinstance(value, str) and value in self.vars:
            return True

        if 'any in' in rule:
            # Check if value is in a variable list like !hexbytes!
            match = re.search(r'any in !(\w+)!', rule)
            if match:
                varname = match.group(1)
                data = self.vars.get(varname)
                if isinstance(data, list) and value in data:
                    return True

        if 'matches r[' in rule or 'matches z[' in rule:
            if re.match(r'[rz]\[.*\]\[.*\]', str(value)):
                return True

        if 'matches {"*key", "*value"}' in rule:
            if re.match(r'\{"\w+",\s*"\w+"\}', str(value)):
                return True

        if 'matches (*, *)' in rule:
            if re.match(r'\(.*?,.*?\)', str(value)):
                return True

        if '*' in rule:  # Wildcard match
            return True

        return False

    def run_line(self, line):
        s = line.strip()
        if not s or s.startswith(('comment', 'using ')):
            return

        m = re.match(r'name (.+)', s)
        if m:
            title = m.group(1)
            os.system(f'title {title}')
            return


        # TYPE DEFINITION
        m = re.match(r'^type\s+(\w+)\s*\((matches.+)\)$', s)
        #print(line)
        if m:
            typename, rulestr = m.groups()
            self.types[typename] = rulestr.strip()
            fprint(f"Registered type '{typename}' with rule: {rulestr}", "INFO", Fore.GREEN)
            return

        # Detect and announce mode
        if self.filetype is None and s.startswith('*FILETYPE'):
            _, ft = s.split(maxsplit=1)
            self.filetype = ft.strip()
            fprint(self.filetype, "MODE", Fore.BLUE)
            return

        m = re.match(r'py\((.+)\)', line)
        if m:
            expr = m.group(1)
            self.vars['result'] = self.eval_python(expr)
            return



        if s.startswith('*uVERSION'):
            ft = (s.split(" "))[1]
            print(ft)
            if (ft.split("a"))[0] > (__version__.split("a"))[0]:
                raise RuntimeError(
                    f"{Fore.RED}This file is not supported because it uses a newer version of LogicLang and therefore requires a compatible interpreter.\n"
                    f" Please upgrade the interpreter to the newest version to resolve this error.\n{Fore.YELLOW} Interpreter Version: {Fore.RED}{__version__}{Fore.YELLOW}    File Version: {ft}")

        # Pre-expand parameters and variables in the line
        s = self.expand_vars(s)

        # FOR loops
        m = re.match(r'for (\w+) from (\d+) to (\d+) then (.+)', s)
        if m:
            var, start, end, rest = m.groups()
            for i in range(int(start), int(end) + 1):
                self.vars[var] = i
                self.run_line(rest)
            return
        m = re.match(r'for (\w+) in (\w+) then (.+)', s)
        if m:
            var, lst, rest = m.groups()
            for item in self.vars.get(lst, []):
                self.vars[var] = item
                self.run_line(rest)
            return

        self.types = {}

        # RETURN
        m = re.match(r'return\s+(.+)', s)
        if m:
            expr = m.group(1).strip()
            call = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)$', expr)
            if call:
                fn_name, arg_str = call.groups()
                args = [self.expand_vars(a) for a in arg_str.split()]
                val = self.call_function(fn_name, args)
            else:
                expanded = self.expand_vars(expr)
                try:
                    val = eval(expanded, {}, {**self.vars, **self.python_context})
                except:
                    # If it's not a Python expression, return raw string
                    try:
                        val = expanded
                    except Exception as e:
                        if errors:
                            fprint(f"Error evaluating return: {e}", "ERROR", Fore.RED)

            raise ReturnSignal(val)

        # GENERAL SET: dynamic variable names allowed
        m = re.match(r'general set variable (.+?) to (.+)', s)
        if m:
            var_expr, expr = m.groups()
            var_name = self.expand_vars(var_expr).strip()
            expr = expr.strip()
            if expr.startswith('py:'):
                val = self.eval_python(expr[3:].strip())
            else:
                call = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)$', expr)
                if call:
                    fn_name, arg_str = call.groups()
                    args_list = [self.expand_vars(a) for a in arg_str.split()]
                    val = self.call_function(fn_name, args_list)
                else:
                    val_str = self.expand_vars(expr)
                    try:
                        val = eval(val_str, {}, {**self.vars, **self.python_context})
                    except:
                        val = expr
            # Detect array assignment
            arr_match = re.match(r'(\w+)\[(\d+)\]', var_expr)
            if arr_match:
                name, idx = arr_match.groups()
                idx = int(idx)
                arr = self.vars.get(name)
                if not isinstance(arr, list):
                    arr = []
                while len(arr) <= idx:
                    arr.append(None)
                arr[idx] = val
                self.vars[name] = arr
            else:
                self.vars[var_expr.strip()] = val
            return

        # ALGEBRAIC SET
        m = re.match(r'algebraic set variable (\w+) to (.+)', s)
        if m:
            var, expr = m.groups()
            expr = expr.strip()
            if expr.startswith('py:'):
                val = self.eval_python(expr[3:].strip())
            else:
                call = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)$', expr)
                if call:
                    fn_name, arg_str = call.groups()
                    args_list = [self.expand_vars(a) for a in arg_str.split()]
                    val = self.call_function(fn_name, args_list)
                else:
                    to_eval = self.expand_vars(expr)
                    var, expr = m.groups()
                    try:
                        self.vars[var] = eval(expr, {}, self.vars)
                        return
                    except Exception as e:
                        if errors:
                            fprint(f"evaluating '{expr}': {e}", "ERROR", Fore.RED)
                        return
            try:
                self.vars[var] = val
            except Exception as e:
                if errors:
                    fprint(e, "ERROR", Fore.RED)
            return

        # LOGICAL SET
        m = re.match(r'logical set variable (\w+) to (true|false)', s)
        if m:
            var, val = m.groups()
            self.vars[var] = (val == 'true')
            return

        # LOGICAL COMPARE
        m = re.match(r'logical compare with output (\w+) as the (and|or|not) of (.+)', s)
        if m:
            out, op, args = m.groups()
            parts = args.split()
            vals = [bool(self.vars.get(p, False)) for p in parts]
            res = {'and': all(vals), 'or': any(vals), 'not': not vals[0] if vals else True}[op]
            self.vars[out] = res
            return

        # IF statement
        m = re.match(r'if variable (\w+) is (greater|less|equal) than variable (\w+) then { (.+) }', s)
        if m:
            v1, cond, v2, rest = m.groups()
            a = self.vars.get(v1, 0)
            b = self.vars.get(v2, 0)
            cmp_map = {'greater': a > b, 'less': a < b, 'equal': a == b}
            if cmp_map.get(cond):
                self.run_line(rest)
            return

        # PRINT TEXT
        m = re.match(r'print text "(.+)"', s)
        if m:
            txt = m.group(1)
            print() if txt.strip() == '.' else print(txt)
            return

        # PRINT VARIABLE
        m = re.match(r'print variable (\w+)', s)
        if m:
            print(self.vars.get(m.group(1), ''))
            return

        # INPUTS
        #m = re.match(r'input (\w+) "(.+)"', s)
        #if m:
        #    var_expr, instring = m.groups()
        #    val = input(instring)
        #    self.vars[var_expr.strip()] = val
        #    return

        # Fallback unknown
        if unknowns:
            fprint(f"{s} (NO REGEX MATCH)", "UNKNOWN", Fore.YELLOW)

    def call_function(self, name, args):
        # Attempt to resolve a function in the Python context

        try:
            func = eval(name, {}, self.python_context)
            if callable(func):
                return func(*args)
            else:
                if errors:
                    fprint(f"'{name}' is not callable", "ERROR", Fore.RED)
                raise ValueError(f"'{name}' is not callable")
        except Exception as e:
            if errors:
                fprint(f"Function call error: {e}", "ERROR", Fore.RED)
            return None

    def run(self, lines):
        self.linecount = 0
        for line in lines:
            self.linecount += 1
            self.python_context["linecount"] = self.linecount
            self.linecount = self.python_context["linecount"]
            try:
                self.run_line(line)
            except ReturnSignal as rs:
                return rs.value


class CompoundInterpreter(BaseInterpreter):
    def __init__(self):
        super().__init__()
        self.definitions = {}
        self.types = {}
        self.classes = {}
        self.functions = {}
        self.logic_interp = LogicInterpreter()
        self.logic_interp.call_function = self.execute_function
        self.linecount = 0
        self.do_dump = True
        self.python_context = self.logic_interp.python_context

    def execute_function(self, name, args):
        if not name.startswith("py"):
            if '.' in name:
                cls, method = name.split('.', 1)
                fn = self.classes.get(cls, {}).get(method)
            else:
                fn = self.functions.get(name)
            if not fn:
                if errors:
                    fprint(f"function '{name}' not found", "ERROR", Fore.RED)
                return None
            if len(args) != len(fn['params']):
                if errors:
                    fprint(f"'{name}' expects {len(fn['params'])} args, got {len(args)}", "ERROR", Fore.RED)
                return None
            old_vars = self.logic_interp.vars.copy()
            old_params = self.logic_interp.current_params.copy()
            self.logic_interp.current_params = dict(zip(fn['params'], args))
            for p, v in self.logic_interp.current_params.items():
                self.logic_interp.vars[p] = int(v) if v.isdigit() else v
            try:
                for line in fn['body']:
                    s = line.strip()
                    m = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)', s)
                    if m:
                        nm, ag = m.groups()
                        args_list = [self.logic_interp.expand_vars(a) for a in ag.split()]
                        self.execute_function(nm, args_list)
                    else:
                        self.logic_interp.run_line(s)
            except ReturnSignal as rs:
                ret = rs.value
            else:
                ret = None
            self.logic_interp.vars = old_vars
            self.logic_interp.current_params = old_params
            return ret

    def run(self, lines):
        global errors, unknowns
        current_fn = None
        current_cls = None
        linecount = 0
        for raw in lines:
            linecount += 1
            self.python_context["linecount"] = linecount
            linecount = self.python_context["linecount"]
            currentline = linecount
            line = raw.strip()
            if not line or line.startswith('comment'):
                continue
            if line.startswith('*CONFIG'):
                parts = line.split()
                if len(parts) > 1:
                    if parts[1].lower() == 'd0':
                        self.do_dump = False
                    elif parts[1].lower() == 'd1':
                        self.do_dump = True
                continue
            if line.startswith('*FILETYPE'):
                _, self.filetype = line.split(maxsplit=1)
                self.filetype = self.filetype.strip()
                continue
            if line.startswith('*uVERSION'):
                ft = (line.split(" "))[1]
                print(f"file-declared version {ft}")
                update = (ft.split("a"))[1]
                version2 = (__version__.split("a"))[1]
                if (ft.split("a"))[0] > (__version__.split("a"))[0]:
                    raise RuntimeError(
                        f"\n{Fore.RED}This file is not supported because it uses a newer version of \nLogicLang and therefore requires a compatible interpreter.\n"
                        f"Please upgrade the interpreter to the newest version to resolve this error.\n{Fore.WHITE}Details:\n{Fore.YELLOW}Interpreter Version: {Fore.RED}{__version__}{Fore.YELLOW}    File Version: {ft}")
                if (update.split("c"))[0] > (version2.split("c"))[0]:
                    fprint(
                        f"This file might have errors due to it using a later minor update.\n"
                        f"You do not have to update your interpreter, but there might be significant code function issues.\n"
                        , "WARNING", Fore.YELLOW)
                    keythrough = input("Continue? (Y/N)")
                    if keythrough.lower() == "y":
                        continue
                    else:
                        sys.exit(-255)

            if line.startswith('using resource'):
                continue
            m = re.match(r'int\s+(\w+)\s+def.*?/([^/]+)/', line)
            if m:
                self.definitions[m.group(1)] = m.group(2).split()
                continue
            # TYPE DEFINITION
            m = re.match(r'^type\s+(\w+)\s*\((matches.+)\)$', line)
            # print(line)
            if m:
                typename, rulestr = m.groups()
                self.types[typename] = rulestr.strip()
                fprint(f"Registered type '{typename}' with rule: {rulestr}", "INFO", Fore.GREEN)
                continue

            # DISPLAY RULE
            m = re.match(r'displayrule\s+(\w+)\s+(\w+)', line)
            if m:
                rule, conditions = m.groups()
                if rule == "errors":
                    if conditions == "disable":
                        errors = False
                    else:
                        errors = True
                elif rule == "unknowns":
                    if conditions == "disable":
                        unknowns = False
                    else:
                        unknowns = True
                else:
                    continue
                continue

            m = re.match(r'input (\w+) "(.+)"', line)
            if m:
                var_expr, instring = m.groups()
                val = input(instring)
                self.logic_interp.vars[var_expr.strip()] = val
                continue

            m = re.match(r'fclass\s+(\w+)\s*{', line)
            if m:
                current_cls = m.group(1)
                self.classes[current_cls] = {}
                continue
            m = re.match(r'function\s+(\w+)(?:\((.*?)\))?\s*{', line)
            if m:
                fn, params = m.groups()
                target = self.classes[current_cls] if current_cls else self.functions
                target[fn] = {'params': params.split() if params else [], 'body': []}
                current_fn = target[fn]
                continue
            if line == '}' and current_fn:
                current_fn = None
                continue
            if line == '}' and current_cls and not current_fn:
                current_cls = None
                continue
            if current_fn:
                current_fn['body'].append(line)
        # Summary dump
        if self.do_dump:
            fprint(self.filetype, "MODE", Fore.BLUE)
            print(f"\nDefined {len(self.definitions)} data lists:")
            for k, v in self.definitions.items():
                print(f"  • {k} ({len(v)} entries)")
            print(f"\nDefined {len(self.types)} types:")
            for t, vals in self.types.items():
                print(f"  • {t} -> {len(vals)} values")
            print(f"\nGlobal functions:")
            for fn, info in self.functions.items():
                print(f"  • {fn}({', '.join(info['params'])}) — {len(info['body'])} lines")
            print(f"\nClasses:")
            for cls, methods in self.classes.items():
                print(f"  • {cls} with methods: {', '.join(methods.keys())}")
        print("\n[Executing logic and calls]")
        self.linecount = 0
        for raw in lines:
            self.linecount += 1
            self.python_context["linecount"] = self.linecount
            #print(linecount)
            s = raw.strip()
            if any(s.startswith(pref) for pref in (
                    'general set', 'algebraic set', 'logical set',
                    'logical compare', 'print text', 'print variable', 'if variable'
            )):
                self.logic_interp.run_line(s)
                continue
            m = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)', s)
            if m:
                nm, ag = m.groups()
                args_list = [self.logic_interp.expand_vars(a) for a in ag.split()]
                ret = self.execute_function(nm, args_list)
                if ret is not None:
                    print(ret)
            m = re.match(r'input (\w+) "(.+)"', s)
            if m:
                var_expr, instring = m.groups()
                val = input(instring)
                self.logic_interp.vars[var_expr.strip()] = val

    def match_type(self, value, typename):
        rule = self.types.get(typename)
        if not rule:
            return False

        # Preprocess type rule
        rule = rule.strip().lower()

        # Common type checks
        if '0..9' in rule:
            if re.fullmatch(r'\d+', str(value)):
                return True

        if 'float' in rule or '0..9.0..9' in rule:
            if re.fullmatch(r'\d+\.\d+', str(value)):
                return True

        if '*reg' in rule and '\\w+' in rule:
            if re.fullmatch(r'\w+', str(value)):
                return True

        if '*v' in rule and isinstance(value, str) and value in self.vars:
            return True

        if 'any in' in rule:
            # Check if value is in a variable list like !hexbytes!
            match = re.search(r'any in !(\w+)!', rule)
            if match:
                varname = match.group(1)
                data = self.vars.get(varname)
                if isinstance(data, list) and value in data:
                    return True

        if 'matches r[' in rule or 'matches z[' in rule:
            if re.match(r'[rz]\[.*\]\[.*\]', str(value)):
                return True

        if 'matches {"*key", "*value"}' in rule:
            if re.match(r'\{"\w+",\s*"\w+"\}', str(value)):
                return True

        if 'matches (*, *)' in rule:
            if re.match(r'\(.*?,.*?\)', str(value)):
                return True

        if '*' in rule:  # Wildcard match
            return True

        return False


def main():
    if len(sys.argv) < 1:
        print("Usage: python interpreter.py <file_path> <options>")
        sys.exit(0)
    if not sys.argv[1] == "-terminal":
        path = sys.argv[1]
        try:
            raw_lines = open(path, 'r', encoding='utf-8').readlines()
        except FileNotFoundError:
            fprint(f"File not found: {path}", "ERROR", Fore.RED)
            sys.exit(1)
        lines = []
        linecount = 0
        for raw in raw_lines:
            m = re.match(r'using resource\s+(\w+)', raw.strip())
            if m:
                name = m.group(1)
                file_path = os.path.abspath(__file__)  # Get the absolute path of the current file
                directory_path = os.path.dirname(file_path)
                res_path = os.path.join(directory_path, 'res', f'{name}.logical')
                if not os.path.exists(res_path):
                    fprint(f"Resource not found: {res_path}", "ERROR", Fore.RED)
                    fprint(f"Functions types or variables pulled from this source might not work or error. "
                           f"\n...... Verify that the file exists and that the location and/or the path is correct.", "INFO", Fore.YELLOW)
                    _ = input("Press ENTER to continue.")
                else:
                    with open(res_path, 'r', encoding='utf-8') as rf:
                        lines.extend(rf.readlines())
            else:
                lines.append(raw)

        mode = None
        with open(f"{basepath}/rt_temp.ltmp", "wb") as _L:
            _L.write(bytes(f"rtid:{rtid} // ver:{__version__}~{__compat__}\n", "utf-8"))
        with open(f"{basepath}/nulled.ltmp", "wb") as _L:
            _L.write(bytes(f"rtid:{rtid} // ver:{__version__}~{__compat__}\n", "utf-8"))
        with open(f"{basepath}/temp.pairs", "w") as _S:
            _S.write(f"rtid:{rtid} // ver:{__version__}~{__compat__}\n")
        for l in lines:
            if l.startswith("clear"):
                os.system("cls")
            text = ''
            with open(f"{basepath}/nulled.ltmp", "ab") as _L:
                for char in l:
                    _L.write(bytes(chr(ord(char) + ord(char)), "utf-8"))
            with open(f"{basepath}/rt_temp.ltmp", "ab") as _L:
                for char in l:
                    _L.write(bytes(chr(ord(char) + 12), "utf-8"))
                    text += bytes_to_custom_pairs(bytes(char, "utf-8"), " ") + " "
            with open(f"{basepath}/temp.pairs", "a") as _S:
                _S.write(text)
            linecount += 1
            currentline = linecount
            if l.strip().startswith('*FILETYPE'):
                parts = l.strip().split(maxsplit=1)
                mode = parts[1].strip() if len(parts) > 1 else ''
                break
        if mode == 'logic':
            interpreter = LogicInterpreter()
        elif mode == 'compound':
            interpreter = CompoundInterpreter()
        else:
            fprint(f"unsupported FILETYPE '{mode}'", "ERROR", Fore.RED)
            sys.exit(1)
        for line in lines:
            with open(f"{basepath}/rt_temp.ltmp", "ab") as _L:
                for char in line:
                    _L.write(bytes(chr(ord(char) + 12),"utf-8"))
        for line in lines:
            with open(f"{basepath}/nulled.ltmp", "ab") as _L:
                for char in line:
                    _L.write(bytes(chr(ord(char) + ord(char)),"utf-8"))
        interpreter.run(lines)
    else:
        if sys.argv[2] == "-logic":
            interpreter = LogicInterpreter()
        if sys.argv[2] == "-compound":
            interpreter = LogicInterpreter()
        while True:
            lines = []
            data = input(">> ")
            if data == "help":
                with open(f"{basepath}/helpfile", "r") as _f:
                    print(_f.read())
            elif data == "clear":
                os.system("cls")
            elif data == "env":
                os.system("set")
            elif data.startswith("using"):
                name = data.split(' ')[2]
                file_path = os.path.abspath(__file__)  # Get the absolute path of the current file
                directory_path = os.path.dirname(file_path)
                res_path = os.path.join(directory_path, 'res', f'{name}.logical')
                if not os.path.exists(res_path):
                    fprint(f"Resource not found: {res_path}", "ERROR", Fore.RED)
                    sys.exit(1)
                with open(res_path, 'r', encoding='utf-8') as rf:
                    lines.extend(rf.readlines())
            elif data.startswith("run"):
                interpreter.run(lines)
            else:
                lines.append(data)

if __name__ == "__main__":
    main()
