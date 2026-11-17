# STScalarField: Exporting to VTK

**Purpose.** Write the mesh and the nodal values of a space-time scalar
field (`STScalarField_`) in a VTK (`.vtu`) file, step by step, with
`VTKFile_`, the mesh and `Get` of the field. Node fields have no
VTK method of their own.

**Classes.** `STScalarField_` (`STScalarField_Class`), `TimeFEDOF_`,
`VTKFile_` (`VTKFile_Class`), `AbstractMesh_` (`AbstractMesh_Class`,
method `ExportToVTK`), `FEDOF_` (`GetMeshPointer`). Interface:
`classes:src/modules/STScalarField/src/STScalarField_Class.F90`.
The general steps are in
[ScalarField: Exporting to VTK](scalarfield-vtk-export.md).

## Steps

1. **Open the file, write the mesh, open the point data.** As in steps
   1 to 3 of [ScalarField: Exporting to VTK](scalarfield-vtk-export.md).
2. **Write the values.** Write one scalar array for each time component
   `ia = 1, ..., timeCompo`, named `<fieldname>_<physicalname>_t<ia>`.
   Get the values at the local nodes `1, ..., tNodes` with Get4
   `u%Get(VALUE(:), globalNode(:), tsize, islocal=math%yes,
   timeCompo=ia)`.
3. **Close.** As in step 5 of the ScalarField recipe.

Trimmed from `classes:src/modules/STScalarField/examples/ExportToVTK_test_1.F90`
(uses `STScalarField_test.toml`, `timeCompo = 2`; `meshptr`, `nptrs`,
`tnodes` and the open `vtk` as in the ScalarField recipe):

```fortran
USE Display_Method, ONLY: ToString

CHARACTER(:), ALLOCATABLE :: baseName
REAL(DFP), ALLOCATABLE :: nodeVal(:)
INTEGER(I4B) :: ia, tsize, timeCompo(1)

timeCompo = u%GetTimeCompo(1)
CALL u%GetPhysicalNames(dofnames)
baseName = u%GetName()//"_"//dofnames(1)//"_t"
ALLOCATE (nodeVal(tnodes))

DO ia = 1, timeCompo(1)
  CALL u%Get(VALUE=nodeVal, globalNode=nptrs, tsize=tsize, &
             islocal=math%yes, timeCompo=ia)
  CALL vtk%WriteDataArray(name=String(baseName//ToString(ia)), &
                          x=nodeVal(1:tsize), numberOfComponents=1)
END DO
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STScalarField/examples/ExportToVTK_test_1.F90`:
  the value at node `i` and time component `a` is `10 i + a`; the
  arrays `u_u_t1` and `u_u_t2` are read back from the file and
  checked.

## Pitfalls

- `STScalarField_` has no VTK method of its own, and `AbstractField_` has
  none either: `u%WriteData(vtk=vtk)` does not compile (the generic
  `WriteData` of a field takes only an HDF5 file). Write the file with
  the steps above.
- Get4 takes **local** node numbers; pass `islocal=math%yes`.
- The time components are values at the time DOFs of `TimeFEDOF_`
  (here order 1 Lagrange in time, two DOFs), not values at time steps.
- See also the pitfalls of
  [ScalarField: Exporting to VTK](scalarfield-vtk-export.md)
  (`closetag`, order 1).
