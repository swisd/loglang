import re
import sys
import os
import platform
from printmods import fprint, fprint_s, Fore
__version__ = '8a24c3'
__compat__ = '12w5'
print(f"Running on {platform.system()} {platform.release()} {platform.version()}")
print(f"Interpreter Version {__version__}-SP{__compat__}")
if platform.system() == "Windows":
    os.system('')  # Enables ANSI escape codes
import random

rtid = random.randrange(65536)

class ReturnSignal(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value

class BaseInterpreter:
    """Abstract base for LogLang mode interpreters."""
    def __init__(self):
        self.filetype = None

    def run(self, lines):
        raise NotImplementedError("Must implement run() in subclass")

class LogicInterpreter(BaseInterpreter):
    """Interpreter for LogLang 'logic' mode with return, loop, and dynamic vars support."""
    def __init__(self):
        super().__init__()
        self.vars = {}
        self.current_params = {}

    def expand_vars(self, text):
        # First replace param:foo then !foo! in text
        text = re.sub(r'param:(\w+)', lambda m: str(self.current_params.get(m.group(1), '')), text)
        text = re.sub(r'!(\w+)!', lambda m: str(self.vars.get(m.group(1), '')), text)
        return text

    def run_line(self, line):
        s = line.strip()
        if not s or s.startswith(('comment', 'name ', 'using ')):
            return

        # Detect and announce mode
        if self.filetype is None and s.startswith('*FILETYPE'):
            _, ft = s.split(maxsplit=1)
            self.filetype = ft.strip()
            fprint(self.filetype, "MODE", Fore.BLUE)
            return

        if s.startswith('*uVERSION'):
            ft = (s.split(" "))[1]
            print(ft)
            if (ft.split("a"))[0] > (__version__.split("a"))[0]:
                raise RuntimeError(f"{Fore.RED}This file is not supported because it uses a newer version of LogicLang and therefore requires a compatible interpreter.\n"
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

        # RETURN
        m = re.match(r'return (.+)', s)
        if m:
            expr = m.group(1)
            try:
                val = int(expr)
            except ValueError:
                try:
                    val = eval(expr, {}, self.vars)
                except:
                    val = expr
            raise ReturnSignal(val)

        # GENERAL SET: dynamic variable names allowed
        m = re.match(r'general set variable (.+?) to (.+)', s)
        if m:
            var_expr, expr = m.groups()
            var_name = self.expand_vars(var_expr).strip()
            # check for function call in RHS
            call = re.match(r'(\w+(?:\.\w+)*)\((.*?)\)', expr)
            if call:
                fn, args = call.groups()
                args_list = [self.expand_vars(a) for a in args.split()]
                val = self.call_function(fn, args_list)
            else:
                val_str = self.expand_vars(expr)
                try:
                    val = int(val_str)
                except:
                    val = val_str
            self.vars[var_name] = val
            return

        # ALGEBRAIC SET
        m = re.match(r'algebraic set variable (\w+) to (.+)', s)
        if m:
            var, expr = m.groups()
            try:
                self.vars[var] = eval(expr, {}, self.vars)
            except Exception as e:
                fprint(f"evaluating '{expr}': {e}", "ERROR", Fore.RED)
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
        m = re.match(r'if variable (\w+) is (greater|less|equal) than variable (\w+) then (.+)', s)
        if m:
            v1, cond, v2, rest = m.groups()
            a = self.vars.get(v1, 0)
            b = self.vars.get(v2, 0)
            cmp_map = {'greater': a > b, 'less': a < b, 'equal': a == b}
            if cmp_map.get(cond):
                self.run_line(rest)
            return

        # PRINT TEXT
        m = re.match(r'print text (.+)', s)
        if m:
            txt = m.group(1)
            print() if txt.strip() == '.' else print(txt)
            return

        # PRINT VARIABLE
        m = re.match(r'print variable (\w+)', s)
        if m:
            print(self.vars.get(m.group(1), ''))
            return

        # Fallback unknown
        fprint(s, "UNKNOWN", Fore.YELLOW)

    def call_function(self, name, args):
        raise NotImplementedError

    def run(self, lines):
        for line in lines:
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
        self.do_dump = True

    def execute_function(self, name, args):
        if '.' in name:
            cls, method = name.split('.', 1)
            fn = self.classes.get(cls, {}).get(method)
        else:
            fn = self.functions.get(name)
        if not fn:
            fprint(f"function '{name}' not found", "ERROR", Fore.RED)
            return None
        if len(args) != len(fn['params']):
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
        current_fn = None
        current_cls = None
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('comment'):
                continue
            if line.startswith('*CONFIG'):
                parts = line.split()
                if len(parts) > 1:
                    if parts[1].lower() == 'd0': self.do_dump = False
                    elif parts[1].lower() == 'd1': self.do_dump = True
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
            m = re.match(r'type\s+(\w+)\s+\(matches any in (\w+)\)', line)
            if m:
                name, src = m.groups()
                self.types[name] = self.definitions.get(src, [])
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
        for raw in lines:
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <file_path> <options>")
        sys.exit(0)
    path = sys.argv[1]
    try:
        raw_lines = open(path, 'r', encoding='utf-8').readlines()
    except FileNotFoundError:
        fprint(f"File not found: {path}", "ERROR", Fore.RED)
        sys.exit(1)
    lines = []
    for raw in raw_lines:
        m = re.match(r'using resource\s+(\w+)', raw.strip())
        if m:
            name = m.group(1)
            file_path = os.path.abspath(__file__)  # Get the absolute path of the current file
            directory_path = os.path.dirname(file_path)
            res_path = os.path.join(directory_path, 'res', f'{name}.logical')
            if not os.path.exists(res_path):
                fprint(f"Resource not found: {res_path}", "ERROR", Fore.RED)
                sys.exit(1)
            with open(res_path, 'r', encoding='utf-8') as rf:
                lines.extend(rf.readlines())
        else:
            lines.append(raw)


    mode = None
    for l in lines:
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
    interpreter.run(lines)

if __name__ == "__main__":
    main()


