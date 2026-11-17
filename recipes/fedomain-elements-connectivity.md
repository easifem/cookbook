# FEDomain: Elements, connectivity and numbers

**Purpose.** Get the connectivity and the coordinates of elements. Loop
over the elements of a mesh. Convert between global and local numbers.

**Classes.** `FEDomain_` (`FEDomain_Class`), `FEMesh_` (`FEMesh_Class`),
`AbstractMesh_` (`AbstractMesh_Class`), `ElemData_` (`ElemData_Class`).
See [Mesh numbering and element data](../theory/mesh-numbering-and-data.md).

## Steps

1. Read the domain as in
   [Read a mesh and query it](fedomain-read-and-query.md).
2. Get the connectivity with `GetConnectivity(globalElement=, DIM=)`.
   `DIM` defaults to `nsd`.
3. Use `GetConnectivity_` when you want no allocation. It writes
   `ans(1:tsize)`. The array `ans` must be large enough.
4. Get coordinates with `GetNodeCoord`. The result has `nsd` rows and
   one column per node.
5. For a loop over elements, get the mesh pointer and call
   `GetElemNum()`. Then call `GetConnectivity` for each number.
6. Convert numbers with `GetLocalNodeNumber`, `GetGlobalNodeNumber` and
   `GetLocalElemNumber`.

```fortran
USE AbstractMesh_Class, ONLY: AbstractMesh_
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE ExceptionHandler_Class, ONLY: EXCEPTION_INFORMATION
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE HDF5File_Class, ONLY: HDF5File_
USE Test_Method, ONLY: OK

TYPE(HDF5File_) :: meshfile
TYPE(FEDomain_) :: obj
CLASS(AbstractMesh_), POINTER :: mesh
INTEGER(I4B), ALLOCATABLE :: con(:), elems(:)
INTEGER(I4B) :: buf(20), tsize, ii
REAL(DFP), ALLOCATABLE :: xij(:, :)

CALL e%SetQuietMode(EXCEPTION_INFORMATION, math%yes)
CALL meshfile%Initiate(filename="./meshdata/very_small_quad4_mesh.h5", &
                       mode="READ")
CALL meshfile%OPEN()
CALL obj%Initiate(hdf5=meshfile, group="")

! connectivity
con = obj%GetConnectivity(globalElement=14_I4B)
CALL OK(ALL(con .EQ. [7, 9, 6, 3]), "element 14")
con = obj%GetConnectivity(globalElement=6_I4B, DIM=1_I4B)
CALL OK(ALL(con .EQ. [5, 2]), "line element 6")
CALL OK(obj%GetNNE(13_I4B) .EQ. 4_I4B, "GetNNE")
CALL obj%GetConnectivity_(globalElement=13_I4B, ans=buf, &
                          tsize=tsize, opt="V")
CALL OK(ALL(buf(1:tsize) .EQ. [1, 5, 9, 7]), "GetConnectivity_")

! coordinates
CALL obj%GetNodeCoord(nodeCoord=xij)
CALL OK(SIZE(xij, 2) .EQ. 9_I4B, "all nodes")

! loop over the elements of the surface mesh
mesh => obj%GetMeshPointer()
elems = mesh%GetElemNum()
CALL OK(ALL(elems .EQ. [13, 14, 15, 16]), "global element numbers")
DO ii = 1, SIZE(elems)
  con = obj%GetConnectivity(globalElement=elems(ii))
  ! use con here
END DO
mesh => NULL()

! numbers
CALL OK(obj%GetLocalNodeNumber(7_I4B) .EQ. 7_I4B, "local node")
CALL OK(obj%GetGlobalNodeNumber(7_I4B) .EQ. 7_I4B, "global node")
CALL OK(obj%GetLocalElemNumber(15_I4B) .EQ. 3_I4B, "local element")

CALL obj%DEALLOCATE()
CALL meshfile%DEALLOCATE()
```

More queries on the domain:

- `GetNodeCoord(nodeCoord=, nrow=, ncol=, globalNode=[...])`: some nodes.
- `GetNodeCoord(..., DIM=1)`: nodes of the curve mesh.
- `GetNodeCoordPointer()`: pointer to the stored coordinates.
- `GetNodeToElements(globalNode=)`: elements around a node.
- `GetDimEntityNum(globalElement)`: `[dim, entityNum]`.
- `GetElemData`, `GetElemDataPointer`: the `ElemData_` of an element.

On the mesh (`FEMesh_`), `GetConnectivity(globalElement=, islocal=,
opt=)` takes a local number if `islocal` is true.

## Example files (run from the `examples` directory)

- `classes:src/modules/FEDomain/examples/GetConnectivity_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetNodeCoord_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetLocalNodeNumber_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetNptrs_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetNodeToElements_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetDimEntityNum_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetElemData_test_1.F90`
- `classes:src/modules/FEMesh/examples/GetElemNum_test_1.F90`
- `classes:src/modules/FEMesh/examples/GetConnectivity_test_1.F90`

## Pitfalls

- `FEDomain_%GetNodeCoord` returns `nsd` rows. `FEMesh_%GetNodeCoord`
  returns 3 rows. The first rows hold the coordinates.
- In `very_small_quad4_mesh.h5`, global and local node numbers agree.
  Element numbers do not: global 15 is local 3.
- `GetNodeToElements` initiates the node-to-elements data on first use.
  You need no call to `InitiateNodeToElements` first.
- A buffer passed to a `...Get..._` routine is not reallocated. Size it
  for the largest case.
- `GetElemNum()` on the mesh returns global numbers. Pass
  `islocal=.TRUE.` for local numbers.
- `opt="V"` selects the vertex nodes of the element. The tests use it
  on linear elements only. (unverified for higher-order elements)
