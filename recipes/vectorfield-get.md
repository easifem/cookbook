# VectorField: Getting values

**Purpose.** Read the values of a `VectorField_` (and of a
`VectorFieldLis_`, which keeps the same API on a LIS vector): by node
and space component (`Get`), into rank-2 arrays in nodes or DOF
format, into an `FEVariable_` (`Get`, `GetFEVariable`), into another
field (`Get(VALUE=field)`), and by index of the value vector
(`GetSingle`, `GetMultiple`).

**Classes.** `VectorField_` (`VectorField_Class`), which extends
`AbstractNodeField_`, and `VectorFieldLis_` (`VectorFieldLis_Class`),
which extends `VectorField_`. Interfaces:
`classes:src/modules/VectorField/src/VectorField_Class.F90`,
`classes:src/modules/VectorFieldLis/src/VectorFieldLis_Class.F90`.
Implementations: `@GetMethods.F90` in
`classes:src/submodules/VectorField/src/` and
`classes:src/submodules/VectorFieldLis/src/`. The index methods are
described in
[ScalarField: Setting and Getting values](scalarfield-set-get.md);
the BLAS methods in
[VectorField: BLAS methods](vectorfield-blas.md). Setting values:
[VectorField: Setting values](vectorfield-set.md).

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
3. **Get** (generic `Get`, Get1..Get7).
   - Get5 `Get(VALUE, globalNode, islocal, spaceCompo)`: one entry.
   - Get1 `Get(VALUE(:), tsize, globalNode)`: the vector of one node,
     `tsize = spaceCompo`; `Get(VALUE(:), tsize, spaceCompo)`: one
     component of all nodes, `tsize = tNodes`. Give exactly one of
     `globalNode` and `spaceCompo`. No `islocal` argument.
   - Get4 `Get(VALUE(:), tsize, globalNode(:), islocal, spaceCompo)`:
     one component of the selected nodes, `tsize = SIZE(globalNode)`.
   - Get2 `Get(VALUE(:, :), nrow, ncol, storageFMT)`: all entries;
     nodes format `nrow = spaceCompo`, `ncol = tNodes`; DOF format the
     transpose.
   - Get3 `Get(VALUE(:, :), nrow, ncol, storageFMT, globalNode(:),
     islocal)`: the selected nodes, same layout as Set8.
   - Get6 `Get(VALUE=fevar, globalNode(:), islocal)` and
     `GetFEVariable(globalNode, islocal, VALUE)`: vector, nodal, space
     `FEVariable_`, column `j` is node `globalNode(j)`.
   - Get7 `Get(VALUE=field)`: copy into another vector field; calls
     `field%Set(VALUE=obj)` (Set13), so engines may differ.
4. **By index.** `SetSingle`, `SetAll`, `SetMultiple`, `GetSingle`,
   `GetMultiple` of `AbstractNodeField_` (overridden by
   `VectorFieldLis_`) take indices into the value vector (step 1). To
   set all `Size()` entries from one array use `SetMultiple(istart=1,
   iend=u%Size(), stride=1, VALUE=)`.

Native engine (trimmed from `Set_test_1`, `Set_test_3`, `Set_test_4`,
`Set_test_5` and `Set_test_6` of `VectorField`; all use
`VectorField_test.toml`; each block starts from the values the test
sets just before):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE BaseType, ONLY: FEVariable_
USE BaseType, ONLY: TypeFEVariableConstant
USE BaseType, ONLY: TypeFEVariableSpace
USE BaseType, ONLY: TypeFEVariableVector
USE ExceptionHandler_Class, ONLY: e
USE ExceptionHandler_Class, ONLY: EXCEPTION_INFORMATION
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE FEVariable_Method, ONLY: NodalVariable
USE FieldOpt_Class, ONLY: TypeFieldOpt
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE Test_Method, ONLY: OK
USE VectorField_Class, ONLY: VectorField_

CHARACTER(*), PARAMETER :: tomlFileName = "VectorField_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(VectorField_) :: u, v, w
TYPE(FEVariable_) :: fevar
REAL(DFP) :: raw(12), vec(6), val, src(6), want(12)
REAL(DFP) :: xn(2, 6), xd(6, 2)
INTEGER(I4B) :: tsize, nrow, ncol, ii

CALL e%SetQuietMode(EXCEPTION_INFORMATION, math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL v%Initiate(NAME="v", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
CALL w%Initiate(NAME="w", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)

! Get1 (node), Get5 (one entry), Get1 (component)   [Set_test_1]
CALL u%Set(VALUE=0.0_DFP)
CALL u%Set(globalNode=3, islocal=math%yes, VALUE=[1.0_DFP, 2.0_DFP])
CALL u%Get(VALUE=vec, tsize=tsize, globalNode=3)
CALL OK(tsize .EQ. 2, "Get node: tsize")
CALL OK(ALL(ABS(vec(1:2) - [1.0_DFP, 2.0_DFP]) .LT. tol), "Get node")
CALL u%Set(globalNode=3, islocal=math%yes, VALUE=[1.0_DFP, 1.0_DFP], &
           scale=2.0_DFP, addContribution=math%yes)
CALL u%Set(VALUE=7.0_DFP, globalNode=4, islocal=math%yes, spaceCompo=2)
CALL u%Get(VALUE=val, globalNode=4, islocal=math%yes, spaceCompo=2)
CALL OK(ABS(val - 7.0_DFP) .LT. tol, "Set/Get one value")
CALL u%Set(globalNode=[1, 2], islocal=math%yes, &
           VALUE=[5.0_DFP, 6.0_DFP])
CALL u%Get(VALUE=vec, tsize=tsize, spaceCompo=1)
CALL OK(tsize .EQ. 6, "Get component: tsize")
CALL OK(ALL(ABS(vec - [5.0_DFP, 5.0_DFP, 3.0_DFP, 0.0_DFP, 0.0_DFP, &
                       0.0_DFP]) .LT. tol), "Get component 1")

! Get4: one component of selected nodes   [Set_test_3]
src = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL u%Set(VALUE=-1.0_DFP, spaceCompo=2)
CALL u%Set(VALUE=src, spaceCompo=1)
CALL u%Set(VALUE=[10.0_DFP, 20.0_DFP], globalNode=[2, 5], &
           islocal=math%yes, spaceCompo=2)
CALL u%Get(VALUE=vec, tsize=tsize, globalNode=[5, 2, 1], &
           islocal=math%yes, spaceCompo=2)
CALL OK(tsize .EQ. 3, "Get selected component: tsize")
CALL OK(ALL(ABS(vec(1:3) - [20.0_DFP, 10.0_DFP, -1.0_DFP]) .LT. tol), &
        "Set selected component")

! Get2: rank 2, nodes format in, DOF format out   [Set_test_4]
DO ii = 1, 6
  xn(:, ii) = [REAL(ii, DFP), 10.0_DFP * ii]
END DO
CALL u%Set(VALUE=xn, storageFMT=TypeFieldOpt%storageFormatNodes)
CALL u%Get(VALUE=xd, nrow=nrow, ncol=ncol, &
           storageFMT=TypeFieldOpt%storageFormatDOF)
CALL OK(nrow .EQ. 6 .AND. ncol .EQ. 2, "Get DOF format: nrow, ncol")
CALL OK(ALL(ABS(xd - TRANSPOSE(xn)) .LT. tol), &
        "Set nodes format, Get DOF format")

! Get6 and GetFEVariable   [Set_test_5]
CALL u%Set(VALUE=0.0_DFP)
fevar = NodalVariable([1.0_DFP, 2.0_DFP], TypeFEVariableVector, &
                      TypeFEVariableConstant)
CALL u%Set(VALUE=fevar, globalNode=[3, 4], islocal=math%yes)
fevar = NodalVariable(RESHAPE([5.0_DFP, 6.0_DFP, 7.0_DFP, 8.0_DFP], &
                              [2, 2]), TypeFEVariableVector, &
                      TypeFEVariableSpace)
CALL u%Set(VALUE=fevar, globalNode=[5, 6], islocal=math%yes)
CALL u%Get(VALUE=fevar, globalNode=[6, 3], islocal=math%yes)
CALL OK(ALL(fevar%s(1:2) .EQ. [2, 2]), "Get FEVariable: shape")
CALL OK(ALL(ABS(fevar%val(1:4) - [7.0_DFP, 8.0_DFP, 1.0_DFP, &
                                  2.0_DFP]) .LT. tol), &
        "Get FEVariable: values")
CALL u%GetFEVariable(globalNode=[5], islocal=math%yes, VALUE=fevar)
CALL OK(ALL(ABS(fevar%val(1:2) - [5.0_DFP, 6.0_DFP]) .LT. tol), &
        "GetFEVariable")

! Get7: copy into another vector field   [Set_test_6]
want = [(REAL(ii, DFP), ii=1, 12)]
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=want)
CALL v%Set(VALUE=u)
CALL v%Get(VALUE=w)
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=raw, &
                   tsize=tsize)
CALL OK(ALL(ABS(raw - want) .LT. tol), "Get(VALUE=w): w = v")

CALL w%DEALLOCATE()
CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
```

The LIS engine uses the same calls; see `Set_test_1` and
`SetMultiple_test_1` of `VectorFieldLis` and the cross-engine snippet
in [VectorField: Setting values](vectorfield-set.md).

## Example files (run from the `examples` directory)

- `classes:src/modules/VectorField/examples/Set_test_1.F90` (Get1,
  Get5)
- `classes:src/modules/VectorField/examples/Set_test_3.F90` (Get4)
- `classes:src/modules/VectorField/examples/Set_test_4.F90` (Get2,
  Get3)
- `classes:src/modules/VectorField/examples/Set_test_5.F90` (Get6,
  `GetFEVariable`)
- `classes:src/modules/VectorField/examples/Set_test_6.F90` (Get7)
- `classes:src/modules/VectorField/examples/VectorField_test.toml`
- `classes:src/modules/VectorFieldLis/examples/Set_test_1.F90`
  (Get on LIS)
- `classes:src/modules/VectorFieldLis/examples/SetMultiple_test_1.F90`
  (`GetSingle`, `GetMultiple` on LIS)

## Pitfalls

- `globalNode` must hold **local** node (DOF) numbers. Pass
  `islocal=math%yes` in every form that has it; a debug build raises
  "global nodes are not local nodes" for `islocal = .FALSE.` in Set1,
  Set9, Set10, Get3, Get4 and Get5
  (`classes:src/submodules/VectorField/src/localNodeError.F90`).
  Get1, Get2 and `GetFEVariable` have no (or ignore) `islocal`; their
  `globalNode` is local too.
- Get1: give `globalNode` **or** `spaceCompo`, not both (checked in
  debug builds). `VALUE` must hold `spaceCompo` or `tNodes` entries.
- Get2/Get3: `VALUE` must be at least `nrow x ncol` of the chosen
  format; it is not reallocated. `force3D` is not used.
- Get7 (`Get(VALUE=field)`) calls `field%Set(VALUE=obj)`, so `field`
  must be initiated; see Set13 in
  [VectorField: Setting values](vectorfield-set.md).
- Native vs LIS engine:
  - `VectorFieldLis_%GetPointer()` returns `NULL()` (debug error); its
    `realVec` is only filled by `Display` and `Export`.
  - Get2/Get3 read `realVec` directly only for `engine =
    "NATIVE_SERIAL"`; other engines go through `GetMultiple`.
  - Start LIS (`LisOmpEngine_%Initiate`) before initiating a
    `VectorFieldLis_` and stop it after all LIS fields are
    deallocated.
