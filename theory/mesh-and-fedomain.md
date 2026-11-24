# Mesh and FEDomain: the concepts

**Purpose.** Explain what a mesh and a `FEDomain_` are in
`easifemClasses`, how they fit together, and who uses them.

**Classes.** `AbstractMesh_`, `FEMesh_`, `AbstractDomain_`, `FEDomain_`,
`MeshSelection_`, `FEDOF_`. Interfaces:
`classes:src/modules/AbstractMesh/src/AbstractMesh_Class.F90`,
`classes:src/modules/FEMesh/src/FEMesh_Class.F90`,
`classes:src/modules/AbstractDomain/src/AbstractDomain_Class.F90`,
`classes:src/modules/FEDomain/src/FEDomain_Class.F90`.

## Mesh

- `AbstractMesh_` holds the elements of one dimension. The dimension is
  0 (points), 1 (curves), 2 (surfaces) or 3 (volumes).
- The component `xidim` holds the dimension of its elements. The
  component `nsd` holds the spatial dimension.
- `FEMesh_` extends `AbstractMesh_`. It adds no components and no
  methods. Use `FEMesh_` when you need a concrete mesh object.
- A mesh keeps data for nodes (`nodeData`), elements (`elementData`)
  and facets (`facetData`). See
  [Mesh numbering and element data](mesh-numbering-and-data.md).
- The module `Mesh` exists in the source tree but is not built.
  Use `AbstractMesh_` and `FEMesh_`.

## FEDomain

- `AbstractDomain_` holds the data shared by all meshes.
  This is `nsd`, the number of nodes and the node coordinates.
  It also holds the number of entities of each dimension.
- `FEDomain_` extends it. It owns one `FEMesh_` for each dimension up
  to `nsd`.
- A 2D domain has a surface mesh, a curve mesh and a point mesh. A 3D
  domain also has a volume mesh.
- The mesh of dimension `nsd` is the default mesh. Most methods take
  `dim` and use `nsd` when `dim` is absent.
- A mesh of one dimension holds the elements of all entities of that
  dimension.
- An entity is a geometric piece, such as one surface of the geometry.
- The entity number of an element is its mesh id.
- Method `GetDimEntityNum` returns `[dim, entityNum]` for an element
  number.
- The domain owns its meshes. `DEALLOCATE` on the domain frees them. A
  pointer from `GetMeshPointer` is then dangling.

## The mesh file

- Gmsh writes the mesh as a `.msh` file.
- The program `msh2hdf5.F90` reads the `.msh` file with `MSHFile_` and
  calls `Export` to write an HDF5 file.
  See `classes:src/modules/FEMesh/examples/meshdata/msh2hdf5.F90`.
- `FEDomain_%Initiate(hdf5, group)` reads that HDF5 file. Pass `""` as
  the group when the data is at the root of the file.
- Test meshes are in `examples/meshdata/` of the `FEDomain`, `FEMesh`
  and `MeshSelection` modules.

## Who uses the domain

- `FEDOF_` stores a pointer to the domain (`dom`). It numbers degrees
  of freedom on the meshes of the domain.
  See [DOF numbering](fedof-dof-numbering.md).
- Node fields (`ScalarField_`, `VectorField_`, ...) use `FEDOF_`
  objects. They reach the domain through them.
- `MeshSelection_` picks elements by mesh id, element number, node
  number or bounding box. Methods with a `dom` argument turn mesh ids
  into element numbers.
- Boundary conditions use `MeshSelection_` to say where they apply.

## Gotchas

- Error checks and `[START]`/`[END]` messages exist only in a Debug
  build (`DEBUG_VER`). A Release build does no checks.
- `AbstractMesh_`, `FEDomain_` and `HDF5File_` live in very large
  files. Read them by section.
- Some directories under `src/modules` are not built. Check the
  `CMakeLists.txt` before you rely on a module.
- Prefer the `Abstract*` hierarchies over the legacy modules.

## Related entries

- [Mesh numbering and element data](mesh-numbering-and-data.md)
- [Read a mesh and query it](../recipes/fedomain-read-and-query.md)
- [Elements and numbers](../recipes/fedomain-elements-connectivity.md)
- [Boundary and facets](../recipes/fedomain-boundary-facets.md)
