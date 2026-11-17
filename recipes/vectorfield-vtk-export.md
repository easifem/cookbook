# VectorField: Exporting to VTK

**Purpose.** Write the mesh and the nodal values of a `VectorField_` in
a VTK (`.vtu`) file, step by step, with `VTKFile_`, the mesh and `Get`
of the field. Node fields have no VTK method of their own.

**Classes.** `VectorField_` (`VectorField_Class`), `VTKFile_`
(`VTKFile_Class`), `AbstractMesh_` (`AbstractMesh_Class`, method
`ExportToVTK`), `FEDOF_` (`GetMeshPointer`). Interfaces:
`classes:src/modules/VectorField/src/VectorField_Class.F90`,
`classes:src/modules/VTKFile/src/VTKFile_Class.F90`,
`classes:src/modules/AbstractMesh/src/AbstractMesh_Class.F90`.
The general steps are in
[ScalarField: Exporting to VTK](scalarfield-vtk-export.md).

## Steps

1. **Open the file, write the mesh, open the point data.** As in steps
   1 to 3 of [ScalarField: Exporting to VTK](scalarfield-vtk-export.md).
2. **Write the values.** A VTK vector has three components (x, y, z).
   For each space component `ic`, get the values at the local nodes
   `1, ..., tNodes` with Get4 `u%Get(VALUE(:), tsize, globalNode(:),
   islocal=math%yes, spaceCompo=ic)`. Keep a missing component (z of a
   2D field) at zero. Write one array with
   `vtk%WriteDataArray(name=, x=, y=, z=)`.
3. **Close.** As in step 5 of the ScalarField recipe.

Trimmed from `classes:src/modules/VectorField/examples/ExportToVTK_test_1.F90`
(uses `VectorField_test.toml`, `spaceCompo = 2`; `meshptr`, `nptrs`,
`tnodes` and the open `vtk` as in the ScalarField recipe):

```fortran
REAL(DFP), ALLOCATABLE :: xyz(:, :)
INTEGER(I4B) :: ic, tsize, spaceCompo(1)

spaceCompo = u%GetSpaceCompo(1)
CALL u%GetPhysicalNames(dofnames)
arrayName = u%GetName()//"_"//dofnames(1)
ALLOCATE (xyz(tnodes, 3))

! xyz(:, 3) stays zero for a 2D field
xyz = 0.0_DFP
DO ic = 1, spaceCompo(1)
  CALL u%Get(VALUE=xyz(:, ic), tsize=tsize, globalNode=nptrs, &
             islocal=math%yes, spaceCompo=ic)
END DO
CALL vtk%WriteDataArray(name=String(arrayName), x=xyz(:, 1), &
                        y=xyz(:, 2), z=xyz(:, 3))
```

## Example files (run from the `examples` directory)

- `classes:src/modules/VectorField/examples/ExportToVTK_test_1.F90`:
  the value at node `i` is `[10 i + 1, 10 i + 2]`; the array `u_u` is
  read back from the file (x y z for each point) and checked.

## Pitfalls

- Write three components even for a 2D field, so that ParaView reads
  the array as a vector.
- Get4 takes **local** node numbers; pass `islocal=math%yes`.
- `VectorField_` has no VTK method of its own, and `AbstractField_` has
  none either: `u%WriteData(vtk=vtk)` does not compile (the generic
  `WriteData` of a field takes only an HDF5 file). Write the file with
  the steps above.
- See also the pitfalls of
  [ScalarField: Exporting to VTK](scalarfield-vtk-export.md)
  (`closetag`, order 1).
