# Installing DOLFINx 0.11 on Windows

DOLFINx is a Linux library. The reliable way to use it on Windows is **WSL2**,
the Windows Subsystem for Linux: a real Ubuntu running inside Windows, sharing
your files and your desktop. You install it once, then follow exactly the same
conda instructions as everyone else.

Docker is documented as an alternative in the [appendix](#appendix-docker) at the
end, but WSL2 is what we recommend and what we support.

> Conda packages of DOLFINx for native Windows do exist, but several of the
> packages used in this course have no Windows build. Use WSL2.

Allow about thirty minutes, most of it unattended.

---

## 1. Install WSL2

Open **PowerShell as Administrator** (right-click the Start button → *Terminal
(Admin)*) and run:

```powershell
wsl --install -d Ubuntu
```

Restart the computer when asked. After the restart Ubuntu opens by itself and
asks for a username and password. These are for Linux only and have nothing to
do with your Windows account; the password is invisible as you type it.

If WSL was already installed, bring it up to date — this also enables the
graphics support used further down:

```powershell
wsl --update
```

From now on, "the terminal" means the **Ubuntu** window, which you can reopen at
any time from the Start menu. Commands typed there are Linux commands.

Check that you are on version 2:

```powershell
wsl -l -v
```

The `VERSION` column must read `2`. If it says `1`, run
`wsl --set-version Ubuntu 2`.

---

## 2. Prerequisites, inside Ubuntu

In the Ubuntu terminal:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git
```

PyVista needs an OpenGL driver from the system. conda ships the OpenGL client
libraries but not a driver, so install Mesa as well:

```bash
sudo apt install -y libgl1 libglx-mesa0 libxrender1 libxcursor1
```

You will be asked for the Linux password you chose in step 1.

---

## 3. Install conda and create the environment

From here the instructions are identical to Linux, because inside WSL you *are*
on Linux. **Follow [INSTALL-conda.md](INSTALL-conda.md) from section 2
("Install conda") onwards**, typing everything in the Ubuntu terminal.

Two Windows-specific points before you go:

**Keep your files in the Linux home directory.** Clone the repository under `~`,
not under `/mnt/c/Users/...`. Files on the Windows side are reachable from Linux,
but every read crosses a translation layer and meshing or assembly can become
several times slower.

```bash
cd ~
git clone https://github.com/cmaurini/fenicsx-install.git
cd fenicsx-install
```

**To reach those files from Windows**, type this in the Ubuntu terminal:

```bash
explorer.exe .
```

A normal Explorer window opens on the current directory. You can also type
`\\wsl$` in the Explorer address bar, or use the *Linux* entry in its sidebar.

---

## 4. Run the test

```bash
conda activate fenicsx-0.11
python elasticity.py
```

Then open the resulting image from Windows:

```bash
explorer.exe output
```

Double-click `elasticity.png`. It should show a deformed bar with your machine
name and today's date in the corner. Send that file as proof that your
installation works.

---

## 5. Visualising with PyVista under WSL

Drawing 3-D graphics from inside WSL is the one place where Windows differs in
practice. Three approaches, from the most reliable to the least. **Start with the
first one.**

### a. In a notebook, viewed in your Windows browser — recommended

Rendering happens inside WSL and the result is served over HTTP. WSL2 forwards
`localhost` to Windows automatically, so your ordinary Windows browser can open
it. No graphics driver is involved, which is why this is the robust option.

```bash
conda activate fenicsx-0.11
jupyter lab
```

Ctrl-click the `http://localhost:8888/...` link printed in the terminal. In a
notebook cell:

```python
import pyvista
pyvista.set_jupyter_backend("trame")   # interactive; "static" gives a flat image
```

The plots are then fully interactive — rotate, zoom, pick — inside the notebook.

### b. Render to a file

This is what `elasticity.py` does, and it always works, including over SSH on a
machine with no screen at all:

```python
plotter = pyvista.Plotter(off_screen=True)
plotter.add_mesh(grid)
plotter.screenshot("figure.png")
```

Then `explorer.exe .` and open the image. For something interactive without a
notebook, write a self-contained web page instead and open it in your browser:

```python
plotter.export_html("figure.html")
```

### c. A real window on your desktop

Modern WSL includes **WSLg**, which lets Linux applications open ordinary
Windows windows. `plotter.show()` then behaves as it would on Linux — no X
server such as VcXsrv, and no `DISPLAY` variable to set.

```python
plotter = pyvista.Plotter()
plotter.add_mesh(grid)
plotter.show()
```

This requires Windows 11, or a recent Windows 10, and `wsl --update` from
PowerShell if you have not run it lately.

If the window stays black, flickers, or the program crashes when it opens:
WSLg routes OpenGL through a Direct3D translation layer that VTK does not always
tolerate. Force software rendering instead — slower, but correct:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

To make that permanent, append it to `~/.bashrc`.

---

## 6. Install ParaView

Install ParaView **on Windows**, not inside WSL: you get a proper native
application, hardware accelerated, and it can read the files in your WSL home
directory directly.

Download the Windows installer from <https://www.paraview.org/download/> and run
it. Then open `output/elasticity.xdmf` through the Explorer window that
`explorer.exe output` gives you, or by typing a path like

```
\\wsl$\Ubuntu\home\<your-linux-username>\fenicsx-install\output
```

into ParaView's file dialog.

Choose the **Xdmf3** reader if asked, press *Apply*, then add a **Warp By
Vector** filter on `displacement` and colour it by `von_Mises`. See section 6 of
[INSTALL-conda.md](INSTALL-conda.md) for details.

---

## Appendix: Docker

An alternative if WSL2 cannot be installed, for instance on a managed machine
where you are not administrator — though note that Docker Desktop itself needs
WSL2 or Hyper-V underneath.

1. Install [Docker Desktop](https://docs.docker.com/get-docker/).
2. Build the image, from the root of this repository, in PowerShell:

   ```powershell
   docker build -t fenicsx-install -f docker/Dockerfile .
   ```

3. Start a container with the current directory mounted:

   ```powershell
   docker run --rm -ti -v ${PWD}:/root/shared -w /root/shared --init -p 8888:8888 fenicsx-install
   ```

   `${PWD}` is the PowerShell spelling. In `cmd.exe` write `%cd%`, and in a
   Linux or macOS shell `$(pwd)`.

4. Open one of the `http://127.0.0.1:8888/...` links printed in the terminal.

Files written inside `/root/shared` appear in the directory you started from, so
`output/elasticity.png` lands on your Windows disk as usual. Step 2 is only
needed the first time.

Inside the container PyVista must render off-screen, which the image is already
configured for. Interactive notebook plots work through the trame backend as in
section 5a.
