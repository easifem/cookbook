# FEDOF: H1 hierarchical DOFs of order p

**Purpose.** Read an HDF5 mesh, build a `FEDomain_`, initiate a `FEDOF_`
with H1 continuity and hierarchical basis of order `p`, and query the
vertex, edge and face DOFs and their totals.

**Classes.** `HDF5File_` (`HDF5File_Class`), `FEDomain_`
(`FEDomain_Class`), `FEDOF_` (`FEDOF_Class`). Interfaces:
`classes:src/modules/FEDOF/src/FEDOF_Class.F90`.

## Steps

1. Open the mesh file with `mode="READ"` and call `OPEN()`.
2. `dom%Initiate(meshfile, "")`: the second argument is the group.
3. `obj%Initiate(order=, dom=, baseContinuity="H1",
   baseInterpolation="Hierarchical", isBrokenSpace=math%no)`. Only the
   first four letters of the interpolation are used, so `"HIER"` works.
4. Query per entity (`Get*DOF` writes `ans(1:tsize)`) or count
   (`GetTotal*DOF` returns an integer). Edge and face queries take either
   a mesh entity number (`globalEdge`, `globalFace`) or an element plus
   a local number (`globalElement`, `localEdgeNumber`/`localFaceNumber`).

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B
USE HDF5File_Class, ONLY: HDF5File_
USE Test_Method, ONLY: OK

TYPE(FEDOF_) :: obj
TYPE(FEDomain_) :: dom
TYPE(HDF5File_) :: meshfile
INTEGER(I4B) :: ans(10), tsize, order

order = 2
CALL meshfile%Initiate("./meshdata/small_hexa8_mesh.h5", mode="READ")
CALL meshfile%OPEN()
CALL dom%Initiate(meshfile, "")
CALL obj%Initiate(baseContinuity="H1", baseInterpolation="Hierarchical", &
                  isBrokenSpace=math%no, order=order, dom=dom)

CALL obj%GetVertexDOF(globalNode=1, islocal=math%yes, ans=ans, &
                      tsize=tsize)                     ! tsize = 1
CALL obj%GetEdgeDOF(globalElement=1, localEdgeNumber=1, ans=ans, &
                    tsize=tsize, islocal=math%yes)     ! tsize = p-1
CALL obj%GetFaceDOF(globalElement=1, localFaceNumber=1, ans=ans, &
                    tsize=tsize, islocal=math%yes)     ! tsize = 1 (p=2)
CALL OK(obj%GetTotalDOF() .EQ. 45_I4B, "12 + 20 + 11 + 2 for p=2")
CALL OK(obj%GetTotalVertexDOF() .EQ. 12_I4B, "one DOF per vertex")

CALL obj%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL meshfile%DEALLOCATE()
```

Other totals: `GetTotalEdgeDOF`, `GetTotalFaceDOF`, `GetTotalCellDOF
(globalCell=)`, `GetTotalDOF(globalElement=)` (all DOFs of one element)
and `GetTotalDOF(globalElement=, opt=)` with `opt` = `"V"`, `"E"`, `"F"`,
`"C"` or `"A"` (first letter used).

## Example files (run from the `examples` directory)

- `classes:src/modules/FEDOF/examples/GetVertexDOF_test_1.F90`
- `classes:src/modules/FEDOF/examples/GetEdgeDOF_test_1.F90` (hexa, 3D)
- `classes:src/modules/FEDOF/examples/GetFaceDOF_test_1.F90` (quad, 2D)
- `classes:src/modules/FEDOF/examples/GetFaceDOF_test_2.F90` (tri6, 2D)
- `classes:src/modules/FEDOF/examples/GetTotalFaceDOF_test_1.F90`
- `classes:src/modules/FEDOF/examples/GetTotalDOF_test_1.F90`

## Pitfalls

- `order` must be at least 1 (order 0 is not supported for H1 HIER).
- `order=1`: no edge, face or cell DOFs; `tsize = 0` and totals are 0.
- In 2D the "faces" are the lines: line DOFs (p-1 each) are face DOFs and
  the edge block is empty (`opt="E"` gives 0). Cell interior: triangle
  (p-1)(p-2)/2, quadrangle (p-1)^2.
- Numbering: vertex DOFs are `1:tNodes`, then edge, face and cell blocks,
  each ordered by mesh entity number.
- `isBrokenSpace=math%yes`: vertices, edges and faces own no DOFs
  (`tsize = 0`); every cell owns its full local basis.
- `islocal` says how to read the input number (`globalNode`,
  `globalElement`); `ans` always holds DOF numbers local to the FEDOF.
  The `globalEdge`/`globalFace` forms do not use it yet.
- A hexahedron face has (p-1)^2 DOFs: 1 at p=2
  (`classes:src/modules/FEDOF/examples/GetEdgeDOF_test_1.F90` header).
- `ans` must hold at least `tsize` entries; it is not reallocated.
- `Initiate` calls `DEALLOCATE` first, so one object can be re-initiated
  (the tests loop over orders this way).
