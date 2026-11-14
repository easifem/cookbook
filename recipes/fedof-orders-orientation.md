# FEDOF: Orders and orientations of an element

**Purpose.** Ask a `FEDOF_` for the polynomial order of a cell, its faces
and its edges, and for the mesh orientation flags, without querying the
mesh yourself.

**Classes.** `FEDOF_` (`FEDOF_Class`), `FEDomain_`
(`FEDomain_Class`), `AbstractMesh_` (`AbstractMesh_Class`). Interface:
`classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

## Steps

1. Initiate the `FEDOF_` as usual. With a uniform order every cell gets
   that order; with an order array the cells can differ (see
   `recipes/fedof-variable-order-h1.md`).
2. Pick the query. Each call takes `globalElement` and an optional
   `islocal`; the output array is written from its first entry.

   | Call | Writes | Size outputs |
   |---|---|---|
   | `GetCellOrder` | `ans(1)` = cell order | `tsize = 1` |
   | `GetFaceOrder` | `ans(1:3, 1:ncol)` | `nrow = 3` |
   | `GetEdgeOrder` | `ans(1:tsize)` | number of local edges |
   | `GetOrders` | all six arrays at once | six size arguments |

3. `GetFaceOrder` writes three identical rows per face: `ans(1, jj)`,
   `ans(2, jj)` and `ans(3, jj)` all hold the order of face `jj`. `ncol`
   is the number of local faces.
4. `GetOrders` fills orders and orientations in one call:

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B

TYPE(FEDOF_) :: obj
TYPE(FEDomain_) :: dom
INTEGER(I4B) :: cellOrder(3), faceOrder(3, 10), edgeOrder(20), &
                cellOrient(3), faceOrient(3, 10), edgeOrient(20), &
                tCellOrder, tFaceOrder, tEdgeOrder, tCellOrient, &
                tFaceOrient(2), tEdgeOrient, iel

CALL obj%Initiate(baseContinuity="H1", baseInterpolation="Hierarchical", &
                  order=2, dom=dom)

CALL obj%GetOrders(cellOrder=cellOrder, faceOrder=faceOrder, &
                   edgeOrder=edgeOrder, cellOrient=cellOrient, &
                   faceOrient=faceOrient, edgeOrient=edgeOrient, &
                   tCellOrder=tCellOrder, tFaceOrder=tFaceOrder, &
                   tEdgeOrder=tEdgeOrder, tCellOrient=tCellOrient, &
                   tFaceOrient=tFaceOrient, tEdgeOrient=tEdgeOrient, &
                   globalElement=iel, islocal=math%yes)
```

5. Read the orientation flags. `cellOrient` is three entries, all `1` in
   the current implementation. `edgeOrient` is `+1` when the edge's first
   node has the lower global node number, else `-1`. A 2D face (a line)
   has one flag, a 3D face has three; always use `tFaceOrient(1)` for the
   row count and size the array with at least three rows.
6. Two cells see a shared facet with opposite flags. `SetFE` passes the
   flags to the finite element, and the basis traces then agree from both
   cells.

## Example files (run from the examples directory)

- `classes:src/modules/FEDOF/examples/GetOrders_test_1.F90`
- `classes:src/modules/FEDOF/examples/GetOrders_test_2.F90`
- `classes:src/modules/FEDOF/examples/GetFaceOrder_test_1.F90`
- `classes:src/modules/FEDOF/examples/GetCellOrder_test_1.F90`
- `classes:src/modules/FEDOF/examples/H1Orientation_test_1.F90`
- `classes:src/modules/FEDOF/examples/H1VariableOrder_test_1.F90`

`GetOrders_test_1` runs order 2 hierarchical on the four-quadrangle mesh:
every element reports `tCellOrder = 1` with `cellOrder(1) = 2`, and
`tFaceOrder = 4` with all three rows equal to 2. `GetFaceOrder_test_1`
checks a hexahedron at order 2: `nrow = 3`, `ncol = 6`, `tsize = 12` for
the edges, and every face and edge order is 2. `GetOrders_test_2` runs
order 2 on a triangle and a hexahedron in a broken space and still gets
`cellOrder(1) = 2` and the cell order for every face (and for every edge
of the hexahedron).
`H1Orientation_test_1` checks that two cells sharing a facet have
`orientation(1) * orientation(2) = -1` and matching basis traces.

## Pitfalls

- `faceOrder` is three identical rows, not one row per face node. Read a
  face order from any of the three rows.
- In a broken space the stored face and edge orders are zero, so
  `GetFaceOrder` and `GetEdgeOrder` return zero. `GetOrders` is different:
  it returns the cell order for every local face and edge, because the
  local basis is complete. `SetFE` also skips `SetOrientation` for a
  broken space.
- On a 2D mesh `GetEdgeOrder` returns `tsize = 0` and `tEdgeOrder` is
  zero: `FEDOF_` builds mesh edges only in 3D, and the mesh facets are
  the faces.
- `faceOrient` has one row in 2D and three in 3D; use `tFaceOrient(1)`,
  not a hard-coded row count.
- Do not expect a sign in `cellOrient`; the current mesh code sets all
  three entries to `1`.
- `GetOrders` accepts global or local element numbers. Pass `islocal`
  consistently, because the orientation lookup uses the converted local
  element.
- `SetFE` calls `GetOrders` internally. After re-initiating with new
  orders, call `SetFE` again before using the finite element.
