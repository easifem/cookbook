# VectorField: Setting values

**Purpose.** Set the values of a `VectorField_` (and of a
`VectorFieldLis_`, which keeps the same API on a LIS vector): by node
and space component (`Set`), from rank-2 arrays in nodes or DOF
format, from an `FEVariable_`, from other fields (`Set(VALUE=field)`),
and by index of the value vector (`SetSingle`, `SetAll`,
`SetMultiple`).

**Classes.** `VectorField_` (`VectorField_Class`), which extends
`AbstractNodeField_`, and `VectorFieldLis_` (`VectorFieldLis_Class`),
which extends `VectorField_`. Interfaces:
`classes:src/modules/VectorField/src/VectorField_Class.F90`,
`classes:src/modules/VectorFieldLis/src/VectorFieldLis_Class.F90`.
Implementations: `@SetMethods.F90` in
`classes:src/submodules/VectorField/src/` and
`classes:src/submodules/VectorFieldLis/src/`. The index methods are
described in
[ScalarField: Setting and Getting values](scalarfield-set-get.md);
the BLAS methods in
[VectorField: BLAS methods](vectorfield-blas.md). Getting values:
[VectorField: Getting values](vectorfield-get.md).

## Steps

1. **Data layout.** One physical variable, `spaceCompo` space
   components, one time component; `idofs = [1, ..., spaceCompo]`.
   `Size() = fedof%GetTotalDOF() * spaceCompo`. Values are stored in
   DOF format: component 1 of all DOFs, then component 2, ..., so
   component `c` of DOF (node) `i` is index `(c - 1) * tNodes + i`
   (`obj_Initiate2`, `@ConstructorMethods.F90` in
   `classes:src/submodules/VectorField/src/`).
   With `VectorField_test.toml` (`square_3x2.h5`, six nodes, order 1,
   `spaceCompo = 2`) `Size() = 12`
   (`classes:src/modules/VectorField/examples/Initiate_test_1.F90`),
   and node 3 is index 3 (component 1) and 9 (component 2)
   (`classes:src/modules/VectorField/examples/Set_test_1.F90`).
2. **Initiate.** `dom%ImportFromToml(filename=, tomlName="domain")`,
   then `u%ImportFromToml(fedof=, geofedof=, dom=, filename=,
   tomlName="u")`. More fields on the same FEDOF:
   `v%Initiate(NAME=, engine="NATIVE_SERIAL", spaceCompo=, fedof=,
   geofedof=)` (`spaceCompo` is required).
3. **Set** (generic `Set`, Set1..Set13). Unless noted, each takes
   optional `scale` (default 1) and `addContribution` (default false):
   the entries become `scale * VALUE`, or `scale * VALUE` is added.
   - Set12 `Set(VALUE)`, scalar: all entries (`SetAll`).
   - Set2 `Set(VALUE(:))`: all nodes to one vector,
     `SIZE(VALUE) = spaceCompo`.
   - Set3 `Set(VALUE, spaceCompo)`: one component of all nodes, one
     value.
   - Set5 `Set(VALUE(:), spaceCompo)`: one component of all nodes,
     `SIZE(VALUE) = tNodes`.
   - Set1 `Set(globalNode, islocal, VALUE(:))`: the vector of one
     node, `SIZE(VALUE) = spaceCompo`.
   - Set10 `Set(VALUE, globalNode, islocal, spaceCompo)`: one entry
     (`SetSingle`).
   - Set7 `Set(globalNode(:), islocal, VALUE(:))`: the same vector at
     the selected nodes (calls Set1 for each node).
   - Set9 `Set(VALUE(:), globalNode(:), islocal, spaceCompo)`: one
     component of the selected nodes, `VALUE(j)` for `globalNode(j)`.
   - Set4 `Set(VALUE(:, :), storageFMT)`: all entries. Nodes format
     (`TypeFieldOpt%storageFormatNodes`): `VALUE(c, i)`, shape
     `[spaceCompo, tNodes]`; DOF format: `VALUE(i, c)`.
   - Set8 `Set(globalNode(:), islocal, VALUE(:, :), storageFMT)`: the
     selected nodes; nodes `VALUE(c, j)`, DOF `VALUE(j, c)`.
   - Set11 `Set(VALUE=fevar, globalNode(:), islocal)`: a vector, nodal
     `FEVariable_`; constant: one vector for all nodes (Set7); space:
     shape `[spaceCompo, SIZE(globalNode)]` (Set8, nodes format).
   - Set6 `Set(VALUE=field, spaceCompo)`: one component from a node
     field with one value per node (e.g. a `ScalarField_` on the same
     FEDOF). Calls `SetMultiple5`, so `field` may use any engine.
   - Set13 `Set(VALUE=field)`: copy all values of another
     `VectorField_` of any engine. No `scale`, no `addContribution`.
4. **Other setters.** `SetByFunction(func, [times, spaceCompo])`
   (vector function: all components; scalar function: component
   `spaceCompo`), `SetLagrangeDOF(obj2)`, `SetHigherOrderNodeCoord()`,
   `SetFromToml`. See `SetByFunction_test_1.F90`,
   `SetLagrangeDOF_test_1.F90`.
5. **By index.** `SetSingle`, `SetAll`, `SetMultiple`, `GetSingle`,
   `GetMultiple` of `AbstractNodeField_` (overridden by
   `VectorFieldLis_`) take indices into the value vector (step 1). To
   set all `Size()` entries from one array use `SetMultiple(istart=1,
   iend=u%Size(), stride=1, VALUE=)`.

Native engine (trimmed from `Set_test_1`, `Set_test_3`, `Set_test_4`
and `Set_test_6` of `VectorField`; all use `VectorField_test.toml`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE ExceptionHandler_Class, ONLY: EXCEPTION_INFORMATION
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE FieldOpt_Class, ONLY: TypeFieldOpt
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE Test_Method, ONLY: OK
USE VectorField_Class, ONLY: VectorField_

CHARACTER(*), PARAMETER :: tomlFileName = "VectorField_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(VectorField_) :: u, v
REAL(DFP) :: raw(12), vec(6), val, src(6), want(12)
REAL(DFP) :: xn(2, 6), xd(6, 2)
INTEGER(I4B) :: tsize, nrow, ncol, ii

CALL e%SetQuietMode(EXCEPTION_INFORMATION, math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL v%Initiate(NAME="v", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)

! one node: vector, then add 2 * [1, 1]
CALL u%Set(VALUE=0.0_DFP)
CALL u%Set(globalNode=3, islocal=math%yes, VALUE=[1.0_DFP, 2.0_DFP])
CALL u%GetMultiple(istart=1, iend=12, stride=1, VALUE=raw, &
                   tsize=tsize)
CALL OK(ABS(raw(3) - 1.0_DFP) .LT. tol .AND. &
        ABS(raw(9) - 2.0_DFP) .LT. tol, "Set node: DOF storage")
CALL u%Set(globalNode=3, islocal=math%yes, VALUE=[1.0_DFP, 1.0_DFP], &
           scale=2.0_DFP, addContribution=math%yes)
CALL u%Get(VALUE=vec, tsize=tsize, globalNode=3)
CALL OK(ALL(ABS(vec(1:2) - [3.0_DFP, 4.0_DFP]) .LT. tol), &
        "Set node: add 2 * value")

! one entry
CALL u%Set(VALUE=7.0_DFP, globalNode=4, islocal=math%yes, spaceCompo=2)
CALL u%Get(VALUE=val, globalNode=4, islocal=math%yes, spaceCompo=2)

! one component: all nodes, then selected nodes
src = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL u%Set(VALUE=-1.0_DFP, spaceCompo=2)
CALL u%Set(VALUE=src, spaceCompo=1)
CALL u%Set(VALUE=[10.0_DFP, 20.0_DFP], globalNode=[2, 5], &
           islocal=math%yes, spaceCompo=2)
CALL u%Get(VALUE=vec, tsize=tsize, globalNode=[5, 2, 1], &
           islocal=math%yes, spaceCompo=2)
CALL OK(ALL(ABS(vec(1:3) - [20.0_DFP, 10.0_DFP, -1.0_DFP]) .LT. tol), &
        "Set selected component")

! rank 2: set in nodes format, get in DOF format
DO ii = 1, 6
  xn(:, ii) = [REAL(ii, DFP), 10.0_DFP * ii]
END DO
CALL u%Set(VALUE=xn, storageFMT=TypeFieldOpt%storageFormatNodes)
CALL u%Get(VALUE=xd, nrow=nrow, ncol=ncol, &
           storageFMT=TypeFieldOpt%storageFormatDOF)
CALL OK(nrow .EQ. 6 .AND. ncol .EQ. 2, "Get DOF format: nrow, ncol")
CALL OK(ALL(ABS(xd - TRANSPOSE(xn)) .LT. tol), &
        "Set nodes format, Get DOF format")

! from another field
want = [(REAL(ii, DFP), ii=1, 12)]
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=want)
CALL v%Set(VALUE=u)
CALL v%GetMultiple(istart=1, iend=12, stride=1, VALUE=raw, &
                   tsize=tsize)
CALL OK(ALL(ABS(raw - want) .LT. tol), "Set(VALUE=u): v = u")

CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
```

Across engines (trimmed from `Set_test_2` and `SetMultiple_test_1` of
`VectorFieldLis`; `VectorFieldLis_test.toml` has `engine = "LIS_OMP"`):

```fortran
! other USE items, dom, fedof, geofedof, tol, ii, tsize: as above
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE ScalarFieldLis_Class, ONLY: ScalarFieldLis_
USE VectorField_Class, ONLY: VectorField_
USE VectorFieldLis_Class, ONLY: VectorFieldLis_

TYPE(LisOmpEngine_) :: lis
TYPE(VectorFieldLis_) :: u, w
TYPE(VectorField_) :: n
TYPE(ScalarFieldLis_) :: s
REAL(DFP) :: want(12), found(12), s6(6)

CALL lis%Initiate()
! ... dom%ImportFromToml, u%ImportFromToml with VectorFieldLis_test.toml
CALL w%Initiate(NAME="w", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
CALL s%Initiate(NAME="s", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
want = [(REAL(ii, DFP), ii=1, 12)]
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=want)

CALL n%Set(VALUE=u)                       ! native <- LIS
CALL w%Set(VALUE=u)                       ! LIS <- LIS
CALL n%SetMultiple(istart=1, iend=12, stride=1, VALUE=-want)
CALL w%Set(VALUE=n)                       ! LIS <- native
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found + want) .LT. tol), "w = n")

! component 2 of a LIS vector field from a LIS scalar field (Set6)
s6 = [10.0_DFP, 20.0_DFP, 30.0_DFP, 40.0_DFP, 50.0_DFP, 60.0_DFP]
CALL s%SetMultiple(istart=1, iend=6, stride=1, VALUE=s6)
CALL u%Set(VALUE=s, spaceCompo=2)
CALL u%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found(7:12) - s6) .LT. tol), "Set6: component 2")

CALL s%DEALLOCATE()
CALL n%DEALLOCATE()
CALL w%DEALLOCATE()
CALL u%DEALLOCATE()
! ... fedof, geofedof, dom
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/VectorField/examples/Set_test_1.F90` (node,
  one entry, Set7)
- `classes:src/modules/VectorField/examples/Set_test_2.F90` (Set2)
- `classes:src/modules/VectorField/examples/Set_test_3.F90` (Set3,
  Set5, Set9)
- `classes:src/modules/VectorField/examples/Set_test_4.F90` (Set4,
  Set8)
- `classes:src/modules/VectorField/examples/Set_test_5.F90`
  (`FEVariable_`: Set11)
- `classes:src/modules/VectorField/examples/Set_test_6.F90` (Set13)
- `classes:src/modules/VectorField/examples/Set_test_7.F90` (Set6)
- `classes:src/modules/VectorField/examples/SetByFunction_test_1.F90`
- `classes:src/modules/VectorField/examples/SetLagrangeDOF_test_1.F90`
- `classes:src/modules/VectorField/examples/VectorField_test.toml`
- `classes:src/modules/VectorFieldLis/examples/Set_test_1.F90`
  (Set on LIS)
- `classes:src/modules/VectorFieldLis/examples/Set_test_2.F90` (Set13
  across engines)
- `classes:src/modules/VectorFieldLis/examples/SetMultiple_test_1.F90`
  (index methods on LIS, Set2, Set6)

## Pitfalls

- `Set(VALUE(:))` (Set2) sets **every node to one vector**
  (`SIZE(VALUE) = spaceCompo`); in `ScalarField_` the same call sets
  all entries from an array. To fill all `Size()` entries use
  `SetMultiple(istart=1, iend=u%Size(), stride=1, VALUE=)`.
- Without `addContribution` the result is `scale * VALUE`, not `VALUE`
  (every form calls `SetSingle`, `SetAll` or `SetMultiple` with
  `scale`).
- `globalNode` must hold **local** node (DOF) numbers. Pass
  `islocal=math%yes` in every form that has it; a debug build raises
  "global nodes are not local nodes" for `islocal = .FALSE.` in Set1,
  Set9, Set10, Get3, Get4 and Get5
  (`classes:src/submodules/VectorField/src/localNodeError.F90`).
  Get1, Get2 and `GetFEVariable` have no (or ignore) `islocal`; their
  `globalNode` is local too.
- `VectorField_` has no `ASSIGNMENT(=)` (unlike `ScalarField_`), so
  `v = u` is the intrinsic assignment: it copies the components,
  including the FEDOF pointers and the LIS handle `lis_ptr`. Use
  `v%Set(VALUE=u)` or `u%Get(VALUE=v)`; `v` must be initiated.
- Set13 has no `scale`/`addContribution`. For `v = v + a * u` use
  `v%AXPY(x=u, scale=a)` (same engine) or `SetMultiple` with
  `VALUE=u`, `scale`, `addContribution` (any engine).
- Set1 to Set11 raise an error for a constant field (`fieldType =
  TypeFieldOpt%constant`) in debug builds.
- Native vs LIS engine:
  - `VectorFieldLis_%GetPointer()` returns `NULL()` (debug error); its
    `realVec` is only filled by `Display` and `Export`.
  - Set13 on a native `obj`: native `VALUE` through `GetPointer`,
    other engines through a temporary array. Set13 on a LIS `obj`
    (overridden): `VectorField_` through `GetPointer`,
    `VectorFieldLis_` through `lis_vector_copy`; other types are
    ignored (debug error) (`@SetMethods.F90` in
    `classes:src/submodules/VectorFieldLis/src/`).
  - Start LIS (`LisOmpEngine_%Initiate`) before initiating a
    `VectorFieldLis_` and stop it after all LIS fields are
    deallocated.
