# STVectorField: Setting values

**Purpose.** Set the values of a space-time vector field
`STVectorField_` (and of `STVectorFieldLis_`, same API on a LIS
vector): by node, space component and time component (`Set`,
Set1..Set14), from rank 2 and rank 3 arrays and `FEVariable_`, from
another space-time field (Set14), from a `VectorField_`
(`SetFromVectorField`), from a user function (`SetByFunction`), and by
index of the value vector (`SetSingle`, `SetAll`, `SetMultiple`).

**Classes.** `STVectorField_` (`STVectorField_Class`), which extends
`AbstractNodeField_`; `STVectorFieldLis_` (`STVectorFieldLis_Class`),
which extends `STVectorField_`. Interfaces:
`classes:src/modules/STVectorField/src/STVectorField_Class.F90`,
`classes:src/modules/STVectorFieldLis/src/STVectorFieldLis_Class.F90`.
Implementation:
`classes:src/submodules/STVectorField/src/STVectorField_Class@SetMethods.F90`.
Data layout and reading values:
[STVectorField: Getting values](stvectorfield-get.md).

## Steps

1. **Initiate.** `dom%ImportFromToml(filename=, tomlName="domain")`,
   then `u%ImportFromToml(tomlName="u", filename=, fedof=, geofedof=,
   timefedof=, dom=)`. More fields on the same FEDOFs:
   `v%Initiate(NAME=, engine="NATIVE_SERIAL", spaceCompo=, fedof=,
   geofedof=, timefedof=)` (or `timeCompo=` without `timefedof`).
2. **Set** (generic `Set`). Every form except Set14 takes optional
   `scale` (default 1) and `addContribution` (default false): the
   entries become `scale * VALUE`, or `scale * VALUE` is added.
   - Set11 `Set(VALUE)`, scalar: all entries (`SetAll`).
   - Set2 `Set(VALUE(:, :))`: every node gets `VALUE(s, t)`, shape
     `(spaceCompo, timeCompo)`.
   - Set3 `Set(VALUE, spaceCompo, timeCompo)`: one component of all
     nodes, one value.
   - Set5 `Set(VALUE(:), spaceCompo, timeCompo)`: one component of all
     nodes, `SIZE(VALUE) = tNodes`.
   - Set12 `Set(VALUE(:, :), spaceCompo(:), timeCompo, storageFMT)`:
     several space components at one time component. `NODES_FMT`:
     `VALUE(j, i)`, shape `(SIZE(spaceCompo), tNodes)`; `DOF_FMT`: the
     transpose.
   - Set13 `Set(VALUE(:, :), spaceCompo, timeCompo(:), storageFMT)`:
     several time components of one space component, same layout.
   - Set4 `Set(VALUE(:, :, :))`: all values, `VALUE(s, t, i)`, shape
     `(spaceCompo, timeCompo, tNodes)`. No `storageFMT`.
   - Set1 `Set(globalNode, islocal, VALUE(:, :))`: one node,
     `VALUE(s, t)`.
   - Set9 `Set(VALUE, globalNode, islocal, spaceCompo, timeCompo)`: one
     entry (`SetSingle`).
   - Set6 `Set(VALUE(:, :), globalNode(:), islocal)`: the same matrix at
     the selected nodes.
   - Set7 `Set(globalNode(:), islocal, VALUE(:, :, :))`: selected nodes,
     `VALUE(s, t, j)` for `globalNode(j)`.
   - Set8 `Set(VALUE(:), globalNode(:), islocal, spaceCompo, timeCompo)`:
     one component of the selected nodes.
   - Set10 `Set(VALUE=fevar, globalNode(:), islocal)`: nodal, vector,
     space-time `FEVariable_` `(spaceCompo, nodes, timeCompo)`, the
     layout that Get7 returns.
   - Set14 `Set(VALUE=field)`: copy all values of another
     `STVectorField_` or child, any engine. No `scale`, no
     `addContribution`.
3. **From a vector field.** `u%SetFromVectorField(VALUE=v, timeCompo,
   [scale, addContribution])` sets time component `timeCompo` from the
   `VectorField_` `v` (`v%spaceCompo = u%spaceCompo`, same FEDOF). `v`
   may be a `VectorFieldLis_` (`SetFromVectorField_test_2`; setting `v`:
   [VectorField: Setting values](vectorfield-set.md)).
4. **From a user function.** `u%SetByFunction(func, [times])`: `func` is
   a vector `UserFunction_` of `(x, y, z, t)`. Each space component is
   interpolated element by element in the space of `fedof` (all DOFs,
   any order). With `times` (`SIZE = timeCompo`) time component `a` gets
   `func(., times(a))`; without, `func(., 0)` at every time component.
   The time basis must be Lagrange (checked in debug builds).
5. **By index** (`AbstractNodeField_`, overridden by
   `STVectorFieldLis_`): `SetSingle`, `SetAll`, `SetMultiple1..5`; see
   [ScalarField: Setting and Getting values](scalarfield-set-get.md).
   The index of `(node i, s, t)` is `((t - 1) * spaceCompo + s - 1) *
   tNodes + i`.

Trimmed from `Set_test_1` to `Set_test_4` and `SetFromVectorField_test_1`
of `STVectorField` (all use `STVectorField_test.toml`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: DOF_FMT
USE GlobalData, ONLY: I4B
USE GlobalData, ONLY: NODES_FMT
USE STVectorField_Class, ONLY: STVectorField_
USE Test_Method, ONLY: OK
USE TimeFEDOF_Class, ONLY: TimeFEDOF_
USE VectorField_Class, ONLY: VectorField_

CHARACTER(*), PARAMETER :: tomlFileName = "STVectorField_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STVectorField_) :: u, n
TYPE(VectorField_) :: v
REAL(DFP) :: found(24), mat(2, 2), a(6), b(6), m(2, 6), w3(2, 2, 3)
INTEGER(I4B) :: tsize, ii

CALL e%SetQuietMode(math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
CALL v%Initiate(NAME="v", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
a = [(REAL(ii, DFP), ii=1, 6)]
b = 10.0_DFP * a

! all entries (Set11), the same matrix at every node (Set2)
CALL u%Set(VALUE=1.0_DFP)
mat = RESHAPE([1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP], [2, 2])
CALL u%Set(VALUE=mat)
CALL u%GetMultiple(istart=1, iend=24, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found(7:12) - 2.0_DFP) .LT. tol), &
        "Set matrix at all nodes: DOF format")

! one node (Set1), then add 2 * 1; one entry (Set9)
mat = RESHAPE([5.0_DFP, 6.0_DFP, 7.0_DFP, 8.0_DFP], [2, 2])
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=mat)
mat = 1.0_DFP
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=mat, &
           scale=2.0_DFP, addContribution=math%yes)
CALL u%Set(VALUE=9.0_DFP, globalNode=3, islocal=math%yes, &
           spaceCompo=2, timeCompo=1)

! one component of all nodes (Set3, Set5)
CALL u%Set(VALUE=4.0_DFP, spaceCompo=2, timeCompo=1)
CALL u%Set(VALUE=a, spaceCompo=1, timeCompo=2)

! several space components (Set12), several time components (Set13)
m(1, :) = a
m(2, :) = b
CALL u%Set(VALUE=m, spaceCompo=[1, 2], timeCompo=2, &
           storageFMT=NODES_FMT)
CALL u%Set(VALUE=TRANSPOSE(m), spaceCompo=1, timeCompo=[2, 1], &
           storageFMT=DOF_FMT)

! selected nodes: same matrix (Set6), rank 3 (Set7), one component (Set8)
mat = RESHAPE([1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP], [2, 2])
CALL u%Set(VALUE=mat, globalNode=[2, 5], islocal=math%yes)
w3 = 2.0_DFP
CALL u%Set(globalNode=[6, 4, 1], islocal=math%yes, VALUE=w3)
CALL u%Set(VALUE=[7.0_DFP, 8.0_DFP], globalNode=[3, 5], &
           islocal=math%yes, spaceCompo=2, timeCompo=2)

! time component 2 from a vector field, then add 2 * v
CALL v%Set(VALUE=a, spaceCompo=1)
CALL v%Set(VALUE=b, spaceCompo=2)
CALL u%SetFromVectorField(VALUE=v, timeCompo=2)
CALL u%SetFromVectorField(VALUE=v, timeCompo=2, scale=2.0_DFP, &
                          addContribution=math%yes)
CALL u%Get(VALUE=found, tsize=tsize, spaceCompo=2, timeCompo=2)
CALL OK(ALL(ABS(found(1:6) - 3.0_DFP * b) .LT. tol), &
        "SetFromVectorField: add 2 * value")

! copy another field (Set14)
CALL n%Initiate(obj2=u)
CALL n%Set(VALUE=0.0_DFP)
CALL n%Set(VALUE=u)

CALL n%DEALLOCATE()
CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
```

Between engines (trimmed from `Set_test_2` of `STVectorFieldLis`;
`STVectorFieldLis_test.toml` is `STVectorField_test.toml` with
`engine = "LIS_OMP"`):

```fortran
! other USE items, dom, fedof, geofedof, timefedof, tol: as above
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE STVectorField_Class, ONLY: STVectorField_
USE STVectorFieldLis_Class, ONLY: STVectorFieldLis_

TYPE(LisOmpEngine_) :: lis
TYPE(STVectorFieldLis_) :: u
TYPE(STVectorField_) :: n
REAL(DFP) :: found(24), want(24)
INTEGER(I4B) :: ii, tsize

CALL lis%Initiate()
! ... dom%ImportFromToml, u%ImportFromToml with STVectorFieldLis_test.toml
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof, timefedof=timefedof)
want = [(REAL(ii, DFP), ii=1, 24)]

CALL n%SetMultiple(istart=1, iend=24, stride=1, VALUE=want)
CALL u%Set(VALUE=n)                                ! LIS <- native
CALL u%GetMultiple(istart=1, iend=24, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - want) .LT. tol), "Set14: LIS <- native")
CALL u%SetMultiple(istart=1, iend=24, stride=1, VALUE=-want)
CALL n%Set(VALUE=u)                                ! native <- LIS
CALL n%GetMultiple(istart=1, iend=24, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found + want) .LT. tol), "Set14: native <- LIS")

CALL n%DEALLOCATE()
CALL u%DEALLOCATE()
! ... timefedof, fedof, geofedof, dom
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STVectorField/examples/Set_test_1.F90` (Set11,
  Set2, Set1, Set9)
- `classes:src/modules/STVectorField/examples/Set_test_2.F90` (Set3,
  Set5, Set12, Set13)
- `classes:src/modules/STVectorField/examples/Set_test_3.F90` (Set4,
  Set6, Set7, Set8)
- `classes:src/modules/STVectorField/examples/Set_test_4.F90` (Set10,
  Set14)
- `classes:src/modules/STVectorField/examples/SetFromVectorField_test_1.F90`
- `classes:src/modules/STVectorField/examples/SetFromVectorField_test_2.F90`
  (from a `VectorFieldLis_`)
- `classes:src/modules/STVectorField/examples/SetByFunction_test_1.F90`
  (order 1), `SetByFunction_test_2.F90` (order 2 in space)
- `classes:src/modules/STVectorField/examples/STVectorField_test.toml`
- `classes:src/modules/STVectorFieldLis/examples/Set_test_1.F90`
  (inherited Set forms on a LIS field)
- `classes:src/modules/STVectorFieldLis/examples/Set_test_2.F90` (Set14
  between engines, `SetFromVectorField`, `SetToVectorField`)
- `classes:src/modules/STVectorFieldLis/examples/SetMultiple_test_1.F90`
  (index methods on LIS, `SetMultiple5` from native and LIS)

## Pitfalls

- Pass `islocal=math%yes` and local node numbers. No Set uses `islocal`:
  the `localNodeError.F90` include of `STVectorField` is empty, so
  unlike `STScalarField_` a debug build does not catch `islocal=.FALSE.`.
- Without `addContribution` the entries become `scale * VALUE`, not
  `VALUE`.
- Set14 is the way to move values between engines: same engine calls
  `COPY`, otherwise `VALUE%GetMultiple` into a temporary and
  `obj%SetMultiple`. Sizes must agree (checked in debug builds only).
  `COPY` itself needs the same engine.
- No `ASSIGNMENT(=)` for `STVectorField_`: write `v%Set(VALUE=u)`.
- `n%Initiate(obj2=lisField)` with a native `n` copies the engine name
  (`"LIS_OMP"`) and `realVec`, which is not up to date for a LIS field
  (`AbstractNodeField_` `obj_Initiate1`; unverified, no test). Initiate
  `n` by arguments and copy with Set14 instead.
- Sizes are checked in debug builds only (Set1, Set2, Set4, Set6, Set7,
  Set8, Set12, Set13). Set3, Set5 and Set10 check neither sizes nor
  component bounds (native `SetMultiple2`, which Set5 calls, does not
  check `SIZE(VALUE)` either); Set8, Set9, Set12 and Set13 check
  `<= spaceCompo` / `<= timeCompo` but not `>= 1`.
- Set10 accepts only a space-time `FEVariable_`; another `vartype` does
  nothing in release (error in debug builds).
- Set1 and Set12/Set13 (`NODES_FMT`) build the index list in a fixed
  buffer of 128 entries (`TEMP_INTVEC_LEN`), not checked. Set8 switches
  to a growing buffer above 128 nodes.
- `SetByFunction`: `ivar`, `idof`, `spaceCompo` and `timeCompo` are not
  used; times must be distinct (debug check).
- LIS: `STVectorFieldLis_` overrides only the index methods, `Size`,
  `GetPointer`, BLAS, constructors and IO; every `Set` form,
  `SetFromVectorField`, `SetToVectorField` and `SetByFunction` is
  inherited and reaches the LIS vector through `SetSingle`, `SetAll` and
  `SetMultiple`. Its `Initiate` always stores engine `"LIS_OMP"`,
  whatever `engine` is passed. Call `lis%Initiate()` before the first
  LIS field and `lis%DEALLOCATE()` after the last one.
