# FEDOF: Broken (discontinuous) spaces

**Purpose.** Number a broken space, where every cell owns its complete
local basis, and query its connectivity and matrix pattern.

**Classes.** `FEDOF_` (`FEDOF_Class`), `FEDomain_` (`FEDomain_Class`),
`HDF5File_` (`HDF5File_Class`); `CSRMatrix_` for the pattern. Interface:
`classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

## Steps

1. Use `baseContinuity="H1"` with `isBrokenSpace=.TRUE.`. The broken
   space is a flag, not a `DG` continuity string.
2. Number the cells. Every active cell owns a contiguous block in local
   cell order, and `GetTotalDOF()` is the sum of the block sizes. A block
   is the full local basis:

   | Topology | DOFs at order p |
   |---|---|
   | triangle | `(p+1)(p+2)/2` |
   | quadrangle | `(p+1)^2` |

   `p=0` gives one DOF (the cell centroid).
3. Query connectivity. `GetConnectivity(opt="All")` and
   `GetCellDOF(globalCell=...)` return the owning-cell block.
   `GetFacetConnectivity_` returns the same full block for every local
   facet, because a trace uses all cell DOFs.

```fortran
USE BaseType, ONLY: TypeInterpolationOpt
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B

TYPE(FEDOF_) :: obj
TYPE(FEDomain_) :: dom
INTEGER(I4B) :: orders(2)
INTEGER(I4B), ALLOCATABLE :: con(:)

orders = [0, 2]
CALL obj%Initiate(order=orders, islocal=.TRUE., dom=dom, &
                  baseContinuity="H1", isBrokenSpace=.TRUE., &
                  baseInterpolation="Lagrange", &
                  ipType=TypeInterpolationOpt%Equidistance)

con = obj%GetConnectivity(opt="All", globalElement=101)
! contiguous block of the cell; adjacent cells share no DOF
```

4. Shared entities own nothing. `GetTotalVertexDOF()` is zero, and
   `GetVertexDOF`, `GetEdgeDOF` and `GetFaceDOF` return `tsize=0`.
5. Call `SetFE` then `GetFEPointer` for the local FE; its
   `GetTotalDOF()` equals the cell block size.
6. Call `SetSparsity(mat=...)`: a broken space connects each cell block
   to itself and to its active neighbour cells.

## Example files (run from the examples directory)

- `classes:src/modules/FEDOF/examples/DGNumbering_test_1.F90`
- `classes:src/modules/FEDOF/examples/DGTrace_test_1.F90`
- `classes:src/modules/FEDOF/examples/GetConnectivity_test_5.F90`
- `classes:src/modules/FEDOF/examples/SetSparsity_test_1.F90`

`DGNumbering_test_1` checks the block sizes above for order pairs
`(0,0) (1,1) (2,2) (3,3) (1,3) (3,1) (0,2) (2,0)`, that blocks are
contiguous, that adjacent cells share no DOF, and that a degree-zero
basis is constant. On the four-quadrangle fixture, order 1 gives 16 DOFs
and 192 nonzeros; order 2 gives 972 nonzeros (`SetSparsity_test_5`).

## Pitfalls

- Do not add `N_v` shared vertex DOFs. Vertex-position nodal values
  belong to the owning cell block, even when their interpolation points
  coincide with mesh vertices.
- Stored `faceOrder` and `edgeOrder` are zero in a broken space.
  `GetOrders` returns the cell order for every local face and edge.
- Inactive cells have empty block ranges.
- Global cell IDs need not be contiguous (the fixtures use 101 and 205);
  block order follows local cell order.
- A Lagrange space needs `ipType`; for a broken Lagrange space pass it
  together with `isBrokenSpace=.TRUE.`.
- A broken space accepts cell order zero (one constant DOF); do not
  assume the same for a conforming H1 space.
- `GetTotalDOF()` and `GetSumElemTotalDOF()` agree for a broken space,
  because no DOF is shared.
