import re
import sys
import os

from printmods import fprint, fprint_s, Fore
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
        text = re.sub(r'param:(\w+)', lambda m: str(self.current_params.get(m.group(1), '')), text)
        text = re.sub(r'!(\w+)!', lambda m: str(self.vars.get(m.group(1), '')), text)
        return text

    def run_line(self, line):
        raw = line.strip()
        if not raw or raw.startswith(('comment', 'name ', 'using ')):
            return

        # Detect and announce mode
        if self.filetype is None and raw.startswith('*FILETYPE'):
            _, ft = raw.split(maxsplit=1)
            self.filetype = ft.strip()
            fprint(self.filetype, "MODE", Fore.BLUE)
            return

        # FOR loops
        m = re.match(r'for (\w+) from (\d+) to (\d+) then (.+)', raw)
        if m:
            var, start, end, rest = m.groups()
            for i in range(int(start), int(end) + 1):
                self.vars[var] = i
                self.run_line(rest)
            return
        m = re.match(r'for (\w+) in (\w+) then (.+)', raw)
        if m:
            var, lst, rest = m.groups()
            for item in self.vars.get(lst, []):
                self.vars[var] = item
                self.run_line(rest)
            return

        # RETURN
        m = re.match(r'return (.+)', raw)
        if m:
            expr = m.group(1)
            expr = self.expand_vars(expr)

            try:
                val = int(expr)
            except ValueError:
                try:
                    val = eval(expr, {}, self.vars)
                except:
                    val = expr
            raise ReturnSignal(val)

        # GENERAL SET: dynamic variable names allowed
        m = re.match(r'general set variable (.+?) to (.+)', raw)
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
                expr_val = self.expand_vars(expr)
                try:
                    val = int(expr_val)
                except:
                    val = expr_val
            self.vars[var_name] = val
            return

        # ALGEBRAIC SET
        m = re.match(r'algebraic set variable (\w+) to (.+)', raw)
        if m:
            var, expr = m.groups()
            expr_val = self.expand_vars(expr)
            try:
                val = eval(expr_val, {}, self.vars)
            except TypeError:
                parts = [p.strip() for p in expr_val.split('+')]
                vals = []
                for part in parts:
                    try:
                        v = eval(part, {}, self.vars)
                    except:
                        v = self.vars.get(part, part)
                    vals.append(v)
                val = ''.join(str(v) for v in vals)
            except Exception as e:
                fprint(f"evaluating '{expr}': {e}", "ERROR", Fore.RED)
                return
            self.vars[var] = val
            return

        # LOGICAL SET
        m = re.match(r'logical set variable (\w+) to (true|false)', raw)
        if m:
            var, val = m.groups()
            self.vars[var] = (val == 'true')
            return

        # LOGICAL COMPARE
        m = re.match(r'logical compare with output (\w+) as the (and|or|not) of (.+)', raw)
        if m:
            out, op, args = m.groups()
            parts = args.split()
            vals = [bool(self.vars.get(p, False)) for p in parts]
            res = {'and': all(vals), 'or': any(vals), 'not': not vals[0] if vals else True}[op]
            self.vars[out] = res
            return

        # IF statement
        m = re.match(r'if variable (\w+) is (greater|less|equal) than variable (\w+) then (.+)', raw)
        if m:
            v1, cond, v2, rest = m.groups()
            a = self.vars.get(v1, 0)
            b = self.vars.get(v2, 0)
            cmp_map = {'greater': a > b, 'less': a < b, 'equal': a == b}
            if cmp_map.get(cond):
                self.run_line(rest)
            return

        # PRINT TEXT
        m = re.match(r'print text (.+)', raw)
        if m:
            txt = m.group(1)
            print() if txt.strip() == '.' else print(txt)
            return

        # PRINT VARIABLE
        m = re.match(r'print variable (\w+)', raw)
        if m:
            print(self.vars.get(m.group(1), ''))
            return

        # Fallback unknown
        fprint(raw, "UNKNOWN", Fore.YELLOW)

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


