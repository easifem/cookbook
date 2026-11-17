# BlockNodeField: Exporting to VTK

**Purpose.** Write the mesh and the nodal values of a block node field
(`BlockNodeField_`, several physical variables in one vector) in a VTK
(`.vtu`) file, step by step, with `VTKFile_`, the mesh and `Get` of the
field. Node fields have no VTK method of their own.

**Classes.** `BlockNodeField_` (`BlockNodeField_Class`), `FEDOF_` and
`FEDOFPointer_` (`FEDOF_Class`), `VTKFile_` (`VTKFile_Class`),
`AbstractMesh_` (`AbstractMesh_Class`, method `ExportToVTK`).
Interface:
`classes:src/modules/BlockNodeField/src/BlockNodeField_Class.F90`.
The general steps are in
[ScalarField: Exporting to VTK](scalarfield-vtk-export.md).

## Steps

1. **Open the file, write the mesh, open the point data.** As in steps
   1 to 3 of [ScalarField: Exporting to VTK](scalarfield-vtk-export.md).
   All variables of the example use the same FEDOF, so one mesh is
   written.
2. **Read the layout.** `tvar` variables;
   `spaceCompo = u%GetSpaceCompo(tvar)`,
   `timeCompo = u%GetTimeCompo(tvar)`,
   `CALL u%GetPhysicalNames(dofnames)`.
3. **Write the values.** For each variable `ivar` and time component
   `ia`, get each space component `ic` at the local nodes
   `1, ..., tNodes` with Get6 `u%Get(VALUE(:), tsize, globalNode(:),
   islocal=math%yes, ivar=ivar, spaceCompo=ic, timeCompo=ia)`. Write
   one array:
   - one space component: scalar array, `numberOfComponents=1`,
   - more space components: vector array (x, y, z), missing
     components zero.

   The array is named `<fieldname>_<physicalname>`. A variable with
   more than one time component gets one array for each time
   component, `<fieldname>_<physicalname>_t<ia>`.
4. **Close.** As in step 5 of the ScalarField recipe.

Trimmed from `classes:src/modules/BlockNodeField/examples/ExportToVTK_test_1.F90`
(uses `BlockNodeField_test.toml`; `u` has `V` with two space and one
time component, and `T` with one space and two time components;
`meshptr`, `nptrs`, `tnodes` and the open `vtk` as in the ScalarField
recipe):

```fortran
USE Display_Method, ONLY: ToString

INTEGER(I4B), PARAMETER :: tvar = 2
CHARACTER(1) :: dofnames(tvar)
CHARACTER(:), ALLOCATABLE :: arrayName
REAL(DFP), ALLOCATABLE :: xyz(:, :)
INTEGER(I4B) :: ic, ia, ivar, tsize
INTEGER(I4B) :: spaceCompo(tvar), timeCompo(tvar)

spaceCompo = u%GetSpaceCompo(tvar)
timeCompo = u%GetTimeCompo(tvar)
CALL u%GetPhysicalNames(dofnames)
ALLOCATE (xyz(tnodes, 3))

DO ivar = 1, tvar
  DO ia = 1, timeCompo(ivar)
    xyz = 0.0_DFP
    DO ic = 1, spaceCompo(ivar)
      CALL u%Get(VALUE=xyz(:, ic), tsize=tsize, globalNode=nptrs, &
                 islocal=math%yes, ivar=ivar, spaceCompo=ic, &
                 timeCompo=ia)
    END DO

    arrayName = u%GetName()//"_"//dofnames(ivar)
    IF (timeCompo(ivar) .GT. 1) &
      arrayName = arrayName//"_t"//ToString(ia)

    IF (spaceCompo(ivar) .EQ. 1) THEN
      CALL vtk%WriteDataArray(name=String(arrayName), x=xyz(:, 1), &
                              numberOfComponents=1)
    ELSE
      CALL vtk%WriteDataArray(name=String(arrayName), x=xyz(:, 1), &
                              y=xyz(:, 2), z=xyz(:, 3))
    END IF
  END DO
END DO
```

## Example files (run from the `examples` directory)

- `classes:src/modules/BlockNodeField/examples/ExportToVTK_test_1.F90`:
  the value of variable `ivar` at node `i`, space component `c` and
  time component `a` is `1000 ivar + 100 a + 10 i + c`; the arrays
  `u_V`, `u_T_t1` and `u_T_t2` are read back from the file and checked.

## Pitfalls

- `BlockNodeField_` has no VTK method of its own, and `AbstractField_` has
  none either: `u%WriteData(vtk=vtk)` does not compile (the generic
  `WriteData` of a field takes only an HDF5 file). Write the file with
  the steps above.
- Get the mesh from the FEDOF, not from the field: `BlockNodeField_`
  leaves `obj%fedof` `NULL()` and keeps one FEDOF per variable in
  `obj%fedofs`.
- The example points every variable to the same `fedof`
  (`fedofs(ivar)%ptr => fedof`). With different FEDOFs per variable,
  node `i` of one variable need not be point `i` of the written mesh.
- Get6 takes **local** node numbers; pass `islocal=math%yes`.
- See also the pitfalls of
  [ScalarField: Exporting to VTK](scalarfield-vtk-export.md)
  (`closetag`, order 1).
