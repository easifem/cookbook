# Mesh numbering, connectivity and element data

**Purpose.** Explain global and local numbers and connectivity. Show
the data kept per node, element and facet. Say when each exists.

**Classes.** `AbstractMesh_`, `FEMesh_`, `FEDomain_`. Interfaces:
`classes:src/modules/AbstractMesh/src/AbstractMesh_Class.F90`,
`classes:src/modules/FEDomain/src/FEDomain_Class.F90`.

## Global and local numbers

- A global number is the number in the mesh file. Node numbers and
  element numbers are global by default.
- A local number is a position in the mesh arrays. Local numbers start
  at 1.
- Local node numbers follow the order of the global node numbers.
- Local element numbers follow the order of the elements in the file.
- Each mesh has its own local numbers.
- Most methods take a global number. If `islocal` is true, they take a
  local number. The default is false.
- Example from `very_small_quad4_mesh.h5`: the surface mesh has global
  elements 13 to 16. Global element 15 is local element 3. Node 7 has
  local number 7.
  See `classes:src/modules/FEDomain/examples/GetLocalNodeNumber_test_1.F90`.
- Domain methods use the mesh of dimension `nsd`. They are
  `GetLocalNodeNumber`, `GetGlobalNodeNumber` and `GetLocalElemNumber`.
- The node numbers of a file can be sparse. The domain flags this in
  `isNodeNumberSparse`. Do not assume that numbers run from 1 to the
  number of nodes.

## Connectivity

- The connectivity of an element is the list of its global node numbers.
- Example: element 13 of the quad mesh has the connectivity
  `[1, 5, 9, 7]`.
  See `classes:src/modules/FEMesh/examples/GetConnectivity_test_1.F90`.
- The argument `opt="V"` selects the vertex nodes. The tests use it on
  linear elements only.
- The connectivity of a facet is the node list of one face of an
  element. `GetFacetConnectivity(globalElement, iface)` returns it.
- `GetNNE` returns the number of nodes of an element.

## Data stored in a mesh

- `nodeData(:)`: one entry per local node. It holds the global number,
  the type (internal or boundary), the coordinates and the links to
  elements and nodes.
- `elementData(:)`: one entry per local element. It holds the global
  number, connectivity, mesh id, neighbours, boundary data, edges,
  faces and materials.
- `facetData(:)`: one entry per facet element.

- Type `ElemData_` describes one element.
  `GetElemData` returns a copy. `GetElemDataPointer` returns a pointer.
- The accessors `Elemdata_localElemNum` and `Elemdata_globalElemNum`
  read the numbers of an `ElemData_`.
  See `classes:src/modules/FEDomain/examples/GetElemData_test_1.F90`.

## When data exists

- `Initiate` or `Import` reads the mesh. It also builds the
  element-to-elements data. That data marks boundary elements and
  boundary nodes.
- Other data is not built at once. Call these methods before you use it.
  - `InitiateNodeToElements`: elements around each node.
  - `InitiateNodeToNodes`: nodes around each node.
  - `InitiateExtraNodeToNodes`: extra node-to-node links.
  - `InitiateElementToElements`: neighbours of each element.
  - `InitiateBoundaryData`: boundary facets of boundary elements.
  - `InitiateEdgeConnectivity`, `InitiateFaceConnectivity`: edge and
    face numbering.
  - `InitiateFacetElements`: facet elements of the mesh.
  - `InitiateKdtree`: kdtree for nearest-node searches.
- `FEDomain_` has `InitiateNodeToElements`, `InitiateNodeToNodes`,
  `InitiateExtraNodeToNodes`, `InitiateElementToElements` and
  `InitiateFacetElements`. Each one acts on the meshes of the domain.

## Node coordinates

- The domain stores `nodeCoord(:, :)` with `nsd` rows and one column per
  node.
- `FEDomain_%GetNodeCoord` returns `nsd` rows.
  `FEMesh_%GetNodeCoord` returns 3 rows.
  See the two `GetNodeCoord_test_1.F90` files in `FEDomain` and `FEMesh`.

## Facets and boundaries

- A boundary element has a facet on the boundary of the mesh.
- A facet is a face in 3D and an edge in 2D.
- A domain boundary element is a boundary element not connected to
  another mesh. In a single mesh, every boundary element is one.
- A boundary node is a node on a boundary facet. In the quad mesh test,
  nodes 1 to 8 are boundary nodes and node 9 is internal.
- Facet elements exist only for meshes with `xidim` of 2 or 3. Point
  and curve meshes have none.

## Related entries

- [Mesh and FEDomain: the concepts](mesh-and-fedomain.md)
- [Elements and numbers](../recipes/fedomain-elements-connectivity.md)
- [Boundary and facets](../recipes/fedomain-boundary-facets.md)
