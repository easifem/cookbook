# FEDOF: H1 DOF numbering and offset arrays

This note explains how `FEDOF_` numbers H1 degrees of freedom and how the
`edgeIA`, `faceIA` and `cellIA` offsets are built. It covers conforming
and broken H1 spaces.

## Blocks in global order

A conforming H1 space numbers its DOFs in four blocks:

| Block | Range | Order inside the block |
|---|---|---|
| vertex | `1:N_v` | mesh-local vertex number |
| edge interior | after the vertices | increasing edge number |
| face interior | after the edges | increasing face number |
| cell interior | after the faces | local cell order |

`N_v` is the number of shared vertex DOFs: the mesh vertex nodes for a
conforming space, zero for a broken space.

## Cumulative offsets

Each entity owns a half-open range. For entity counts `n_i` and the first
DOF `b` of the block:

$$ I_1 = b, \qquad I_{i+1} = I_i + n_i $$

Entity `i` owns `IA(i):IA(i+1)-1`. Equal neighbouring offsets mean an
empty block. `cellIA(N_c+1)` is `tdof + 1`, so `tdof` is the last offset
minus one. Each array has one more entry than its entity count.

- `edgeIA` has size `N_e + 1` and starts at `N_v + 1`.
- `faceIA` has size `N_f + 1` and starts at the last edge offset.
- `cellIA` has size `N_c + 1` and starts at the last face offset.

The code counts entities before it builds offsets. `obj_SetFedofForH1`
first stores the count of each edge, face and cell once, then accumulates
in increasing entity number. An entity with no active incident cell gets
an empty range.

## Local counts for conforming H1 at uniform order p

| Topology | Vertices | Edge interiors | Face interiors | Cell interior |
|---|---|---|---|---|
| triangle | 3 | 3(p-1) | 0 | (p-1)(p-2)/2 |
| quadrangle | 4 | 4(p-1) | 0 | (p-1)^2 |

In two dimensions the mesh facets are lines: the edge block is empty and
line-interior DOFs are stored in the face block, `p-1` per line. In
three dimensions edges and faces both carry DOFs; a hexahedron face has
`(p-1)^2`.

For a uniform space on a two-dimensional mesh:

$$ n_{dof} = N_v + N_f (p-1) + \sum_K n_{int}(p) $$

`H1Numbering_test_1` checks this on adjacent two-cell meshes:

| Mesh | p=1 | p=2 | p=3 |
|---|---|---|---|
| two triangles (`N_v=4`, `N_f=5`) | 4 | 9 | 16 |
| two quadrangles (`N_v=6`, `N_f=7`) | 6 | 15 | 28 |

## Element connectivity order

`GetConnectivity(opt="All")` writes vertex, edge, face and cell DOFs in
that order. Only the first letter of `opt` is used. `GetConnectivity_`
writes the same values into a preallocated array and returns `tsize`;
size that array with `GetMaxTotalConnectivity()`.

## Variable orders

For a conforming space the order of a shared facet is the minimum order
of its cells, `p_e = MIN(p_K, p_L)`, so it owns `p_e - 1` interior DOFs.
The cell interior keeps its own order `p_K`. Only hierarchical H1 applies
this trace reduction in the current code; variable-order Lagrange
constraints are not provided.

## Broken spaces

With `isBrokenSpace=.TRUE.` no entity is shared:

- `N_v = 0`, and every edge and face offset is one (empty);
- each active cell owns a disjoint block, starting at DOF one, in local
  cell order;
- the block is the complete local basis: `(p+1)(p+2)/2` for a triangle
  and `(p+1)^2` for a quadrangle, including `p=0`, which gives one DOF;
- `tdof` is the sum of the active cell block sizes.

`GetConnectivity(opt="All")` and `GetCellDOF` return the owning-cell
block. `GetVertexDOF`, `GetEdgeDOF` and `GetFaceDOF` return `tsize=0`.
`GetFacetConnectivity_` returns the full cell block for every local
facet.

## Mapping to the implementation

| Routine | Role |
|---|---|
| `obj_AllocateSizes` | allocate orders and offsets; zero `tNodes` if broken |
| `obj_Set` | dispatch H1 or broken numbering |
| `obj_SetFedofForH1` | count entities once, then build cumulative offsets |
| `obj_SetFedofForH1Broken` | count full cell bases, build cell blocks |
| `obj_GetVertexDOF` | one DOF (local node number) or zero |
| `obj_GetEdgeDOF1` | `edgeIA` range |
| `obj_GetFaceDOF1` | `faceIA` range |
| `obj_GetCellDOF` | `cellIA` range |
| `obj_GetTotalDOF1` | `tdof` |
| `obj_GetTotalDOF2`, `obj_GetTotalDOF3` | DOFs of one element, per entity |
| `obj_SetFE`, `obj_GetFEPointer` | configure and return the local FE |

Interface: `classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

Tests: `classes:src/modules/FEDOF/examples/H1Numbering_test_1.F90`,
`classes:src/modules/FEDOF/examples/H1Connectivity_test_1.F90`,
`classes:src/modules/FEDOF/examples/H1VariableOrder_test_1.F90`,
`classes:src/modules/FEDOF/examples/DGNumbering_test_1.F90`.
