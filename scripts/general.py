import os
import sys
import argparse
import shlex
import shutil
import stat
import tempfile
import time
from pathlib import Path

from ltl_decompose import decompose_ltl, DecompositionResult, format_result
from call import SolverError, call_nusmv, call_get_path
from generate_nuxmv import create_nusmv_file
from alg_paper import not_in_v, renaming, call_full_aalta, call_aalta_var_list
from readXML import parse_xml, not_same_var
from req_parser import parse_req_exp
from sys import platform
from project_paths import FILES_DIR, RESULTS_DIR, SCRIPTS_DIR


def _temporary_nusmv_file(env_vars, sys_vars):
    descriptor, model_path = tempfile.mkstemp(
        prefix='indvar_', suffix='.smv', dir=SCRIPTS_DIR
    )
    os.close(descriptor)
    create_nusmv_file(env_vars, sys_vars, model_path)
    return Path(model_path)


def generate_exp(fi, cs, ncs, is_nusmv):
    """
    This function generates the formula to ask the checker or the SAT Tool.

    Parameters
    ----------

    fi : str
        Initial formula.
    cs : list
        Variables in one group which after must be renamed.
    ncs : list
        Complementary group of variables.
    is_nusmv : bool
        If the expression is generated for NuSMV or for Aalta. (A model checker or a SAT solver).

    Returns
    -------
    str
        The original formula renamed with the corresponding variables.
    """
    fi_cs = fi
    fi_not_cs = fi
    for v in cs:
        fi_cs = renaming(fi_cs, v, "_")
    for v in ncs:
        fi_not_cs = renaming(fi_not_cs, v, "_")
    if is_nusmv:
        # !fi_cs || !fi_ncs || fi
        # return "!(" + fi_cs + ") | !(" + fi_not_cs + ") | (" + fi + ")"
        return f"!({fi_cs}) | !({fi_not_cs}) | ({fi})"
    else:
        # fi_cs && fi_ncs && !fi
        # return "(" + fi_cs + ") & (" + fi_not_cs + ") & !(" + fi + ")"
        return f"({fi_cs}) & ({fi_not_cs}) & !({fi})"


def look_for_dep_var(fi, oldfi, changing_vars, cs, treated, cv, model_file):
    # cz = not_in_v(cs, changing_vars)
    z = changing_vars[0]
    inv = " | !(" + z + " <-> " + z + "_)"
    newfi = oldfi + inv
    trace_path = call_nusmv(model_file, newfi, "counterexample")
    if trace_path.exists():
        new_changing_vars = ob_vars(cs, treated, trace_path)
        return look_for_dep_var(fi, newfi, new_changing_vars, cs, treated, cv, model_file)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, cv)
        if ncs:
            other_fi = generate_exp(fi, cs, ncs, True)
            trace_path = call_nusmv(model_file, other_fi, "counterexample")
            if trace_path.exists():
                changing_vars = ob_vars(cs, treated, trace_path)
                return look_for_dep_var(fi, other_fi, changing_vars, cs, treated, cv, model_file)
            else:
                return cs
        else:
            return cs


def look_for_dep_var_while_aalta(fi, oldfi, changing_vars, cs, treated, cv, is_model, is_temporal):
    # cz = not_in_v(cs, changing_vars)
    newfi = oldfi
    while is_model:
        z = changing_vars[0]
        if is_temporal:
            inv = " & G(" + z + " <-> " + z + "_)"
        else:
            inv = " & (" + z + " <-> " + z + "_)"
        newfi += inv
        aalta_res, model = call_full_aalta('expression.dimacs', newfi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
        else:
            is_model = False
            # He cambiado esto dentro del else por la variable z
            cs.append(z)
            treated.append(z)
    ncs = not_in_v(cs, cv)
    if ncs:
        other_fi = generate_exp(fi, cs, ncs, False)
        aalta_res, model = call_full_aalta('expression.dimacs', other_fi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
            return look_for_dep_var_while_aalta(fi, other_fi, changing_vars, cs, treated, cv, True, is_temporal)
        else:
            return cs
    else:
        return cs


def look_for_dep_var_while(fi, oldfi, changing_vars, cs, treated, cv, is_model, is_temporal, model_file):
    # cz = not_in_v(cs, changing_vars)
    newfi = oldfi
    while is_model:
        z = changing_vars[0]
        if is_temporal:
            inv = " | F(!(" + z + " <-> " + z + "_))"
        else:
            inv = " | !(" + z + " <-> " + z + "_)"
        newfi += inv
        trace_path = call_nusmv(model_file, newfi, "counterexample")
        if trace_path.exists():
            new_changing_vars = ob_vars(cs, treated, trace_path)
            if not new_changing_vars:
                raise RuntimeError(
                    "The counterexample contains no untreated dependent variable"
                )
            changing_vars = new_changing_vars
        else:
            is_model = False
            # He cambiado esto dentro del else por la variable z
            cs.append(z)
            treated.append(z)
    ncs = not_in_v(cs, cv)
    if ncs:
        other_fi = generate_exp(fi, cs, ncs, True)
        trace_path = call_nusmv(model_file, other_fi, "counterexample")
        if trace_path.exists():
            changing_vars = ob_vars(cs, treated, trace_path)
            if not changing_vars:
                raise RuntimeError(
                    "The counterexample contains no untreated dependent variable"
                )
            return look_for_dep_var_while(
                fi, other_fi, changing_vars, cs, treated, cv, True,
                is_temporal, model_file
            )
        else:
            return cs
    else:
        return cs


def partition(fi, cv):
    return partition_general(fi, cv, [], False, True)


def partition_general(fi, cv, treated, is_temporal, is_nusmv):
    expected_variables = list(cv)
    if is_nusmv:
        groups = partition_recursive(fi, cv, treated, is_temporal)
    else:
        groups = partition_recursive_aalta(fi, cv, treated, is_temporal)

    flattened = flatt_list(groups)
    if len(flattened) != len(set(flattened)):
        raise RuntimeError(f"Solver produced overlapping variable groups: {groups}")
    if set(flattened) != set(expected_variables):
        missing = sorted(set(expected_variables) - set(flattened))
        unexpected = sorted(set(flattened) - set(expected_variables))
        raise RuntimeError(
            f"Invalid variable partition; missing={missing}, unexpected={unexpected}"
        )
    return groups


def partition_recursive_aalta(fi, cv, treated, is_temporal):
    if not cv:
        return []
    # elif len(cv) == 1:
    #     return [cv]
    else:
        v = cv[0]
        cs = [v]
        treated.append(v)
        ncs = not_in_v(cs, cv)
        newfi = generate_exp(fi, cs, ncs, False)
        aalta_res, model = call_full_aalta('expression.dimacs', newfi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
            cs = look_for_dep_var_while_aalta(fi, newfi, changing_vars, cs, treated, cv, True, is_temporal)
        cv = not_in_v(cs, cv)
        return [cs] + partition_recursive_aalta(fi, cv, treated, is_temporal)


def partition_recursive(fi, cv, treated, is_temporal):
    if not cv:
        return []
    # elif len(cv) == 1:
    #     return [cv]
    else:
        v = cv[0]
        cs = [v]
        model_file = _temporary_nusmv_file(treated, cv)
        try:
            treated.append(v)
            ncs = not_in_v(cs, cv)
            newfi = generate_exp(fi, cs, ncs, True)
            trace_path = call_nusmv(model_file, newfi, "counterexample")
            if trace_path.exists():
                changing_vars = ob_vars(cs, treated, trace_path)
                if not changing_vars:
                    raise RuntimeError(
                        "The counterexample contains no untreated dependent variable"
                    )
                cs = look_for_dep_var_while(
                    fi, newfi, changing_vars, cs, treated, cv, True,
                    is_temporal, model_file
                )
            cv = not_in_v(cs, cv)
        finally:
            model_file.unlink(missing_ok=True)
        return [cs] + partition_recursive(fi, cv, treated, is_temporal)


def __var_list_from_tree(exp):
    # From a binary tree of a requirement returns it on a string

    if not (type(exp) == str):
        if len(exp) == 2:
            return __var_list_from_tree(exp[1])
        elif len(exp) == 3:
            return __var_list_from_tree(exp[1]) + __var_list_from_tree(exp[2])
        else:
            return [exp[0]]
    else:
        return [exp]

# def __var_list_from_tree(exp):
#     vars_set = set()
#
#     operadores = {'!', '~', '&', '&&', '|', '||', '->', '<->', 'X', 'F', 'G'}
#
#     def helper(node):
#         if isinstance(node, str):
#             # Cadena no vacía y no operador, es variable
#             if node and node not in operadores:
#                 vars_set.add(node)
#         elif isinstance(node, (list, tuple)):
#             for child in node:
#                 # Ignorar cadenas vacías o None
#                 if child not in ('', None):
#                     helper(child)
#
#     helper(exp)
#     return sorted(vars_set)
#


def var_list_exp(exp):
    l = __var_list_from_tree(exp)
    return list(dict.fromkeys(l))


def ob_vars(cs, treated, trace_path):
    try:
        counterex = parse_xml(trace_path)
    finally:
        Path(trace_path).unlink(missing_ok=True)
    dvars = list(dict.fromkeys(not_same_var(counterex)))
    l3 = not_in_v(cs, dvars)
    return not_in_v(treated, l3)


def __env_process(l):
    prefix, separator, values = l.partition(":")
    if prefix.strip().lower() != "env_vars":
        return None
    if not separator:
        raise ValueError("An env_vars declaration must contain ':'")
    return extract_env_vars(values)


def parse_arguments():
    parser = argparse.ArgumentParser(description="LTL decomposition tool")
    parser.add_argument("-f", dest="filename", help="Read the logical expression from FILE",
                        metavar="FILE")
    parser.add_argument(
        "--solver",
        choices=("nusmv", "aalta"),
        help="Solver backend (default: NuSMV on macOS; prompt on Linux)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--decompose', action='store_true',
                      help='Extract and certify formula components without asking')
    mode.add_argument('--partition-only', action='store_true',
                      help='Only compute variable groups; do not ask for extraction')
    return parser.parse_args()


def terminal_use(args=None):
    # Read the arguments from the terminal
    if args is None:
        args = parse_arguments()
    # print("Entra aquí")
    if not args.filename:
        if not sys.stdin.isatty():
            raise SystemExit("Non-interactive execution requires -f FILE.")
        return "", [], ""
    else:
        if not os.path.exists(args.filename):
            parser.error(f"file not found: {args.filename}")
        else:
            formula_parts = []
            e_vars = []
            env_declaration_seen = False
            with open(args.filename, "r") as input_file:
                for line in input_file:
                    text = line.rstrip('\n')
                    declared_vars = __env_process(text)
                    if declared_vars is None:
                        formula_parts.append(text)
                    elif env_declaration_seen:
                        raise ValueError("Only one env_vars declaration is allowed")
                    else:
                        e_vars = declared_vars
                        env_declaration_seen = True
            formula = ''.join(formula_parts)
            return formula, e_vars, args.filename


def no_file_terminal():
    # When there is no file in the arguments
    print("\nEnter the formula:")
    formula = input()
    return formula


def __get_formula(args=None):
    file_name = ""
    f, e, file_name = terminal_use(args)
    if not f:
        f = no_file_terminal()
    return f, e, file_name


def create_bash_file(solver_path, is_nusmv):
    # Create the solver launcher using the discovered executable path.
    executable = shlex.quote(str(solver_path))
    if is_nusmv:
        script_name = SCRIPTS_DIR / "call_nusmv.sh"
        content = f'#!/bin/bash\n\n{executable} -int "$2" <<< "$1"'
    else:
        script_name = SCRIPTS_DIR / "call_aalta.sh"
        content = f'#!/bin/bash\n\ncat "$1" | {executable} -e > "$2"'

    with open(script_name, "w") as script:
        script.write(content)
    os.chmod(script_name, stat.S_IRWXU)


def get_app_path(is_linux, is_nusmv):
    # Prefer executables available on PATH, including Homebrew installations.
    executable = "NuSMV" if is_nusmv else "aalta"
    solver_path = shutil.which(executable)
    if solver_path:
        return solver_path

    # Retain the original filesystem search as a fallback.
    call_get_path(is_linux, is_nusmv)
    paths_file = FILES_DIR / "allpaths.txt"
    try:
        with open(paths_file) as paths:
            return paths.readline().rstrip("\n")
    except OSError:
        return ""
    finally:
        paths_file.unlink(missing_ok=True)


def checker_path(is_linux, is_nusmv):
    # Gets the path and creates the bash file for NuSMV or Aalta
    path = get_app_path(is_linux, is_nusmv)
    if path:
        create_bash_file(path, is_nusmv)



def pregunta_path(is_linux, is_nusmv):
    # Questions to start the app
    print("Looking for the solver executable...")
    checker_path(is_linux, is_nusmv)



def get_the_partition(formula, var_tree, variables, var_groups, is_nusmv):
    # Save the expression tree when created
    # Ask NuSMV for a model of the original formula
    # Save the value of the variables
    # While there are groups of the variables left
    #   Give the value to the rest of the variables and treat the tree
    #   Save the result of the final expression
    model = None
    if is_nusmv:
        model_file = _temporary_nusmv_file(variables, [])
        try:
            trace_path = call_nusmv(
                model_file, '!(' + formula + ')', "counterexample"
            )
            if not trace_path.exists():
                raise SystemExit('The formula has no satisfying model.')
            try:
                counterex = parse_xml(trace_path)
            finally:
                trace_path.unlink(missing_ok=True)
            model = counterex[0][0]
        finally:
            model_file.unlink(missing_ok=True)
    else:
        aalta_res, model = call_aalta_var_list('expression.dimacs', formula)
        if aalta_res == 'unsat':
            raise SystemExit('The formula has no satisfying model.')
    f = []
    i = 0
    for i in range(len(var_groups)):
        if i == 0:
            selected_vars = flatt_list(var_groups[i+1:])
        elif i == len(var_groups)-1:
            selected_vars = flatt_list(var_groups[:len(var_groups)-1])
        else:
            selected_vars = flatt_list(var_groups[:i] + var_groups[i+1:])
        f_i = get_new_formula(var_tree, model, selected_vars)
        f.append(f_i)
    return f


def flatt_list(l):
    return [item for sublist in l for item in sublist]


def get_new_formula(tree, model, sel_vars):
    # Given a tree of the formula and a model that satisfies it, returns
    t = __change_values_tree(tree, model, sel_vars)
    nt = __simplify_tree(t)
    return nt


def __change_values_tree(tree, model, sel_vars):
    if not (type(tree) == str):
        if len(tree) == 2:
            return [tree[0], __change_values_tree(tree[1], model, sel_vars)]
        elif len(tree) == 3:
            return [tree[0], __change_values_tree(tree[1], model, sel_vars), __change_values_tree(tree[2], model, sel_vars)]
        else:
            # No se en que caso se da esto pero por si acaso
            return [__change_values_tree(tree[0], model, sel_vars)]
    else:
        if tree in sel_vars:
            return __get_var_value(tree, model)
        else:
            return tree


def __simplify_tree(tree):
    if type(tree) != str:
        if len(tree) == 2:
            if tree[1] == 'True':
                return 'False'
            elif tree[1] == 'False':
                return 'True'
            else:
                return tree[0] + '(' + __simplify_tree(tree[1]) + ')'
        elif len(tree) == 3:
            if tree[1] == 'True':
                if tree[0] == '&':
                    return __simplify_tree(tree[2])
                elif tree[0] == '|':
                    return 'True'
                else:
                    # ->
                    return __simplify_tree(tree[2])
            elif tree[1] == 'False':
                if tree[0] == '&':
                    return 'False'
                elif tree[0] == '|':
                    return __simplify_tree(tree[2])
                else:
                    # ->
                    return 'True'
            elif tree[2] == 'True':
                if tree[0] == '&':
                    return __simplify_tree(tree[1])
                elif tree[0] == '|':
                    return 'True'
                else:
                    # ->
                    return 'True'
            elif tree[2] == 'False':
                if tree[0] == '&':
                    return 'False'
                elif tree[0] == '|':
                    return __simplify_tree(tree[1])
                else:
                    # ->
                    return __simplify_tree(['!', tree[1]])
            else:
                izq = __simplify_tree(tree[1])
                der = __simplify_tree(tree[2])
                if izq == 'True':
                    if tree[0] == '&':
                        return der
                    elif tree[0] == '|':
                        return 'True'
                    else:
                        # ->
                        return der
                elif izq == 'False':
                    if tree[0] == '&':
                        return 'False'
                    elif tree[0] == '|':
                        return der
                    else:
                        # ->
                        return 'True'
                elif der == 'True':
                    if tree[0] == '&':
                        return izq
                    elif tree[0] == '|':
                        return 'True'
                    else:
                        # ->
                        return 'True'
                elif der == 'False':
                    if tree[0] == '&':
                        return 'False'
                    elif tree[0] == '|':
                        return izq
                    else:
                        # ->
                        return '!(' + izq + ')'
                else:
                    return '(' + izq + ' ' + tree[0] + ' ' + der + ')'
        else:
            return tree[0]
    else:
        return tree


def __get_var_value(v, model):
    for m in model:
        if v == m.get_name():
            return str(m.get_value())
    raise RuntimeError(f"The solver model does not contain variable '{v}'")


def ask_for_env(variables, res):
    evars = extract_env_vars(res)
    for v in evars:
        if v not in variables:
            print(f"The variable '{v}' does not occur in the formula. "
                  "Enter the environment variables again, or type 'quit' to exit:")
            r = input()
            r = r.replace(" ", "")
            if r == "quit":
                quit("\nSee you next time!")
            else:
                return ask_for_env(variables, r)
    return evars

# G((p -> X(v & !(t))) & (! p -> X(!(v) & t)) & (v -> X(!(w) & u)) & (!(v) -> X(w & !(u))))
def extract_env_vars(res):
    res_a = res.replace(" ", "")
    return list(dict.fromkeys(var for var in res_a.split(",") if var))


def check_is_temporal(var_tree):
    if not (type(var_tree) == str):
        if len(var_tree) == 2:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return check_is_temporal(var_tree[1])
        elif len(var_tree) == 3:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return check_is_temporal(var_tree[1]) or check_is_temporal(var_tree[2])
        else:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return False
    else:
        return False


def full_process(first, is_nusmv, args=None):
    # Gets the formula and calls the main method partition_recursive
    if first:
        formula, env_vars, file_name = __get_formula(args)
        # print(file_name)
    else:
        formula = no_file_terminal()
        env_vars = []
        file_name = ""
    if file_name:
        print('\nInput formula:\n  ' + formula.strip() + '\n')
    var_tree = parse_req_exp(formula, 'ltl')
    variables = var_list_exp(var_tree)
    unknown_env_vars = sorted(set(env_vars) - set(variables))
    if unknown_env_vars:
        source = f" in {file_name}" if file_name else ""
        raise SystemExit(
            f"Environment variable(s){source} do not occur in the formula: "
            + ", ".join(unknown_env_vars)
        )
    temporal = check_is_temporal(var_tree)
    if temporal and not env_vars and sys.stdin.isatty():
        # An explicit empty declaration in a file also means no environment vars.
        declared = file_name and any(
            line.strip().lower().startswith('env_vars:')
            for line in Path(file_name).read_text().splitlines()
        )
        if not declared:
            res = input("\nEnter the environment variables as a comma-separated list, "
                        "or type '-' if there are none:\n")
            if res != '-':
                env_vars = ask_for_env(variables, res)
    sys_vars = not_in_v(env_vars, variables)
    print("Computing the variable decomposition...")
    var_groups = partition_general(
        formula, sys_vars, env_vars.copy(), temporal, is_nusmv
    )
    print("\n" + format_partition(env_vars, var_groups))
    complete = getattr(args, 'decompose', False)
    if not complete and not getattr(args, 'partition_only', False) and sys.stdin.isatty():
        try:
            complete = input("\nCompute the full formula decomposition? [y/N]: ").strip().lower() in ('y', 'yes')
        except EOFError:
            complete = False
    form_groups = None
    if complete:
        print("\nComputing the full formula decomposition...")
        form_groups = decompose_ltl(
            formula, env_vars, var_groups, "nusmv" if is_nusmv else "aalta"
        )
    return var_groups, form_groups, file_name, env_vars, formula


def format_partition(env_vars, groups):
    lines = ['Environment vars: {' + ', '.join(env_vars) + '}',
             '', 'Independent system variable sets:']
    lines.extend(f"  {i}: {{" + ', '.join(group) + '}'
                 for i, group in enumerate(groups, 1))
    if not groups:
        lines.append('  {}')
    return '\n'.join(lines)


def get_so():
    if platform == "linux" or platform == "linux2":
        return "linux"
    elif platform == "darwin":
        return "macos"
    elif platform == "win32":
        return "windows"
    else:
        quit("\nThis operating system is not supported.")


def output_file(v_g, f_g, name, env_vars=(), formula=None):
    # Creation of the output file
    input_path = Path(name)
    output_path = RESULTS_DIR / f'{input_path.stem}_r.txt'
    RESULTS_DIR.mkdir(exist_ok=True)
    with output_path.open('w') as out_file:
        out_file.write(f"Decomposition results for {input_path.name}.\n\n")
        if formula is not None:
            out_file.write("Input formula:\n  " + formula.strip() + "\n\n")
        out_file.write(format_partition(env_vars, v_g) + "\n")
        if isinstance(f_g, DecompositionResult):
            out_file.write(format_result(f_g) + "\n")
        elif f_g is not None:
            out_file.write("The formulas are decomposed as follows: ")
            __print_variables(out_file, f_g)


def __print_variables(out_file, v_g):
    line = ""
    for groups in v_g:
        line += str(groups)
        line += ", "
    out_file.write(line[:-2] + "\n")


def main_in(first, program_name, is_nusmv, args=None):
    var_groups, form_groups, file_name, env_vars, formula = full_process(first, is_nusmv, args)
    if isinstance(form_groups, DecompositionResult):
        print("\n" + format_result(form_groups))
    if file_name:
        output_file(var_groups, form_groups, file_name, env_vars, formula)


def main():
    args = parse_arguments()
    program_name = "IndVarLTL"
    print("Welcome to " + program_name + ".")
    is_nusmv = True
    os_name = get_so()
    if os_name == "windows":
        quit("IndVarLTL does not currently support Windows.")

    if args.solver is not None:
        is_nusmv = args.solver == "nusmv"
        solver_name = "NuSMV" if is_nusmv else "Aalta"
        print(f"{solver_name} was selected with --solver.")
        launcher = SCRIPTS_DIR / (
            "call_nusmv.sh" if is_nusmv else "call_aalta.sh"
        )
        if not launcher.is_file():
            pregunta_path(os_name == "linux", is_nusmv)
    elif os_name == "macos" or not sys.stdin.isatty():
        print("NuSMV will be used by default. Use --solver aalta to select Aalta.")
        if not (SCRIPTS_DIR / "call_nusmv.sh").is_file():
            pregunta_path(False, True)
    else:
        print("\nWhich solver would you like to use?\n"
              "Enter 1 for NuSMV, 2 for Aalta, or any other value to exit:")
        res1 = input()
        if res1 == '1':
            if not (SCRIPTS_DIR / "call_nusmv.sh").is_file():
                pregunta_path(True, is_nusmv)
        elif res1 == '2':
            is_nusmv = False
            if not (SCRIPTS_DIR / "call_aalta.sh").is_file():
                pregunta_path(True, is_nusmv)
        else:
            quit("\nSee you next time!")

    selected_launcher = SCRIPTS_DIR / (
        "call_nusmv.sh" if is_nusmv else "call_aalta.sh"
    )
    if selected_launcher.is_file():
        main_in(True, program_name, is_nusmv, args)
    else:
        print("A solver could not be configured. Make sure that NuSMV or Aalta is installed."
              "\nIf a solver is already installed, contact the developers at "
              "josu.oca@udg.edu.")


if __name__ == '__main__':
    # start_time = time.time()
    try:
        main()
    except SolverError as error:
        raise SystemExit(f"Solver error: {error}") from error
    # prueba()
