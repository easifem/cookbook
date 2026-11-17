# FEDomain: Boundary and facets

**Purpose.** Find boundary elements, boundary nodes and facets. Build
the facet data. Select elements of an entity with `MeshSelection_`.

**Classes.** `FEDomain_`, `FEMesh_`, `AbstractMesh_`, `MeshSelection_`
(`MeshSelection_Class`). See
[Mesh numbering and element data](../theory/mesh-numbering-and-data.md).

## Steps

1. Read the domain. This also builds the element-to-elements data. That
   data marks boundary elements and boundary nodes.
2. For boundary queries, use a mesh object. The tests read a `FEMesh_`
   with `obj%Initiate(hdf5=meshfile, DIM=2)`. You can use the pointer
   from `dom%GetMeshPointer(DIM=2)` instead.
3. Call `InitiateBoundaryData()` to store the boundary facets of each
   boundary element. Then `GetBoundaryElementData(globalElement=)`
   returns the local facet numbers on the boundary.
4. Call `dom%InitiateFacetElements()` to build facet elements on the
   meshes of the domain.
5. Call `mesh%InitiateEdgeConnectivity()` before you ask for global edge
   numbers.

```fortran
USE AbstractMesh_Class, ONLY: AbstractMesh_
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE ExceptionHandler_Class, ONLY: EXCEPTION_INFORMATION
USE FEMesh_Class, ONLY: FEMesh_
USE GlobalData, ONLY: I4B
USE HDF5File_Class, ONLY: HDF5File_
USE Test_Method, ONLY: OK

TYPE(FEMesh_) :: obj
TYPE(HDF5File_) :: meshfile
INTEGER(I4B), ALLOCATABLE :: bdata(:), nodes(:)

CALL e%SetQuietMode(EXCEPTION_INFORMATION, math%yes)
CALL meshfile%Initiate(filename="./meshdata/very_small_quad4_mesh.h5", &
                       mode="READ")
CALL meshfile%OPEN()
CALL obj%Initiate(hdf5=meshfile, DIM=2)

CALL OK(obj%IsBoundaryElement(13_I4B), "IsBoundaryElement")
CALL OK(obj%IsBoundaryNode(1_I4B), "node 1")
CALL OK(.NOT. obj%IsBoundaryNode(9_I4B), "node 9")
CALL OK(obj%GetTotalBoundaryNodes() .EQ. 8_I4B, "boundary nodes")
nodes = obj%GetBoundaryNptrs()
CALL OK(ALL(nodes .EQ. [1, 2, 3, 4, 5, 6, 7, 8]), "GetBoundaryNptrs")

CALL obj%InitiateBoundaryData()
CALL OK(obj%GetTotalBoundaryElements() .EQ. 4_I4B, "boundary elements")
bdata = obj%GetBoundaryElementData(globalElement=13_I4B)
CALL OK(ALL(bdata .EQ. [1, 4]), "boundary facets of element 13")

CALL obj%DEALLOCATE()
CALL meshfile%DEALLOCATE()
```

Facet elements on a domain:

```fortran
CALL dom%InitiateFacetElements()
mesh => dom%GetMeshPointer(DIM=2_I4B)
CALL OK(mesh%IsFacetData(), "surface mesh")
CALL OK(mesh%GetTotalFacetElements() .EQ. 12_I4B, "facet elements")
mesh => dom%GetMeshPointer(DIM=1_I4B)
CALL OK(.NOT. mesh%IsFacetData(), "no facet data in the curve mesh")
```

The facet connectivity of an element:
`obj%GetFacetConnectivity(globalElement=13, iface=1)` returns `[1, 5]`.
`GetFacetConnectivity_` writes into `ans(1:tsize)`.

Neighbours and edge numbers:

- `dom%InitiateElementToElements()` builds the neighbour data of every
  mesh.
- `dom%GetGlobalFaceNumber(globalElement=, localFaceNumber=)` returns a
  global face number.
- `dom%GetGlobalEdgeNumber(globalElement=, localEdgeNumber=)` returns a
  global edge number. Call `InitiateEdgeConnectivity` on the mesh first.

Select elements with `MeshSelection_` (mesh ids come from the file):

```fortran
CALL sel%Initiate()
CALL sel%Add(dim=2, meshID=[2])
CALL sel%Set()
tsize = sel%GetTotalElemNum(dim=2, dom=dom)
CALL sel%GetElemNum(dim=2, dom=dom, ans=ans, tsize=tsize)
```

For `very_small_quad4_mesh_two_region.h5`, the test finds elements 20
and 21 for surface mesh id 2.

## Example files (run from the `examples` directory)

- `classes:src/modules/FEMesh/examples/IsBoundaryElement_test_1.F90`
- `classes:src/modules/FEMesh/examples/IsBoundaryNode_test_1.F90`
- `classes:src/modules/FEMesh/examples/InitiateBoundaryData_test_1.F90`
- `classes:src/modules/FEMesh/examples/GetFacetConnectivity_test_1.F90`
- `classes:src/modules/FEDomain/examples/InitiateFacetElements_test_1.F90`
- `classes:src/modules/FEDomain/examples/InitiateElementToElements_test_1.F90`
- `classes:src/modules/FEDomain/examples/GetGlobalFaceNumber_test_1.F90`
- `classes:src/modules/MeshSelection/examples/GetElemNum_test_1.F90`

## Pitfalls

- A facet is an edge in 2D and a face in 3D.
- Point and curve meshes have no facet elements.
- A "boundary element" has a facet on the mesh boundary. It is not the
  same as a boundary node.
- `GetBoundaryElementData` needs `InitiateBoundaryData` first.
- `MeshSelection_` follows the order `Initiate`, `Add`, `Set`. Mesh ids
  need the `dom` argument in the `Get...` methods.
- The `MeshSelection_` tests read their meshes from
  `../../FEMesh/examples/meshdata/`.
