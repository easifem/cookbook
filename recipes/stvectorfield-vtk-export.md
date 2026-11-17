# STVectorField: Exporting to VTK

**Purpose.** Write the mesh and the nodal values of a space-time vector
field (`STVectorField_`) in a VTK (`.vtu`) file, step by step, with
`VTKFile_`, the mesh and `Get` of the field. Node fields have no
VTK method of their own.

**Classes.** `STVectorField_` (`STVectorField_Class`), `TimeFEDOF_`,
`VTKFile_` (`VTKFile_Class`), `AbstractMesh_` (`AbstractMesh_Class`,
method `ExportToVTK`), `FEDOF_` (`GetMeshPointer`). Interface:
`classes:src/modules/STVectorField/src/STVectorField_Class.F90`.
The general steps are in
[ScalarField: Exporting to VTK](scalarfield-vtk-export.md).

## Steps

1. **Open the file, write the mesh, open the point data.** As in steps
   1 to 3 of [ScalarField: Exporting to VTK](scalarfield-vtk-export.md).
2. **Write the values.** Write one vector array (x, y, z) for each time
   component `ia`, named `<fieldname>_<physicalname>_t<ia>`. For each
   space component `ic`, get the values at the local nodes
   `1, ..., tNodes` with Get4 `u%Get(VALUE(:), tsize, globalNode(:),
   islocal=math%yes, spaceCompo=ic, timeCompo=ia)`. Keep a missing
   component (z of a 2D field) at zero.
3. **Close.** As in step 5 of the ScalarField recipe.

Trimmed from `classes:src/modules/STVectorField/examples/ExportToVTK_test_1.F90`
(uses `STVectorField_test.toml`, `spaceCompo = 2`, `timeCompo = 2`;
`meshptr`, `nptrs`, `tnodes` and the open `vtk` as in the ScalarField
recipe):

```fortran
USE Display_Method, ONLY: ToString

CHARACTER(:), ALLOCATABLE :: baseName
REAL(DFP), ALLOCATABLE :: xyz(:, :)
INTEGER(I4B) :: ic, ia, tsize, spaceCompo(1), timeCompo(1)

spaceCompo = u%GetSpaceCompo(1)
timeCompo = u%GetTimeCompo(1)
CALL u%GetPhysicalNames(dofnames)
baseName = u%GetName()//"_"//dofnames(1)//"_t"
ALLOCATE (xyz(tnodes, 3))

DO ia = 1, timeCompo(1)
  xyz = 0.0_DFP
  DO ic = 1, spaceCompo(1)
    CALL u%Get(VALUE=xyz(:, ic), tsize=tsize, globalNode=nptrs, &
               islocal=math%yes, spaceCompo=ic, timeCompo=ia)
  END DO
  CALL vtk%WriteDataArray(name=String(baseName//ToString(ia)), &
                          x=xyz(:, 1), y=xyz(:, 2), z=xyz(:, 3))
END DO
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STVectorField/examples/ExportToVTK_test_1.F90`:
  the value at node `i`, space component `c` and time component `a` is
  `100 a + 10 i + c`; the arrays `u_u_t1` and `u_u_t2` are read back
  from the file (x y z for each point) and checked.

## Pitfalls

- `STVectorField_` has no VTK method of its own, and `AbstractField_` has
  none either: `u%WriteData(vtk=vtk)` does not compile (the generic
  `WriteData` of a field takes only an HDF5 file). Write the file with
  the steps above.
- Reset `xyz` to zero for each time component, so that z stays zero.
- Get4 takes **local** node numbers; pass `islocal=math%yes`.
- See also the pitfalls of
  [ScalarField: Exporting to VTK](scalarfield-vtk-export.md)
  and [STScalarField: Exporting to VTK](stscalarfield-vtk-export.md).
