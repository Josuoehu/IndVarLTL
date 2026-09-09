import os
import re
import subprocess
import tempfile
from pathlib import Path

from project_paths import FILES_DIR, PROJECT_ROOT, SCRIPTS_DIR, resolve_from_scripts


class SolverError(RuntimeError):
    """Raised when an external solver cannot execute a query reliably."""


def _new_output_path(out_name, suffix):
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(out_name))
    descriptor, file_name = tempfile.mkstemp(
        prefix=f'{safe_name}_', suffix=suffix, dir=PROJECT_ROOT
    )
    os.close(descriptor)
    output_path = Path(file_name)
    output_path.unlink()
    return output_path


def _run(command, cwd=SCRIPTS_DIR):
    try:
        completed = subprocess.run(
            [str(part) for part in command],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise SolverError(f"Could not start solver: {exc}") from exc

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise SolverError(
            f"Solver exited with status {completed.returncode}:\n{output.strip()}"
        )
    if re.search(
        r"(?:\b(?:syntax|parse) error\b|\*\*\* error\b|\berror:)",
        output,
        re.IGNORECASE,
    ):
        raise SolverError(f"Solver rejected the generated input:\n{output.strip()}")
    return completed


def call_get_path(is_linux, is_nusmv):
    search_root = '/home' if is_linux else '/Users'
    executable = 'NuSMV' if is_nusmv else 'aalta'
    _run([SCRIPTS_DIR / 'get_path.sh', search_root, executable])


def call_nusmv_bounded(script, expression, out_name, bound):
    output_path = _new_output_path(out_name, '.xml')
    command = (
        f'go_bmc;check_ltlspec_bmc -p "{expression}" -k {bound}; '
        f'show_traces -p 4 -o "{output_path}";quit'
    )
    try:
        _run([SCRIPTS_DIR / 'call_nusmv.sh', command, resolve_from_scripts(script)])
    except SolverError:
        output_path.unlink(missing_ok=True)
        raise
    return output_path


def call_nusmv(script, expression, out_name):
    output_path = _new_output_path(out_name, '.xml')
    command = (
        f'go;check_ltlspec -p "{expression}"; '
        f'show_traces -p 4 -o "{output_path}";quit'
    )
    try:
        _run([SCRIPTS_DIR / 'call_nusmv.sh', command, resolve_from_scripts(script)])
    except SolverError:
        output_path.unlink(missing_ok=True)
        raise
    return output_path


def call_aalta(input_file, out_name):
    input_path = Path(input_file)
    if not input_path.is_absolute():
        input_path = FILES_DIR / input_path
    output_path = Path(out_name)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(
        prefix='indvar_aalta_', dir=PROJECT_ROOT
    ) as working_directory:
        try:
            _run(
                [SCRIPTS_DIR / 'call_aalta.sh', input_path, output_path],
                cwd=working_directory,
            )
        except SolverError:
            output_path.unlink(missing_ok=True)
            raise
    if not output_path.exists():
        raise SolverError("Aalta did not create its result file")
    return output_path


def main():
    call_aalta('exten.dimacs', 'res_exten.txt')


if __name__ == '__main__':
    main()
