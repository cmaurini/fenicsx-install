#!/usr/bin/env python3
"""Installation test for DOLFINx 0.11: traction of a bar with a hole.

Meshes a bar with a central hole in gmsh, solves plane-stress linear elasticity
with the left edge clamped and a traction on the right, and writes:

    output/elasticity.xdmf   displacement and stress, to open in ParaView
    output/elasticity.png    the deformed bar, stamped with machine and date

Run it with the environment active:  python elasticity.py
"""

import getpass
import os
import platform
import socket
from datetime import datetime
from pathlib import Path

import gmsh
import numpy as np
import pyvista
import ufl
from mpi4py import MPI

import dolfinx
import dolfinx.fem.petsc  # noqa: F401  -- needed for fem.petsc.LinearProblem
from dolfinx import default_scalar_type, fem, io, plot
from dolfinx.io import gmsh as gmshio  # 0.11: was dolfinx.io.gmshio

L, H, R = 200.0, 100.0, 20.0  # bar length, height, hole radius [mm]
E, NU = 70.0e3, 0.33          # Young's modulus [MPa], Poisson ratio
TRACTION = 100.0              # traction on the right end [MPa]
LEFT, RIGHT = 1, 2            # facet tags

print(f"dolfinx {dolfinx.__version__} | gmsh {gmsh.__version__} | "
      f"pyvista {pyvista.__version__} | python {platform.python_version()}")

# --- mesh: a rectangle minus a disk ----------------------------------------
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
model = gmsh.model()
model.add("bar")
model.setCurrent("bar")

surfaces, _ = model.occ.cut([(2, model.occ.addRectangle(0, 0, 0, L, H))],
                            [(2, model.occ.addDisk(L / 2, H / 2, 0, R, R))])
model.occ.synchronize()
model.addPhysicalGroup(2, [tag for _, tag in surfaces], tag=1)

# Sort the boundary curves by their centre of mass, and tag the two ends.
hole = []
for dim, tag in model.getEntities(1):
    x, y, _ = model.occ.getCenterOfMass(dim, tag)
    if np.isclose(x, 0.0):
        model.addPhysicalGroup(1, [tag], tag=LEFT)
    elif np.isclose(x, L):
        model.addPhysicalGroup(1, [tag], tag=RIGHT)
    elif np.hypot(x - L / 2, y - H / 2) < R + 1e-6:
        hole.append(tag)

# Refine towards the hole, where the stress concentrates.
model.mesh.field.add("Distance", 1)
model.mesh.field.setNumbers(1, "CurvesList", hole)
model.mesh.field.add("Threshold", 2)
model.mesh.field.setNumber(2, "InField", 1)
model.mesh.field.setNumber(2, "SizeMin", H / 48)
model.mesh.field.setNumber(2, "SizeMax", H / 12)
model.mesh.field.setNumber(2, "DistMin", R / 2)
model.mesh.field.setNumber(2, "DistMax", 2 * R)
model.mesh.field.setAsBackgroundMesh(2)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
model.mesh.generate(2)

# 0.11 returns a single MeshData object, not a (mesh, cell_tags, facet_tags) triple.
mesh_data = gmshio.model_to_mesh(model, MPI.COMM_WORLD, 0, gdim=2)
domain, facet_tags = mesh_data.mesh, mesh_data.facet_tags
gmsh.finalize()

# --- plane-stress linear elasticity ----------------------------------------
mu = E / (2 * (1 + NU))
lmbda = E * NU / (1 - NU**2)  # plane stress


def epsilon(u):
    return ufl.sym(ufl.grad(u))


def sigma(u):
    return 2 * mu * epsilon(u) + lmbda * ufl.tr(epsilon(u)) * ufl.Identity(2)


V = fem.functionspace(domain, ("Lagrange", 1, (2,)))  # vector via shape tuple
u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
ds = ufl.Measure("ds", domain=domain, subdomain_data=facet_tags)
traction = fem.Constant(domain, np.array([TRACTION, 0.0], dtype=default_scalar_type))

# Clamping the left edge removes the rigid-body modes.
domain.topology.create_connectivity(1, 2)
bc = fem.dirichletbc(np.zeros(2, dtype=default_scalar_type),
                     fem.locate_dofs_topological(V, 1, facet_tags.find(LEFT)), V)

problem = fem.petsc.LinearProblem(
    ufl.inner(sigma(u), epsilon(v)) * ufl.dx,
    ufl.inner(traction, v) * ds(RIGHT),
    bcs=[bc],
    petsc_options_prefix="elasticity_",  # required keyword in 0.11
    petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
)
uh = problem.solve()
uh.name = "displacement"

# Von Mises stress, one value per element.
s = sigma(uh) - ufl.tr(sigma(uh)) / 3 * ufl.Identity(2)
W = fem.functionspace(domain, ("DG", 0))
von_mises = fem.Function(W, name="von_Mises")
# 0.11: interpolation_points is a property, not a method.
von_mises.interpolate(fem.Expression(ufl.sqrt(3 / 2 * ufl.inner(s, s)),
                                     W.element.interpolation_points))

u_max = np.max(np.linalg.norm(uh.x.array.reshape(-1, 2), axis=1))
vm_max = np.max(von_mises.x.array)
print(f"{domain.topology.index_map(2).size_local} triangles, "
      f"{V.dofmap.index_map.size_global * V.dofmap.index_map_bs} dofs")
print(f"max |u| = {u_max:.4f} mm, max von Mises = {vm_max:.1f} MPa "
      f"(K_t = {vm_max / TRACTION:.2f}, theory ~3)")

# --- output ----------------------------------------------------------------
outdir = Path(__file__).parent / "output"
outdir.mkdir(exist_ok=True)

with io.XDMFFile(domain.comm, outdir / "elasticity.xdmf", "w") as xdmf:
    xdmf.write_mesh(domain)
    xdmf.write_function(uh)
    xdmf.write_function(von_mises)

# On headless Linux (a server, a bare WSL shell) VTK has no way to draw and
# will crash rather than raise. Say so, instead of failing obscurely.
if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
    print("no DISPLAY: if rendering crashes, install libosmesa6, "
          "or rerun as  xvfb-run -a python elasticity.py")

grid = pyvista.UnstructuredGrid(*plot.vtk_mesh(V))
values = np.zeros((grid.n_points, 3))  # pyvista wants 3 components per point
values[:, :2] = uh.x.array.real.reshape(-1, 2)
grid["displacement"] = values

factor = 0.12 * L / u_max  # scale the deformation so it is always visible
warped = grid.warp_by_vector("displacement", factor=factor)
warped.cell_data["von Mises [MPa]"] = von_mises.x.array.real
warped.set_active_scalars("von Mises [MPa]")

plotter = pyvista.Plotter(off_screen=True, window_size=(1400, 700))
plotter.add_mesh(grid.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                            manifold_edges=False, non_manifold_edges=False),
                 color="darkgrey", line_width=1.5, opacity=0.7)
plotter.add_mesh(warped, show_edges=True, edge_color="black", line_width=0.4,
                 cmap="viridis",
                 scalar_bar_args={"title": "von Mises [MPa]", "title_font_size": 16,
                                  "label_font_size": 13, "n_labels": 5,
                                  "position_x": 0.32, "position_y": 0.06,
                                  "width": 0.36, "height": 0.05})
plotter.add_text(f"{getpass.getuser()}@{socket.gethostname()}\n"
                 f"{datetime.now().astimezone():%Y-%m-%d %H:%M %Z}\n"
                 f"DOLFINx {dolfinx.__version__} - Python {platform.python_version()}",
                 position="upper_left", font_size=11, color="black")
plotter.add_text(f"bar with a hole, traction {TRACTION:g} MPa\n"
                 f"deformation scaled x{factor:.0f}",
                 position="upper_right", font_size=10, color="dimgrey")
plotter.view_xy()
plotter.camera.zoom(1.45)
plotter.set_background("white")
plotter.screenshot(outdir / "elasticity.png")
plotter.close()

print("\nSUCCESS - your DOLFINx installation works.")
print(f"  {outdir / 'elasticity.xdmf'}   open with ParaView")
print(f"  {outdir / 'elasticity.png'}    send this as proof")
