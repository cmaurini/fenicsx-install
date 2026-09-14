# Image for the DOLFINx 0.11 installation test, built on the official DOLFINx
# JupyterLab image.
#
# Build from the root of the repository:
#   docker build -t fenicsx-install -f docker/Dockerfile .
#
# Run, mounting the current directory:
#   docker run --rm -ti -v $(pwd):/root/shared -w /root/shared --init -p 8888:8888 fenicsx-install
#
# On Windows use ${PWD} in PowerShell, or %cd% in cmd.exe, instead of $(pwd).

FROM ghcr.io/fenics/dolfinx/lab:v0.11.0

# System libraries PyVista needs to render without a screen.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-dev libxrender1 libxcursor1 xvfb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -U pip setuptools

# vtk must go in before pyvista, so pyvista binds to this build.
RUN python3 -m pip install --no-cache-dir vtk && \
    python3 -m pip install --no-cache-dir \
        "pyvista[all]>=0.48" gmsh plotly pandas tqdm rich jupytext && \
    python3 -m pip cache purge

# Render off-screen through the software rasteriser: there is no GPU in a
# container, and no display attached to it.
ENV PYVISTA_OFF_SCREEN=true
ENV PYVISTA_JUPYTER_BACKEND=trame
ENV LIBGL_ALWAYS_SOFTWARE=1

WORKDIR /root/shared
EXPOSE 8888/tcp
ENTRYPOINT ["jupyter", "lab", "--ip", "0.0.0.0", "--no-browser", "--allow-root"]
