# STScalarField: Setting and Getting values

**Purpose.** Set and read the values of a space-time scalar field
`STScalarField_`: by node and time component (`Set`, `Get`), from rank-2
arrays and `FEVariable_`, from other fields (`Set(VALUE=field)`, `=`,
`SetFromScalarField`, `SetToScalarField`), from a user function
(`SetByFunction`), and by index of the value vector (`SetSingle`,
`SetMultiple`, `GetSingle`, `GetMultiple`). The LIS engine
(`STScalarFieldLis_`, same API) has its own recipes:
[Getting values](stscalarfieldlis-get.md),
[Setting values](stscalarfieldlis-set.md),
[BLAS methods](stscalarfieldlis-blas.md).

**Classes.** `STScalarField_` (`STScalarField_Class`), which extends
`AbstractNodeField_`. Interface:
`classes:src/modules/STScalarField/src/STScalarField_Class.F90`.
Implementations: `@SetMethods.F90` and `@GetMethods.F90` in
`classes:src/submodules/STScalarField/src/`. The index methods are
the ones of the ScalarField recipe
([ScalarField: Setting and Getting values](scalarfield-set-get.md)).

## Steps

1. **Data layout.** A space-time field has one physical variable, one
   space component and `timeCompo` time components. `Initiate` takes
   `timeCompo = timefedof%GetTotalDOF()` when `timefedof` is given and
   initiated, else the integer `timeCompo`; `idofs = [1, ..., timeCompo]`; the
   size is `fedof%GetTotalDOF() * timeCompo` (`obj_Initiate2`,
   `@ConstructorMethods.F90` in `classes:src/submodules/STScalarField/src/`).
   Values are stored in DOF format: all space DOFs of time component 1,
   then all of time component 2, ... The value of space DOF `i` (node
   `i` for order 1 Lagrange) at time component `a` has index
   `(a - 1) * tNodes + i`. With `STScalarField_test.toml` (six nodes,
   order 1 in space and time) `timeCompo = 2`, `Size() = 12`, and node
   2 is index 2 (time 1) and 8 (time 2) (`CALL OK` in
   `classes:src/modules/STScalarField/examples/Set_test_1.F90` and
   `classes:src/modules/STScalarField/examples/Initiate_test_1.F90`).
   In a `ScalarField_` node, DOF and index are the same number; here
   node and index differ, so use `Set`/`Get` with `globalNode` and
   `timeCompo`, or compute the index as above for `SetMultiple`.
2. **Initiate.** `dom%ImportFromToml(filename=, tomlName="domain")`,
   then `u%ImportFromToml(tomlName="u", filename=, fedof=, geofedof=,
   timefedof=, dom=)`. More fields on the same FEDOFs:
   `v%Initiate(NAME=, engine="NATIVE_SERIAL", fedof=, geofedof=,
   timefedof=)`, or `timeCompo=3` without `timefedof`
   (`classes:src/modules/STScalarField/examples/Initiate_test_1.F90`).
3. **Set** (generic `Set`, Set1..Set14). Unless noted, each takes
   optional `scale` (default 1) and `addContribution` (default false):
   the entries become `scale * VALUE`, or `scale * VALUE` is added.
   - Set12 `Set(VALUE)`, scalar: all entries (`SetAll`).
   - Set2 `Set(VALUE(:))`: time component `a` of all nodes to
     `VALUE(a)`, `SIZE(VALUE) = timeCompo`.
   - Set3 `Set(VALUE, timeCompo)`: one time component, one value.
   - Set5 `Set(VALUE(:), timeCompo)`: one time component from a vector,
     `SIZE(VALUE) = tNodes`.
   - Set1 `Set(globalNode, islocal, VALUE(:))`: all time components of
     one node, `VALUE(a)` for time `a`.
   - Set10 `Set(VALUE, globalNode, islocal, timeCompo)`: one entry
     (`SetSingle`).
   - Set7 `Set(VALUE(:), globalNode(:), islocal)`: all time components
     of the selected nodes, the same `VALUE(1:timeCompo)` for each.
   - Set9 `Set(VALUE(:), globalNode(:), islocal, timeCompo)`: one time
     component of the selected nodes, `VALUE(j)` for `globalNode(j)`.
   - Set4 `Set(VALUE(:, :), storageFMT)`: all entries. DOF format
     (`TypeFieldOpt%storageFormatDOF`): `VALUE(i, a)`, shape
     `[tNodes, timeCompo]`; NODES format: `VALUE(a, i)`.
   - Set8 `Set(globalNode(:), islocal, VALUE(:, :), storageFMT)`: the
     selected nodes; NODES `VALUE(a, j)`, DOF `VALUE(j, a)`.
   - Set11 `Set(VALUE=fevar, globalNode(:), islocal)`: a nodal, scalar,
     space-time `FEVariable_` with `val(j, a)` (space first, the
     easifemBase layout); set by Set8 in DOF format.
   - Set6 `Set(objTimeCompo, VALUE=field, valueTimeCompo)`: one time
     component from a time component of another `STScalarField_`
     (calls `SetMultiple5`).
   - Set13 `Set(VALUE=field)` and `v = u` (`ASSIGNMENT(=)`): copy all
     values of another `STScalarField_`. No `scale`, no
     `addContribution`; calls Set14.
   - Set14 `Set(VALUE=field, scale, addContribution)`, both required:
     `v = [v +] scale * u`. A native `VALUE` is read through
     `GetPointer`. Copies to or from a LIS field:
     [STScalarFieldLis: Setting values](stscalarfieldlis-set.md).
4. **Other setters.** `SetFromScalarField(timeCompo, VALUE=s, [scale,
   addContribution])` sets one time component from a `ScalarField_`;
   `SetToScalarField(timeCompo, VALUE=s, ...)` writes one time
   component into `s`. Both call `SetMultiple5`
   (`classes:src/modules/STScalarField/examples/Set_test_4.F90`).
   `SetByFunction(func, [times])` evaluates `func(x, y, z, t)`
   at the mesh nodes; time component `a` uses `t = times(a)`,
   `SIZE(times) = timeCompo`; without `times`, `t = 0` for all.
5. **Get** (generic `Get`, Get1..Get6; `ans` sizes are not reallocated):
   - Get1 `Get(VALUE(:), tsize, globalNode=, [islocal])`: all time
     components of one node, `tsize = timeCompo`. The number is a local
     node number; `islocal`, if given, must be true (debug check).
   - Get1 `Get(VALUE(:), tsize, timeCompo=)`: all nodes of one time
     component, `tsize = tNodes`. Give exactly one of `globalNode` and
     `timeCompo`.
   - Get4 `Get(VALUE(:), globalNode(:), tsize, islocal, timeCompo)`:
     selected nodes of one time component.
   - Get5 `Get(VALUE, globalNode, islocal, timeCompo)`: one value
     (`GetSingle`).
   - Get2 `Get(VALUE(:, :), nrow, ncol, storageFMT)`: all values; NODES
     gives `VALUE(a, i)` (`nrow = timeCompo`), DOF gives `VALUE(i, a)`.
   - Get3 `Get(VALUE(:, :), nrow, ncol, globalNode(:), islocal,
     storageFMT)`: the same for the selected nodes.
   - Get6 `Get(VALUE=fevar, globalNode(:), islocal)` and
     `GetFEVariable(globalNode, islocal, VALUE)`: nodal space-time
     `FEVariable_`, `val(j, a)`, `s = [SIZE(globalNode), timeCompo]`.
   - There is no `Get` into a `ScalarField_`; use `SetToScalarField`.

By node and time component, native engine (trimmed from `Set_test_1`,
`Set_test_2`, `Set_test_4`, `Set_test_5` and `Get_test_1` of
`STScalarField`; all use `STScalarField_test.toml`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE FieldOpt_Class, ONLY: TypeFieldOpt
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE STScalarField_Class, ONLY: STScalarField_
USE Test_Method, ONLY: OK
USE TimeFEDOF_Class, ONLY: TimeFEDOF_

CHARACTER(*), PARAMETER :: tomlFileName = "STScalarField_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STScalarField_) :: u, v
REAL(DFP) :: found(12), src(12), val, v2(6, 6)
INTEGER(I4B) :: ii, tsize, nrow, ncol

CALL e%SetQuietMode(math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
CALL v%Initiate(NAME="v", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)

! all time components of node 2 (Set1), then add 2 * [1, 1]
CALL u%Set(VALUE=1.0_DFP)
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=[5.0_DFP, 6.0_DFP])
CALL u%GetMultiple(indx=[2, 8], VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found(1:2) - [5.0_DFP, 6.0_DFP]) .LT. tol), &
        "Set node: DOF format")
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=[1.0_DFP, 1.0_DFP], &
           scale=2.0_DFP, addContribution=math%yes)

! one entry (Set10, Get5)
CALL u%Set(VALUE=9.0_DFP, globalNode=3, islocal=math%yes, timeCompo=2)
CALL u%Get(VALUE=val, globalNode=3, islocal=math%yes, timeCompo=2)

! one time component (Set3), selected nodes of it (Set9, Get4)
CALL u%Set(VALUE=4.0_DFP, timeCompo=1)
CALL u%Set(VALUE=[10.0_DFP, 20.0_DFP], globalNode=[1, 3], &
           islocal=math%yes, timeCompo=1)
CALL u%Get(VALUE=found, globalNode=[1, 3], tsize=tsize, &
           islocal=math%yes, timeCompo=1)

! entry k = k; node 4 holds [4, 10]; time 2 holds src(7:12)
src = [(REAL(ii, DFP), ii=1, 12)]
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)
CALL u%Get(VALUE=found, tsize=tsize, globalNode=4)
CALL OK(ALL(ABS(found(1:2) - [4.0_DFP, 10.0_DFP]) .LT. tol), &
        "node: values")
CALL u%Get(VALUE=found, tsize=tsize, timeCompo=2)
CALL OK(tsize .EQ. 6, "timeCompo: tsize")
CALL u%Get(VALUE=v2, nrow=nrow, ncol=ncol, &
           storageFMT=TypeFieldOpt%storageFormatNodes)
CALL OK(nrow .EQ. 2 .AND. ncol .EQ. 6, "all, NODES: shape")

! from another field (Set6): u(time 2) = u(time 2) + 2 * v(time 1)
CALL v%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)
CALL u%Set(VALUE=1.0_DFP)
CALL u%Set(objTimeCompo=2, VALUE=v, valueTimeCompo=1, scale=2.0_DFP, &
           addContribution=math%yes)
CALL u%Get(VALUE=found, tsize=tsize, timeCompo=2)
CALL OK(ALL(ABS(found(1:6) - (1.0_DFP + 2.0_DFP * src(1:6))) .LT. tol), &
        "add: time 2")
CALL v%Set(VALUE=u)                                 ! copy (Set13)
CALL v%Set(VALUE=u, scale=2.0_DFP, addContribution=math%yes)  ! Set14

CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STScalarField/examples/Set_test_1.F90` (all,
  node, single, one value per time component)
- `classes:src/modules/STScalarField/examples/Set_test_2.F90` (one time
  component, selected nodes)
- `classes:src/modules/STScalarField/examples/Set_test_3.F90` (rank-2
  arrays, DOF and NODES format)
- `classes:src/modules/STScalarField/examples/Set_test_4.F90`
  (`FEVariable_`, Set13, Set14, `v = u`, `SetFromScalarField`,
  `SetToScalarField`)
- `classes:src/modules/STScalarField/examples/Set_test_5.F90` (Set6)
- `classes:src/modules/STScalarField/examples/Get_test_1.F90` (all Get
  forms)
- `classes:src/modules/STScalarField/examples/SetByFunction_test_1.F90`
- `classes:src/modules/STScalarField/examples/Import_test_1.F90`
- `classes:src/modules/STScalarField/examples/STScalarField_test.toml`

## Pitfalls

- `globalNode` must hold **local** node numbers: Set1, Set9, Set10,
  Set11, Get3, Get4, Get5 raise "global nodes are not local nodes" in a
  debug build when `islocal` is false, and use the number unchanged in
  release
  (`classes:src/submodules/STScalarField/src/include/localNodeError.F90`).
  Pass `islocal=math%yes`.
- `SetByFunction` writes `VALUE` at mesh node `ii` as space DOF `ii`.
  Only Lagrange is checked (debug); for Lagrange order > 1 the DOFs that
  are not mesh nodes are not set (interface docblock).
- Set14 has no optional arguments: give both `scale` and
  `addContribution`, or use Set13 / `v = u`. Set13 and Set14 copy
  values only; both fields must be initiated and have the same
  `Size()` (debug check).
- Constant fields: Set1..Set6, Set8..Set11 and `SetFromScalarField`
  raise "Not callable for constant ..." in debug builds only. Set12,
  Set13, Set14, `SetToScalarField` and the index methods do not check.
- Sizes are checked in debug builds only: Set1 and Set2 (`SIZE(VALUE) =
  timeCompo`), Set4 and Set8 (exact shape), Set5 (`tNodes`), Set9
  (`SIZE(globalNode)`), Get1/Get2/Get3 (enough room).
- `timeCompo` must be in `[1, obj%timeCompo]`; Set3, Set5, Set6, Set9,
  Set10 and `SetFromScalarField` check it in debug builds only.
  `SetToScalarField` does not check it.
- Get2, Get3 and Get4 read `realVec` directly only when the engine
  name is exactly `"NATIVE_SERIAL"`; otherwise they use `GetMultiple`.
