# Guide for AI coding assistants

This file is for an AI assistant helping someone install DOLFINx 0.11 from this
repository. It is not needed by human readers, who should start at
[README.md](README.md).

If you are such an assistant: work through the diagnosis below rather than
guessing, prefer the documented fix to an invented one, and never modify the
user's environment without telling them what you are about to run.

## What this repository is

Installation instructions and a self-test for **DOLFINx 0.11.0**, for students
of a solid mechanics course. The deliverable for the student is
`output/elasticity.png`, which they send to their teacher as proof of a working
installation.

| File | Role |
|---|---|
| `environment.yml` | the single conda environment, used on Linux, macOS and WSL |
| `elasticity.py` | the self-test: gmsh → DOLFINx → PETSc → XDMF + PyVista |
| `INSTALL-conda.md` | Linux and macOS |
| `INSTALL-windows.md` | WSL2 + conda, plus a Docker appendix |
| `TROUBLESHOOTING.md` | the error-by-error reference; consult it first |
| `docker/Dockerfile` | container based on `ghcr.io/fenics/dolfinx/lab:v0.11.0` |

## Establish the situation before advising

Ask, or determine, these four things. Most wrong advice comes from skipping them.

1. **Operating system**, and on Windows whether they are inside WSL or in
   PowerShell. Native Windows is not supported here: several required packages
   have no Windows build. The answer is WSL2.
2. **Which conda**, via `conda info --envs` and `conda config --show channels`.
   Miniforge is expected. An Anaconda install without conda-forge at strict
   priority is the single most common cause of a failing environment creation.
3. **Whether the environment is active.** `(fenicsx-0.11)` in the prompt, or a
   `*` next to it in `conda info --envs`. A great many "DOLFINx is broken"
   reports are an unactivated environment.
4. **The exact error**, in full. Ask for the whole traceback, not its last line.

The fastest single diagnostic is to run the test script, which prints its
versions on the first line, before doing any work:

```bash
conda run --no-capture-output -n fenicsx-0.11 python elasticity.py
```

```
dolfinx 0.11.0 | gmsh 4.15.2 | pyvista 0.48.4 | python 3.12.x
```

That line appears even when the run fails later, so it is worth asking for
first. For the optional packages, `conda list -n fenicsx-0.11` shows everything.

## Verification commands

```bash
conda env list                                        # does the env exist
conda list -n fenicsx-0.11 fenics-dolfinx gmsh pyvista
conda run -n fenicsx-0.11 python -c "import dolfinx; print(dolfinx.__version__)"
```

Expect `0.11.0`. Anything starting `0.10` or `0.9` means a downgrade happened;
see the `adios4dolfinx` entry in `TROUBLESHOOTING.md`.

To test a change to `environment.yml` without spending twenty minutes on it:

```bash
conda env create -f environment.yml -n scratch-check --dry-run
```

## Version facts, current as of DOLFINx 0.11.0

Assistants routinely produce code for DOLFINx 0.9, which is what most tutorials
and most training data contain. These three changes account for nearly every
such failure:

| Older API | 0.11 |
|---|---|
| `from dolfinx.io import gmshio` | `from dolfinx.io import gmsh as gmshio` — renamed, no compatibility alias |
| `mesh, ct, ft = model_to_mesh(...)` | returns one `MeshData` namedtuple: `.mesh`, `.cell_tags`, `.facet_tags`, `.ridge_tags`, `.peak_tags`, `.physical_groups` |
| `LinearProblem(a, L, bcs=...)` | `petsc_options_prefix=` is a required keyword-only argument |

Also worth knowing:

- `V.element.interpolation_points` is a **property**; older code calls it.
- `fem.functionspace` is lowercase, and vector spaces are built with a shape
  tuple: `fem.functionspace(mesh, ("Lagrange", 1, (2,)))`. `VectorFunctionSpace`
  no longer exists.
- `dolfinx.fem.petsc` must be imported explicitly.
- UFL in this stack is numbered **2026.1.0**, not `0.11.x`. This is correct and
  not a version mismatch.
- Use `u.x.petsc_vec`, not `u.vector`.

Before writing DOLFINx code from memory, check it against the installed version:

```bash
conda run -n fenicsx-0.11 python -c "import dolfinx.io.gmsh as g, inspect; print(inspect.signature(g.model_to_mesh))"
```

## Things not to do

- **Do not `pip install fenics-dolfinx`.** It is not on PyPI. DOLFINx comes from
  conda-forge, or from a container.
- **Do not `conda install adios4dolfinx`.** conda-forge carries only the 0.10
  build and it will silently downgrade the whole stack. Use
  `pip install "adios4dolfinx>=0.11,<0.12"` inside the activated environment.
- **Do not mix MPI implementations.** `environment.yml` pins `mpich`; pulling in
  `openmpi` breaks the environment past repair. Rebuild rather than patch.
- **Do not add `channel-priority: strict` to `environment.yml`.** conda ignores
  that key in an environment file. It must be `conda config --set
  channel_priority strict`.
- **Do not relax the `python>=3.11,<3.13` pin** without checking: `scifem` has no
  build outside that range.
- **Do not suggest native Windows conda**, or an X server such as VcXsrv for
  WSL. WSLg has replaced the latter.
- Avoid editing a student's working environment to chase an error. Where the
  environment is genuinely damaged, removing and recreating it is faster and
  more reliable than repairing it.

## Graphics, the other common failure

PyVista rendering fails differently on each platform, and the fix depends on the
situation rather than the message alone:

- `libGL.so.1` missing → `sudo apt install -y libgl1 libglx-mesa0`. conda ships
  the OpenGL client libraries but not a driver.
- Black window or crash under WSL → `export LIBGL_ALWAYS_SOFTWARE=1`.
- No display at all (server, CI, bare shell) → `sudo apt install libosmesa6`,
  or run under `xvfb-run -a`. VTK segfaults here rather than raising, so a
  crash with no traceback usually means this. Note that `pyvista.start_xvfb()`
  was **removed in PyVista 0.48**: do not suggest it.
- Empty box in a notebook → `pyvista.set_jupyter_backend("trame")`.

`elasticity.py` already handles the headless cases, so if *it* renders but the
student's own script does not, the difference is in their script rather than the
installation.

## When the installation is fine

If `elasticity.py` reports `SUCCESS` and writes both files, the installation is
complete. The reported stress concentration factor should be near 3.3 — close to
the textbook value of 3 for a circular hole under uniform tension — which makes
it a check on the numerics as well as the plumbing. Tell the student to send
`output/elasticity.png`.
