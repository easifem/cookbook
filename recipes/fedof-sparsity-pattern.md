# FEDOF: Matrix sparsity patterns

**Purpose.** Choose the right `SetSparsity` overload to build a CSR
pattern from one or more `FEDOF_` objects, and know whether the overload
finishes the pattern or leaves that to the caller.

**Classes.** `FEDOF_` (`FEDOF_Class`), `FEDOFPointer_`, `FEDOFSetSparsity`,
`CSRMatrix_`, `DOF_`. Interface:
`classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

## Steps

1. Initiate a matrix whose row and column `DOF_` objects match the
   `FEDOF` sizes.
2. Pick the overload:

   | Call | Use | Finishes? |
   |---|---|---|
   | `obj%SetSparsity(mat)` | one FEDOF | yes |
   | `obj%SetSparsity(col_fedof, mat, ivar, jvar)` | same mesh | no |
   | `obj%SetSparsity(col_fedof, cellToCell, mat, ...)` | other mesh | no |
   | `FEDOFSetSparsity(fedofs, mat)` | one per variable | no |

3. The connectivity rule: two DOFs are connected when they belong to the
   same element. Inactive elements are skipped.
4. Call `CSRMatrix` `SetSparsity(mat)` yourself for the last three rows
   of the table. Only `obj%SetSparsity(mat)` finishes the pattern.

```fortran
TYPE(FEDOF_) :: obj, col_fedof
TYPE(DOF_) :: idof, jdof
TYPE(CSRMatrix_) :: mat

CALL obj%Initiate(baseContinuity="H1", &
                  baseInterpolation="Hierarchical", order=2, dom=dom)
CALL col_fedof%Initiate(baseContinuity="H1", &
                        baseInterpolation="Hierarchical", order=1, dom=dom)

CALL CSRMatrixInitiate(mat, nrow=DOFSize(idof), ncol=DOFSize(jdof), &
                       idof=idof, jdof=jdof, matrixProp="RECTANGLE")
CALL obj%SetSparsity(col_fedof=col_fedof, mat=mat, ivar=1, jvar=1)
CALL CSRMatrixSetSparsity(mat)   ! the overload did not finish it
```

5. For a broken space, `SetSparsity` also connects each cell block to its
   active neighbour cells, because numerical fluxes act on interior
   facets. The neighbour couplings are always added by `SetSparsity`;
   there is no extra option to enable them.
6. `FEDOFSetSparsity(fedofs, mat)` treats `fedofs(ii)` as physical
   variable `ii`. For a rectangular matrix, `fedofs(1)` gives the rows and
   `fedofs(2)` the columns. If two FEDOF use the same mesh it takes the
   same-mesh path and skips the cell-to-cell map; otherwise it builds the
   map with `FEDomainConnectivity_`. All FEDOF must have the same `nsd`.

## Example files (run from the examples directory)

- `classes:src/modules/FEDOF/examples/SetSparsity_test_1.F90`
- `classes:src/modules/FEDOF/examples/SetSparsity_test_5.F90`
- `classes:src/modules/FEDOF/examples/SetSparsity_test_6.F90`

`SetSparsity_test_1` checks the full dense pattern on a four-quadrangle
mesh: order 1, H1 hierarchical, gives 49 nonzeros; the broken space of
order 1 gives four cell blocks of 4 DOFs with neighbour couplings.
`SetSparsity_test_5` checks that the same-mesh overload matches the
single-FEDOF pattern, and that a rectangle from order 2 rows and order 1
columns matches `FEDOFSetSparsity`.

## Pitfalls

- A non-finished pattern has no column indices yet. Reading or using the
  matrix before `CSRMatrix` `SetSparsity` gives wrong results.
- `SetSparsity2` skips elements whose `cellToCell(iel)` is zero, so an
  incomplete map silently drops rows.
- In a broken space the pattern is not block diagonal: neighbouring cell
  blocks are coupled.
- `SetSparsity4` assumes a shared mesh pointer. For two meshes, use
  `SetSparsity2` with the cell-to-cell map.
- A square matrix needs `matrixProp` set for a square pattern; a
  rectangle needs separate row and column DOF objects.
