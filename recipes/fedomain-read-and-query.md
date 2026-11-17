# FEDomain: Read a mesh and query it

**Purpose.** Read an HDF5 mesh file into a `FEDomain_`. Query sizes per
dimension. Get the mesh of a given dimension. Display the domain.

**Classes.** `HDF5File_` (`HDF5File_Class`), `FEDomain_`
(`FEDomain_Class`), `AbstractMesh_` (`AbstractMesh_Class`). Interfaces:
`classes:src/modules/FEDomain/src/FEDomain_Class.F90`.

## Steps

1. Open the mesh file with `mode="READ"` and call `OPEN()`.
2. Call `obj%Initiate(hdf5=meshfile, group="")`. The group is `""` when
   the data is at the root of the file.
3. Query the domain. Methods take `DIM`. If `DIM` is absent, they use
   the spatial dimension `nsd`.
4. Call `GetMeshPointer(DIM=)` to get one mesh. The pointer is not
   associated if the domain has no mesh of that dimension.
5. Call `DEALLOCATE` on the domain and on the file.

```fortran
USE AbstractMesh_Class, ONLY: AbstractMesh_
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE ExceptionHandler_Class, ONLY: EXCEPTION_INFORMATION
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B
USE HDF5File_Class, ONLY: HDF5File_
USE Test_Method, ONLY: OK

TYPE(HDF5File_) :: meshfile
TYPE(FEDomain_) :: obj
CLASS(AbstractMesh_), POINTER :: mesh

CALL e%SetQuietMode(EXCEPTION_INFORMATION, math%yes)
CALL meshfile%Initiate(filename="./meshdata/very_small_quad4_mesh.h5", &
                       mode="READ")
CALL meshfile%OPEN()
CALL obj%Initiate(hdf5=meshfile, group="")

CALL OK(obj%GetNSD() .EQ. 2_I4B, "GetNSD")
CALL OK(obj%GetTotalNodes() .EQ. 9_I4B, "GetTotalNodes")
CALL OK(obj%GetTotalNodes(DIM=1_I4B) .EQ. 8_I4B, "curve mesh")
CALL OK(obj%GetTotalElements() .EQ. 4_I4B, "surface elements")
CALL OK(obj%GetTotalElements(DIM=1_I4B) .EQ. 8_I4B, "curve elements")
CALL OK(obj%GetTotalElements(DIM=0_I4B) .EQ. 4_I4B, "point elements")
CALL OK(obj%GetTotalEntities(DIM=2_I4B) .EQ. 1_I4B, "surface entities")
CALL OK(obj%GetMaxElemNumber() .EQ. 16_I4B, "GetMaxElemNumber")

mesh => obj%GetMeshPointer(DIM=1_I4B)
CALL OK(mesh%GetTotalElements() .EQ. 8_I4B, "curve mesh")
mesh => obj%GetMeshPointer(DIM=3_I4B)
CALL OK(.NOT. ASSOCIATED(mesh), "no volume mesh")
mesh => NULL()

CALL obj%Display("domain:")
CALL obj%DisplayDomainInfo("domain info:")

CALL obj%DEALLOCATE()
CALL meshfile%DEALLOCATE()
```

Other queries:

- `GetMinNodeNumber`, `GetMaxNodeNumber`, `GetMinElemNumber`.
- `IsNodePresent(node)`, `IsElementPresent(elem, DIM=)`.
- `GetTotalElements(DIM=, entityNum=)`: elements of one entity.
- Operators: `.tNodes. obj`, `obj .tNodes. dim`, `.tElements. obj`,
  `obj .tElements. dim` and `obj .tElements. [dim, entityNum]`.
- `GetNptrs(DIM=)`: global node numbers of one mesh.
- `GetNearestNode(qv=, x=, globalNode=)`: nearest node to a point.

## Example files (run from the `examples` directory)

- `classes:src/modules/FEDomain/examples/Initiate_test_1.F90`
- `classes:src/modules/FEDomain/examples/Initiate_test_2.F90`
  (two regions)
- `classes:src/modules/FEDomain/examples/GetMeshPointer_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetTotalNodes_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetTotalElements_test_1.F90`
- `classes:src/modules/FEDomain/examples/IsNodePresent_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetNearestNode_test_1.F90`
- `classes:src/modules/FEDomain/examples/Display_test_1.F90`

## Pitfalls

- The quad mesh has 4 surface elements, 8 curve elements and 4 point
  elements. The domain total is 9 nodes. The numbers are for
  `very_small_quad4_mesh.h5`.
- Element numbers are global and unique over all dimensions in this
  file. Surface elements are 13 to 16. `GetMaxElemNumber` is 16.
- `GetTotalElements()` counts the mesh of dimension `nsd` only.
- `GetMeshPointer` returns a pointer into the domain. It is dangling
  after `obj%DEALLOCATE()`.
- A domain with two regions has several entities of one dimension. Use
  `entityNum` to count one of them.
- `Display` shows the domain data and the info of each mesh. The output
  is long for big meshes. `DisplayDomainInfo` shows the meta data.
