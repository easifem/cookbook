# ScalarField: Exporting to VTK

**Purpose.** Write the mesh and the nodal values of a `ScalarField_` in
a VTK (`.vtu`) file, step by step, with `VTKFile_`, the mesh and `Get`
of the field. Node fields have no VTK method of their own.

**Classes.** `ScalarField_` (`ScalarField_Class`), `VTKFile_`
(`VTKFile_Class`), `AbstractMesh_` (`AbstractMesh_Class`, method
`ExportToVTK`), `FEDOF_` (`GetMeshPointer`). Interfaces:
`classes:src/modules/ScalarField/src/ScalarField_Class.F90`,
`classes:src/modules/VTKFile/src/VTKFile_Class.F90`,
`classes:src/modules/AbstractMesh/src/AbstractMesh_Class.F90`.

## Steps

1. **Open the file.** `vtk%InitiateVTKFile(filename=, mode="NEW",
   dataFormat=VTK_ASCII, dataStructureType=VTK_UNSTRUCTUREDGRID)`.
2. **Write the mesh.** `meshptr => fedof%GetMeshPointer()`, then
   `meshptr%ExportToVTK(vtk=, opentag=math%yes, content=math%yes,
   closetag=math%no)`. This writes the points and cells and keeps the
   `Piece` tag open.
3. **Open the point data.** `vtk%WriteDataArray(location=String("node"),
   action=String("open"))`.
4. **Write the values.** The points are the local nodes
   `1, ..., meshptr%GetTotalNodes()`, in this order. Get the values
   with Get3 `u%Get(VALUE(:), globalNode(:), islocal=math%yes, tsize)`
   and write one array with `vtk%WriteDataArray(name=String(name),
   x=VALUE(1:tsize), numberOfComponents=1)`.
5. **Close.** `vtk%WriteDataArray(location=String("node"),
   action=String("close"))`, then `vtk%WritePiece()` (closes `Piece`),
   `vtk%CLOSE()` and `vtk%DEALLOCATE()`.

Trimmed from `classes:src/modules/ScalarField/examples/ExportToVTK_test_1.F90`
(uses `ScalarField_test.toml`):

```fortran
USE AbstractMesh_Class, ONLY: AbstractMesh_
USE BaseType, ONLY: math => TypeMathOpt
USE ScalarField_Class, ONLY: ScalarField_
USE String_Class, ONLY: String
USE VTKFile_Class, ONLY: VTKFile_
USE VTKFile_Class, ONLY: VTK_ASCII
USE VTKFile_Class, ONLY: VTK_UNSTRUCTUREDGRID

TYPE(ScalarField_) :: u
TYPE(VTKFile_) :: vtk
CLASS(AbstractMesh_), POINTER :: meshptr
CHARACTER(1) :: dofnames(1)
CHARACTER(:), ALLOCATABLE :: arrayName
INTEGER(I4B), ALLOCATABLE :: nptrs(:)
REAL(DFP), ALLOCATABLE :: nodeVal(:)
INTEGER(I4B) :: ii, tnodes, tsize

meshptr => fedof%GetMeshPointer()
tnodes = meshptr%GetTotalNodes()
nptrs = [(ii, ii=1, tnodes)]
ALLOCATE (nodeVal(tnodes))

CALL u%GetPhysicalNames(dofnames)
arrayName = u%GetName()//"_"//dofnames(1)

CALL vtk%InitiateVTKFile(filename="ExportToVTK_test_1.vtu", mode="NEW", &
                         dataFormat=VTK_ASCII, &
                         dataStructureType=VTK_UNSTRUCTUREDGRID)
CALL meshptr%ExportToVTK(vtk=vtk, opentag=math%yes, content=math%yes, &
                         closetag=math%no)
CALL vtk%WriteDataArray(location=String("node"), action=String("open"))

CALL u%Get(VALUE=nodeVal, globalNode=nptrs, islocal=math%yes, &
           tsize=tsize)
CALL vtk%WriteDataArray(name=String(arrayName), x=nodeVal(1:tsize), &
                        numberOfComponents=1)

CALL vtk%WriteDataArray(location=String("node"), action=String("close"))
CALL vtk%WritePiece()
CALL vtk%CLOSE()
CALL vtk%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/ScalarField/examples/ExportToVTK_test_1.F90`:
  the steps above. The value at node `i` is `10 i + 1`; the array
  `u_u` is read back from the file and checked.

## Pitfalls

- Pass `closetag=math%no` to the mesh `ExportToVTK`. Otherwise the
  `Piece` tag is closed before the point data. Then close it yourself
  with `vtk%WritePiece()`.
- Get3 takes **local** node numbers; pass `islocal=math%yes` (a debug
  build raises an error otherwise).
- The example uses order 1 Lagrange, where node `i` is DOF `i`. Only
  the mesh nodes are points in the file, so higher-order DOFs are not
  written.
- The example names the array `<fieldname>_<physicalname>` (here
  `u_u`). Use the same rule for all node fields, so that two fields
  with the same physical variable name get different arrays.
- `ScalarField_` has no VTK method of its own, and `AbstractField_` has
  none either: `u%WriteData(vtk=vtk)` does not compile (the generic
  `WriteData` of a field takes only an HDF5 file). Write the file with
  the steps above.
