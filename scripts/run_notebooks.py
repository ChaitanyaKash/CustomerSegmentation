"""Execute both notebooks sequentially using the current Python environment."""
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('CUSTOMERSEG_PAUSE_FILE', str(ROOT / 'thermal.pause'))
for variable in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[variable] = '2'


def run():
    for path in sorted(ROOT.glob('0*.ipynb')):
        notebook = nbformat.read(path, as_version=4)
        manager = KernelManager(kernel_name='python3')
        # Avoid accidentally executing in a different globally installed Python.
        manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']

        def started(cell, cell_index, **kwargs):
            print(f'{path.name}: cell {cell_index}: {cell.source.splitlines()[0][:90]}', flush=True)

        def completed(cell, cell_index, **kwargs):
            nbformat.write(notebook, path)
            for output in cell.get('outputs', []):
                if output.output_type == 'stream':
                    print(output.text, flush=True)

        client = NotebookClient(notebook, km=manager, timeout=3600,
                                resources={'metadata': {'path': str(ROOT)}},
                                on_cell_start=started, on_cell_executed=completed)
        try:
            client.execute(cwd=str(ROOT))
        finally:
            nbformat.write(notebook, path)
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
        print('PASS:', path.name, flush=True)


if __name__ == '__main__':
    run()
