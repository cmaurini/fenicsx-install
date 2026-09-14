# Installing DOLFINx 0.11 with conda — Linux and macOS

These instructions cover Linux and macOS (both Intel and Apple Silicon).
On Windows, start from [INSTALL-windows.md](INSTALL-windows.md) instead: it sets
up WSL2 and then sends you back here.

Allow about twenty minutes, most of it unattended while conda downloads.

---

## 1. Prerequisites

Install these before touching conda.

### macOS

The Command Line Tools provide `git` and the compilers. In a terminal:

```bash
xcode-select --install
```

A dialog appears; accept it. If the tools are already present the command says
so and does nothing.

[Homebrew](https://brew.sh) is not required, but it is the easiest way to install
ParaView later. To install it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Linux (Ubuntu or Debian)

```bash
sudo apt update
sudo apt install -y build-essential curl git
```

PyVista also needs an OpenGL driver from the system. conda ships the OpenGL
*client* libraries, but not a driver, so install Mesa:

```bash
sudo apt install -y libgl1 libglx-mesa0
```

On Ubuntu 20.04 and older that second package is called `libgl1-mesa-glx`.

If you work on a machine with no screen at all — a compute server, or a bare WSL
shell — add a virtual framebuffer as well:

```bash
sudo apt install -y xvfb
```

On Fedora or RHEL the equivalents are `gcc-c++`, `git`, `mesa-libGL` and
`xorg-x11-server-Xvfb`.

---

## 2. Install conda

We recommend **Miniforge**, not Anaconda. Miniforge is smaller, already uses the
`conda-forge` channel where DOLFINx lives, and avoids the Anaconda licence
prompt that the commercial distribution now shows.

Download and run the installer for your platform:

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

Accept the defaults, and answer **yes** when it offers to initialise your shell.
Then close and reopen the terminal. You should see `(base)` at the start of your
prompt:

```bash
conda --version
```

If you already have Anaconda or Miniconda installed you do not need to replace
it. Just make sure conda-forge takes priority:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

That second line matters. Without strict priority conda mixes packages from
different channels and the environment either fails to solve or breaks at
import time.

---

## 3. Get the repository

```bash
git clone https://github.com/cmaurini/fenicsx-install.git
cd fenicsx-install
```

Without git, download the ZIP from the repository page and unzip it.

---

## 4. Create the environment

```bash
conda env create -f environment.yml
```

This downloads roughly 2 GB and takes five to fifteen minutes. Then activate it:

```bash
conda activate fenicsx-0.11
```

`(fenicsx-0.11)` should now appear at the start of your prompt. **You must run
this `conda activate` command in every new terminal**, before running any script.

Check that DOLFINx imports and reports the right version:

```bash
python -c "import dolfinx; print(dolfinx.__version__)"
```

```
0.11.0
```

> The UFL package inside this environment is numbered `2026.1.0`, not `0.11.x`.
> That is normal: UFL uses its own release calendar.

---

## 5. Run the test

```bash
python elasticity.py
```

It prints the installed versions, meshes a bar with a hole, solves a linear
elasticity problem, and writes `output/elasticity.xdmf` and
`output/elasticity.png`:

```
dolfinx 0.11.0 | gmsh 4.15.2 | pyvista 0.48.4 | python 3.12.x
2237 triangles, 2374 dofs
max |u| = 0.3527 mm, max von Mises = 331.9 MPa (K_t = 3.32, theory ~3)

SUCCESS - your DOLFINx installation works.
```

Open the image to confirm that it shows a deformed bar carrying your own machine
name and today's date:

```bash
open output/elasticity.png        # macOS
xdg-open output/elasticity.png    # Linux
```

Send that PNG as proof that your installation works.

If anything failed, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 6. Install ParaView

The PNG is only a snapshot. [ParaView](https://www.paraview.org) is the tool for
actually exploring the `.xdmf` results: slicing, deforming, plotting along lines.
It is a separate desktop application, not a Python package.

**macOS**

```bash
brew install --cask paraview
```

or download the `.dmg` from <https://www.paraview.org/download/>. On Apple
Silicon pick the ARM build.

**Linux**

Download the `.tar.gz` from <https://www.paraview.org/download/> and unpack it;
the version packaged by `apt` is usually several years old. To use `apt` anyway:

```bash
sudo apt install -y paraview
```

**With conda, as an alternative**

ParaView is also on conda-forge and coexists with this environment:

```bash
conda install -c conda-forge paraview
```

This is convenient on a machine where you cannot install desktop software, but
it pulls in Qt and a second copy of VTK — roughly 500 MB. Prefer the native
application when you can.

### Opening the results

Launch ParaView, open `output/elasticity.xdmf`, and choose the **Xdmf3** reader
if asked. Press *Apply*. Then:

1. Add a **Warp By Vector** filter, set *Vectors* to `displacement` and the
   *Scale Factor* to something like `50`, and press *Apply*.
2. In the colour dropdown, pick `von_Mises`.

You should see the stress concentrating at the top and bottom of the hole.

---

## Keeping the environment up to date

If `environment.yml` changes:

```bash
conda env update -f environment.yml --prune
```

To start over from scratch:

```bash
conda deactivate
conda env remove -n fenicsx-0.11
conda env create -f environment.yml
```

## Working in JupyterLab

```bash
conda activate fenicsx-0.11
jupyter lab
```

For interactive 3-D plots inside a notebook, select the trame backend:

```python
import pyvista
pyvista.set_jupyter_backend("trame")
```
