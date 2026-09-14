# Troubleshooting

Errors are grouped by where they occur. Find yours by its message.

When you ask for help, paste the version line that `elasticity.py` prints at
startup, together with the full error message.

---

## Creating the environment

### The solve never finishes, or ends in a conflict

Almost always channel priority. DOLFINx lives on `conda-forge` and must not be
mixed with the `defaults` channel:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
conda env remove -n fenicsx-0.11
conda env create -f environment.yml
```

Note that writing `channel-priority: strict` inside `environment.yml` does
nothing: conda ignores that key in an environment file. It has to be a `conda
config` command.

### `PackagesNotFoundError`, mentioning `fenics-dolfinx` or `scifem`

Either conda-forge is not enabled (see above), or you are on **native Windows**.
Several packages used here have no Windows build. Use WSL2:
[INSTALL-windows.md](INSTALL-windows.md).

### `Terms of Service have not been accepted`

You are on Anaconda's commercial channel. Switch to conda-forge as above, or
install [Miniforge](https://github.com/conda-forge/miniforge), which uses
conda-forge from the start.

### The solve is extremely slow

Older conda versions used a slow solver. Either update conda (`conda update -n
base conda`, version 23.10 and later use the fast solver by default) or install
Miniforge, which uses it already.

---

## Running the script

### `ModuleNotFoundError: No module named 'dolfinx'`

The environment is not active. Every new terminal needs:

```bash
conda activate fenicsx-0.11
```

Check you are in the right one with `conda info --envs`; the active environment
carries a `*`.

### `ImportError: cannot import name 'gmshio' from 'dolfinx.io'`

The module was renamed in DOLFINx 0.10. Tutorials written for 0.9 and earlier
still use the old name. Replace

```python
from dolfinx.io import gmshio            # 0.9 and earlier
```

with

```python
from dolfinx.io import gmsh as gmshio    # 0.10 and later
```

The alias keeps the rest of the code unchanged. There is no compatibility
shim — the old name is simply gone.

### `ValueError: too many values to unpack`, on `model_to_mesh`

Related to the same change. `model_to_mesh` used to return three values and now
returns a single object with named fields:

```python
# 0.9 and earlier
mesh, cell_tags, facet_tags = gmshio.model_to_mesh(model, comm, 0, gdim=2)

# 0.10 and later
mesh_data = gmshio.model_to_mesh(model, comm, 0, gdim=2)
mesh, cell_tags, facet_tags = mesh_data.mesh, mesh_data.cell_tags, mesh_data.facet_tags
```

`mesh_data` also carries `ridge_tags`, `peak_tags` and `physical_groups`.

### `TypeError: __init__() missing 1 required keyword-only argument: 'petsc_options_prefix'`

New in 0.11: every `LinearProblem` needs a prefix naming its PETSc options.
Any string will do, as long as it is unique within the script:

```python
problem = fem.petsc.LinearProblem(
    a, L, bcs=bcs,
    petsc_options_prefix="my_problem_",
    petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
)
```

### `AttributeError: 'FiniteElement' object has no attribute ...`, on `interpolation_points()`

It became a property. Drop the parentheses:

```python
fem.Expression(expr, V.element.interpolation_points)     # 0.11
fem.Expression(expr, V.element.interpolation_points())   # older
```

### `ModuleNotFoundError: No module named 'gmsh'`

On conda-forge the `gmsh` package is the application; the Python interface is a
separate package:

```bash
conda install -c conda-forge python-gmsh
```

Both are already listed in `environment.yml`.

### DOLFINx was silently downgraded to 0.10

Something pulled an older pin. The usual culprit is

```bash
conda install adios4dolfinx     # don't
```

conda-forge only carries `adios4dolfinx` 0.10, and installing it drags the whole
stack back. Use pip inside the activated environment instead:

```bash
pip install "adios4dolfinx>=0.11,<0.12"
```

Check what you actually have with `conda list fenics-dolfinx`.

### MPI errors, or a crash on `import dolfinx` after installing a new package

Conda-forge builds packages against a specific MPI implementation, and mixing
MPICH with OpenMPI breaks the environment beyond repair. `environment.yml` pins
`mpich` for this reason. If a later `conda install` pulled in `openmpi`, rebuild
the environment rather than trying to fix it:

```bash
conda env remove -n fenicsx-0.11
conda env create -f environment.yml
```

### `UCX ERROR ... uct_iface_open ... failed`, then MPI aborts on `import dolfinx`

Seen on cluster nodes and cloud virtual machines, not on laptops. MPICH tries
to talk to a high-speed network device (InfiniBand, or Azure's `mana_0`) that it
cannot open, and aborts before DOLFINx finishes importing. Confine it to
loopback:

```bash
export UCX_TLS=tcp,self,sm
export UCX_NET_DEVICES=lo
```

On a real cluster, prefer the site's own MPI module and ask the administrators
which transport to use; the two lines above disable fast networking.

### `unsupported PMI version PMIx. Aborting.` when using `mpirun`

Another MPI launcher is shadowing the one in the environment. This is common on
macOS when Homebrew's OpenMPI is installed: `/opt/homebrew/bin/mpirun` comes
first on the `PATH`, but `mpi4py` here is built against MPICH, and the two
launchers are not interchangeable.

Check with `which -a mpirun`. Use the environment's own launcher:

```bash
$CONDA_PREFIX/bin/mpirun -n 2 python your_script.py
```

`elasticity.py` is a serial test and does not need `mpirun` at all.

### `ld: warning: duplicate -rpath ... ignored` on macOS

Harmless. It comes from the just-in-time compiler linking the generated forms,
and does not indicate a problem.

---

## Graphics

### `libGL.so.1: cannot open shared object file`

The system OpenGL driver is missing. On Ubuntu or Debian, including WSL:

```bash
sudo apt install -y libgl1 libglx-mesa0
```

On Ubuntu 20.04 and older the second package is `libgl1-mesa-glx`.

### A black window, or a crash, when a plot opens under WSL

WSLg translates OpenGL to Direct3D and VTK does not always survive it. Force
software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

Add the line to `~/.bashrc` to make it permanent. See section 5 of
[INSTALL-windows.md](INSTALL-windows.md) for the alternatives.

### Nothing happens on `plotter.show()`, on a server or in a bare terminal

There is no display to draw on. Render to a file instead:

```python
plotter = pyvista.Plotter(off_screen=True)
...
plotter.screenshot("figure.png")
```

On a headless Linux machine — a server, or a bare WSL shell — VTK has nothing
to draw on and **crashes with a segmentation fault** rather than raising a
Python error. Give it a software renderer:

```bash
sudo apt install -y libosmesa6
```

or run the script under a virtual framebuffer:

```bash
sudo apt install -y xvfb
xvfb-run -a python elasticity.py
```

> Older tutorials call `pyvista.start_xvfb()`. That function was **removed in
> PyVista 0.48** and raises `AttributeError`, so it cannot be the fix here.

### A notebook shows an empty box instead of a 3-D plot

The Jupyter backend is not set. In the first cell:

```python
import pyvista
pyvista.set_jupyter_backend("trame")
```

If it stays empty, check that `trame`, `trame-vtk` and `trame-vuetify` are
installed (`conda list trame`), and fall back to `"static"`, which produces a
plain image.

---

## ParaView

### The XDMF file opens but shows nothing

Two things to check. Pick the **Xdmf3** reader when ParaView offers a choice —
the older Xdmf2 reader fails on these files. And remember to press **Apply**
after opening: ParaView shows nothing until you do.

### `elasticity.xdmf` alone will not open

The `.xdmf` file is only an index; the data sits in `elasticity.h5` beside it.
Keep the two together when you copy results around.

### The bar looks undeformed

The displacements are a fraction of a millimetre on a 200 mm bar, so they are
invisible at true scale. Add a **Warp By Vector** filter on `displacement` and
raise the *Scale Factor* to around 50.

---

## Still stuck

Open an issue, or write to the teacher, including:

- the version line printed by `elasticity.py`;
- the complete error message, not just its last line;
- your operating system, and whether you are using WSL;
- the output of `conda list fenics-dolfinx gmsh pyvista`.
