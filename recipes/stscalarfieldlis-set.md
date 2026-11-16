# STScalarFieldLis: Setting values

**Purpose.** Set the values of a space-time scalar field stored in a
LIS vector (`STScalarFieldLis_`): by index of the value vector
(`SetSingle`, `SetAll`, `SetMultiple`), by node and time component
(`Set`), from another field of any engine (`Set(VALUE=field)`, `=`,
`SetFromScalarField`) and from a user function (`SetByFunction`).

**Classes.** `STScalarFieldLis_` (`STScalarFieldLis_Class`), which
extends `STScalarField_` (`STScalarField_Class`), which extends
`AbstractNodeField_`. `LisOmpEngine_` (`LisOmpEngine_Class`) starts and
stops LIS. Interfaces:
`classes:src/modules/STScalarFieldLis/src/STScalarFieldLis_Class.F90`
(index methods),
`classes:src/modules/STScalarField/src/STScalarField_Class.F90` (`Set`).
Implementations: `@SetMethods.F90` in
`classes:src/submodules/STScalarFieldLis/src/` and
`classes:src/submodules/STScalarField/src/`.
Start-up, layout and reading back:
[STScalarFieldLis: Getting values](stscalarfieldlis-get.md).

## Steps

1. **Start LIS and initiate** as in the Get recipe: `lis%Initiate()`,
   then `ImportFromToml` or `Initiate`; the engine is always
   `"LIS_OMP"`. Index of space DOF `i`, time component `a`:
   `(a - 1) * tNodes + i`.
2. **By index** (overridden, they write the LIS vector). Each takes
   optional `scale` (default 1) and `addContribution` (default false):
   the entries become `scale * VALUE`, or `scale * VALUE` is added
   (`LIS_INS_VALUE` or `LIS_ADD_VALUE`).
   - `SetSingle(indx, VALUE)`; `SetAll(VALUE)`.
   - `SetMultiple(indx(:), VALUE(:))` (SetMultiple1).
   - `SetMultiple(istart, iend, stride, VALUE(:))` (SetMultiple2).
   - `SetMultiple(istart, iend, stride, VALUE(:), istart_value,
     iend_value, stride_value)`: from a range of an array (SetMultiple3).
   - `SetMultiple(istart, iend, stride, VALUE)`, scalar (SetMultiple4).
   - `SetMultiple(istart, iend, stride, VALUE=field, istart_value,
     iend_value, stride_value)` (SetMultiple5): a native `VALUE` passes
     its vector (`GetPointer`) to SetMultiple3; a LIS `VALUE` is read by
     `lis_vector_set_values9` (no copy); another engine goes through a
     temporary array.
3. **By node and time component** (`Set` of `STScalarField_`, Set1 to
   Set12). They are not overridden; each calls the index methods of
   step 2, so it writes the LIS vector. Forms and arguments: see
   [STScalarField: Setting and Getting values](stscalarfield-set-get.md),
   step 3. Short list: Set12 `Set(VALUE)` all entries; Set2
   `Set(VALUE(1:timeCompo))`; Set3/Set5 one time component; Set1, Set7,
   Set10 by node; Set9 selected nodes of one time component; Set4,
   Set8 rank-2 arrays; Set11 `FEVariable_`; Set6 one time component
   from a time component of another `STScalarField_` (SetMultiple5).
4. **From another space-time field, any engine.**
   - Set13 `v%Set(VALUE=u)` and `v = u` (`ASSIGNMENT(=)`): copy all
     values.
   - Set14 `v%Set(VALUE=u, scale=, addContribution=)`:
     `v = [v +] scale * u`. Both arguments are required.
   Set13 calls Set14. Set14 reads a native `VALUE` through
   `GetPointer`, any other `VALUE` (LIS) through `GetMultiple` into a
   temporary array, then writes `obj` with `SetMultiple`. So native to
   LIS, LIS to LIS and LIS to native all work
   (`classes:src/modules/STScalarFieldLis/examples/Set_test_1.F90`).
   This is the way to move values between engines.
5. **From or to a scalar field.** `u%SetFromScalarField(timeCompo=,
   VALUE=s)` and `u%SetToScalarField(timeCompo=, VALUE=s)` use
   SetMultiple5, so `s` may be a `ScalarFieldLis_` (`SetMultiple_test_1`
   Test 9).
6. **Copy-initiate.** `c%Initiate(obj2=x, copyFull=math%yes)`, `x`
   native or LIS: `c` gets its own LIS vector with the values of `x`
   and engine `"LIS_OMP"`
   (`classes:src/modules/STScalarFieldLis/examples/Initiate_test_1.F90`).
7. **User function.** `SetByFunction(func, [times])` evaluates `func`
   at the mesh nodes and calls Set1 for each node (unverified for LIS:
   no LIS test).

Trimmed from `SetMultiple_test_1` and `Set_test_1` of `STScalarFieldLis`
(both use `STScalarFieldLis_test.toml`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE ScalarFieldLis_Class, ONLY: ScalarFieldLis_
USE STScalarField_Class, ONLY: STScalarField_
USE STScalarFieldLis_Class, ONLY: STScalarFieldLis_
USE Test_Method, ONLY: OK
USE TimeFEDOF_Class, ONLY: TimeFEDOF_

CHARACTER(*), PARAMETER :: tomlFileName = "STScalarFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STScalarFieldLis_) :: u, v
TYPE(STScalarField_) :: n
TYPE(ScalarFieldLis_) :: s
REAL(DFP) :: found(12), want(12), areal, s6(6)
INTEGER(I4B) :: ii, tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
CALL v%Initiate(NAME="v", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
CALL s%Initiate(NAME="s", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
want = [(REAL(ii, DFP), ii=1, 12)]

! index 8 = node 2, time 2: 3, then + 2 * 1
CALL u%SetAll(VALUE=0.0_DFP)
CALL u%SetSingle(indx=8, VALUE=3.0_DFP)
CALL u%SetSingle(indx=8, VALUE=1.0_DFP, scale=2.0_DFP, &
                 addContribution=math%yes)
CALL u%GetSingle(indx=8, VALUE=areal)
CALL OK(ABS(areal - 5.0_DFP) .LT. tol, "SetSingle, GetSingle")

! one value in the range of time component 2
CALL u%SetMultiple(istart=7, iend=12, stride=1, VALUE=-1.0_DFP)
! time component a of all nodes to VALUE(a) (Set2)
CALL u%Set(VALUE=[4.0_DFP, 5.0_DFP])

! v(1:6) = 2 * n(7:12), n native (SetMultiple5)
CALL n%SetMultiple(istart=1, iend=12, stride=1, VALUE=want)
CALL v%SetMultiple(istart=1, iend=6, stride=1, VALUE=n, istart_value=7, &
                   iend_value=12, stride_value=1, scale=2.0_DFP)

! all values between engines (Set13, Set14, assignment)
CALL v%Set(VALUE=n)                                   ! LIS <- native
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=2.0_DFP * want)
CALL v%Set(VALUE=u)                                   ! LIS <- LIS
n = u                                                 ! native <- LIS
CALL v%SetAll(VALUE=1.0_DFP)
CALL v%Set(VALUE=n, scale=0.5_DFP, addContribution=math%yes)
CALL v%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - (1.0_DFP + want)) .LT. tol), &
        "Set14: LIS + 0.5 * native")

! time component 2 from a LIS scalar field, time 1 back into it
s6 = [10.0_DFP, 20.0_DFP, 30.0_DFP, 40.0_DFP, 50.0_DFP, 60.0_DFP]
CALL s%SetMultiple(istart=1, iend=6, stride=1, VALUE=s6)
CALL u%SetFromScalarField(timeCompo=2, VALUE=s)
CALL u%SetToScalarField(timeCompo=1, VALUE=s)

CALL s%DEALLOCATE()
CALL n%DEALLOCATE()
CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STScalarFieldLis/examples/SetMultiple_test_1.F90`
  (index methods, Set2, SetMultiple5 from native and LIS,
  `SetFromScalarField`, `SetToScalarField`)
- `classes:src/modules/STScalarFieldLis/examples/Set_test_1.F90` (Set13
  and Set14 between engines, `n = u`)
- `classes:src/modules/STScalarFieldLis/examples/Initiate_test_1.F90`
  (copy-initiate from native and LIS)
- `classes:src/modules/STScalarField/examples/Set_test_1.F90` to
  `Set_test_5.F90` (node forms, native engine)
- `classes:src/modules/STScalarFieldLis/examples/STScalarFieldLis_test.toml`

## Pitfalls

- Pass `islocal=math%yes`. `globalNode` must hold local node numbers:
  Set1, Set9, Set10, Set11 raise "global nodes are not local nodes" in
  a debug build when `islocal` is false and use the number unchanged
  in release
  (`classes:src/submodules/STScalarField/src/include/localNodeError.F90`).
- Use `Set(VALUE=field)` (or `=`), not `COPY`, between a native and a
  LIS field. `COPY` and the other BLAS methods need the same engine
  ([STScalarFieldLis: BLAS methods](stscalarfieldlis-blas.md)).
- Set14 has no optional arguments: give both `scale` and
  `addContribution`, or use Set13.
- Set13 and Set14 need two initiated fields of the same `Size()`
  (checked in debug builds only); no structure is copied. Use
  `Initiate(obj2=, copyFull=math%yes)` to create a copy.
- `SetAll` with `addContribution` calls `lis_vector_set_value` once per
  entry; without it, one `lis_vector_set_all`.
- SetMultiple5 with a LIS `VALUE`: `obj` and `VALUE` may be the same
  field only if the two ranges do not overlap (interface docblock).
  The number of values is set by the range of `obj`.
- Constant-field checks ("Not callable for constant ...") and size
  checks run in debug builds only.
- Only Set2, Set13, Set14, SetMultiple5, `SetFromScalarField` and
  `SetToScalarField` of the inherited methods are covered by a LIS test.
  The other `Set` forms, `SetByFunction` and `v = u` with a LIS left
  side are unverified for LIS (they call the same index methods).
