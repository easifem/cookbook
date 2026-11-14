# FEDOF: Variable-order H1 hierarchical space

**Purpose.** Assign a different polynomial order to each cell of an H1
hierarchical space, and predict the DOFs on shared facets and inside
cells.

**Classes.** `FEDOF_` (`FEDOF_Class`), `FEDomain_` (`FEDomain_Class`),
`HDF5File_` (`HDF5File_Class`). Interface:
`classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

## Steps

1. Open the mesh and initiate a `FEDomain_` from it.
2. Build the cell orders. With `islocal=.TRUE.`, `order(ii)` is the order
   of local element `ii`. With `islocal=.FALSE.`, it is the order of
   global element `ii`; the array must cover the largest element ID, and
   entries for absent elements are ignored. A one-entry array gives every
   cell the same order.
3. Call `Initiate` with `baseInterpolation="Hierarchical"`:

```fortran
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B

TYPE(FEDOF_) :: obj
TYPE(FEDomain_) :: dom
INTEGER(I4B) :: cellOrders(2)

cellOrders = [1, 4]
CALL obj%Initiate(order=cellOrders, islocal=.TRUE., dom=dom, &
                  baseContinuity="H1", &
                  baseInterpolation="Hierarchical")
CALL obj%SetFE(globalElement=101)
```

4. For a conforming space a shared facet uses `p_e = MIN(p_K, p_L)`. It
   owns `p_e - 1` interior DOFs, so `GetFacetConnectivity_` returns
   `p_e + 1` entries: two vertex DOFs plus the interior DOFs. The
   higher-order cell keeps its own interior order.
5. Global DOF count:

   $$ n_{dof} = N_v + \sum_e (p_e-1) + \sum_K n_{int}(p_K) $$

   with `n_int = (p-1)(p-2)/2` on a triangle and `(p-1)^2` on a
   quadrangle. `N_v` is the number of mesh vertex nodes.
6. Call `SetFE(globalElement=...)` before `GetFEPointer(...)`. The local
   FE size equals the local DOF count of the cell.

## Example files (run from the examples directory)

- `classes:src/modules/FEDOF/examples/H1VariableOrder_test_1.F90`
- `classes:src/modules/FEDOF/examples/H1Numbering_test_1.F90`
- fixtures:
  `classes:src/modules/FEDOF/examples/fixtures/h1_two_triangles.msh.txt`,
  `classes:src/modules/FEDOF/examples/fixtures/h1_two_quads.msh.txt`

`H1VariableOrder_test_1` runs the two-cell fixtures with local and global
order input. It checks `nfacet == minOrder + 1` on the shared facet, that
only those trace DOFs are shared, that numbering has no holes, and that
the physical basis and tangential derivative agree from both cells.

## Pitfalls

- Only hierarchical H1 applies this trace reduction. The code does not
  provide constraints for variable-order Lagrange.
- In 2D the mesh facets are lines: the edge block is empty and
  line-interior DOFs are stored in the face block.
- Orientation is applied by the FE (`GetLocalElemShapeData`), not by
  reversing the element connectivity: the test gets matching traces on
  the shared edge with opposite local orientation.
- Elements of one topology share one finite element object. Call `SetFE`
  again before using an element of the same topology.
- A global order array must cover the largest element ID; entries for
  absent elements are ignored, not an error.
