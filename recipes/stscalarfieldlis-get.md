# STScalarFieldLis: Getting values

**Purpose.** Read the values of a space-time scalar field stored in a
LIS vector (`STScalarFieldLis_`): by index of the value vector
(`GetSingle`, `GetMultiple`), by node and time component (`Get`,
`GetFEVariable`) and into a scalar field (`SetToScalarField`).

**Classes.** `STScalarFieldLis_` (`STScalarFieldLis_Class`), which
extends `STScalarField_` (`STScalarField_Class`), which extends
`AbstractNodeField_`. `LisOmpEngine_` (`LisOmpEngine_Class`) starts and
stops LIS. Interfaces:
`classes:src/modules/STScalarFieldLis/src/STScalarFieldLis_Class.F90`
(index methods),
`classes:src/modules/STScalarField/src/STScalarField_Class.F90` (`Get`).
Implementations: `@GetMethods.F90` in
`classes:src/submodules/STScalarFieldLis/src/` and
`classes:src/submodules/STScalarField/src/`.
Setting values: [STScalarFieldLis: Setting values](stscalarfieldlis-set.md);
BLAS: [STScalarFieldLis: BLAS methods](stscalarfieldlis-blas.md); native
field: [STScalarField: Setting and Getting values](stscalarfield-set-get.md).

## Steps

1. **Start LIS and initiate.** `lis%Initiate()` first, then
   `dom%ImportFromToml(filename=, tomlName="domain")` and
   `u%ImportFromToml(tomlName=, filename=, fedof=, geofedof=,
   timefedof=, dom=)` with `engine = "LIS_OMP"` in the table, or
   `u%Initiate(NAME=, engine=, fedof=, geofedof=, timefedof=)`.
   `Initiate` always sets the engine to `"LIS_OMP"` and creates the LIS
   vector (`CALL OK(u%GetEngineName() .EQ. "LIS_OMP", ...)` after
   `engine="NATIVE_SERIAL"` in
   `classes:src/modules/STScalarFieldLis/examples/Get_test_1.F90`).
   Call `lis%DEALLOCATE()` after the last LIS field is deallocated.
2. **Layout.** The value of space DOF `i` at time component `a` has the
   index `(a - 1) * tNodes + i`, `tNodes = fedof%GetTotalDOF()`.
   `Size()` returns `local_n`; it is 12 for `STScalarFieldLis_test.toml`
   (six nodes, order 1 in space and time, `timeCompo = 2`)
   (`classes:src/modules/STScalarFieldLis/examples/Initiate_test_1.F90`).
3. **By index** (overridden, they read the LIS vector):
   - `GetSingle(indx, VALUE)`: `lis_vector_get_value`.
   - `GetMultiple(indx(:), VALUE, tsize)`: `tsize = SIZE(indx)`.
   - `GetMultiple(istart, iend, stride, VALUE, tsize)`: into
     `VALUE(1:tsize)`, `tsize = (iend - istart) / stride + 1`.
   - `GetMultiple(istart, iend, stride, VALUE, istart_value,
     iend_value, stride_value, tsize)`: into a range of `VALUE`.
   - `GetMultiple(istart, iend, stride, VALUE, istart_value,
     iend_value, stride_value, [scale, addContribution])`, no `tsize`:
     `VALUE(range_v) = [VALUE(range_v) +] scale * obj(range)`.
4. **By node and time component** (`Get` of `STScalarField_`; each form
   calls the index methods above, so it reads the LIS vector):
   - Get1 `Get(VALUE(:), tsize, globalNode, [islocal])`: all time
     components of one node, `tsize = timeCompo`.
   - Get1 `Get(VALUE(:), tsize, timeCompo)`: all space DOFs of one time
     component, `tsize = tNodes`. Give exactly one of `globalNode` and
     `timeCompo` (checked in debug builds).
   - Get4 `Get(VALUE(:), globalNode(:), tsize, islocal, timeCompo)`:
     one time component of the selected nodes.
   - Get5 `Get(VALUE, globalNode, islocal, timeCompo)`: one value
     (`GetSingle`).
   - Get2 `Get(VALUE(:, :), nrow, ncol, storageFMT)`: all values. NODES
     format gives `VALUE(a, i)` (`nrow = timeCompo`), DOF format
     `VALUE(i, a)` (`nrow = tNodes`).
   - Get3 `Get(VALUE(:, :), nrow, ncol, globalNode(:), islocal,
     storageFMT)`: the same for the selected nodes.
   - Get6 `Get(VALUE=fevar, globalNode(:), islocal)` and
     `GetFEVariable(globalNode, islocal, VALUE)`: nodal space-time
     `FEVariable_` with `val(j, a)`.
5. **Into a scalar field.** `u%SetToScalarField(timeCompo=, VALUE=s,
   [scale, addContribution])` writes one time component into `s`; `s`
   may be a `ScalarFieldLis_`
   (`classes:src/modules/STScalarFieldLis/examples/SetMultiple_test_1.F90`
   Test 9).

Trimmed from `Get_test_1` and `SetMultiple_test_1` of `STScalarFieldLis`
(both use `STScalarFieldLis_test.toml`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE FieldOpt_Class, ONLY: TypeFieldOpt
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE STScalarFieldLis_Class, ONLY: STScalarFieldLis_
USE Test_Method, ONLY: OK
USE TimeFEDOF_Class, ONLY: TimeFEDOF_

CHARACTER(*), PARAMETER :: tomlFileName = "STScalarFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STScalarFieldLis_) :: w, u
REAL(DFP) :: src(12), found(12), v2(6, 6), areal
INTEGER(I4B) :: ii, nrow, ncol, tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL w%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
! the engine becomes LIS_OMP, whatever engine is given
CALL u%Initiate(NAME="u", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
src = [(REAL(ii, DFP), ii=1, 12)]
CALL u%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)

! by index
CALL u%GetSingle(indx=8, VALUE=areal)                     ! node 2, time 2
CALL u%GetMultiple(indx=[2, 7, 12], VALUE=found, tsize=tsize)
CALL u%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, tsize=tsize)
CALL OK(tsize .EQ. 12, "GetMultiple: tsize")

! all values (Get2), NODES format: v2(a, i)
CALL u%Get(VALUE=v2, nrow=nrow, ncol=ncol, &
           storageFMT=TypeFieldOpt%storageFormatNodes)
CALL OK(nrow .EQ. 2 .AND. ncol .EQ. 6, "Get2, NODES: shape")

! selected nodes (Get3), DOF format: v2(j, a)
CALL u%Get(VALUE=v2, nrow=nrow, ncol=ncol, globalNode=[2, 5], &
           islocal=math%yes, storageFMT=TypeFieldOpt%storageFormatDOF)
CALL OK(ALL(ABS(v2(1:2, 1) - [2.0_DFP, 5.0_DFP]) .LT. tol) .AND. &
        ALL(ABS(v2(1:2, 2) - [8.0_DFP, 11.0_DFP]) .LT. tol), &
        "Get3, DOF")

! all time components of node 4 (Get1)
CALL u%Get(VALUE=found, tsize=tsize, globalNode=4, islocal=math%yes)
CALL OK(tsize .EQ. 2 .AND. &
        ALL(ABS(found(1:2) - [4.0_DFP, 10.0_DFP]) .LT. tol), "Get1")

CALL u%DEALLOCATE()
CALL w%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STScalarFieldLis/examples/Get_test_1.F90` (Get1,
  Get2, Get3; engine forced to `LIS_OMP`)
- `classes:src/modules/STScalarFieldLis/examples/SetMultiple_test_1.F90`
  (`GetSingle`, `GetMultiple` by indices and range,
  `SetToScalarField`)
- `classes:src/modules/STScalarFieldLis/examples/Initiate_test_1.F90`
  (`Size`)
- `classes:src/modules/STScalarFieldLis/examples/STScalarFieldLis_test.toml`

## Pitfalls

- Pass `islocal=math%yes`. `globalNode` must hold local node numbers;
  a debug build raises an error when `islocal` is false (Get3, Get4,
  Get5 through `include/localNodeError.F90`; Get1 when `islocal` is
  given and false). Release builds use the number unchanged.
- `GetPointer` returns `NULL()` (error in debug builds); the values are
  not in `realVec`. `Display` and `Export` gather the LIS vector into
  `realVec` first; do not read `realVec` otherwise.
- Get2, Get3 and Get4 read `realVec` directly only when the engine name
  is exactly `"NATIVE_SERIAL"`; a LIS field takes the `GetMultiple`
  branch (Get2 and Get3 in an OpenMP parallel loop).
- `VALUE` is not reallocated. Its size is checked in debug builds only
  (Get1, Get2, Get3).
- The `GetMultiple` form with `tsize` and a range of `VALUE` is
  `INTENT(OUT)`; the form with `scale`/`addContribution` is
  `INTENT(INOUT)` and keeps the entries outside the range.
- Not covered by a LIS test (unverified for LIS): Get4, Get5, Get6,
  `GetFEVariable`, Get1 with `timeCompo`, and both range-of-`VALUE`
  forms of `GetMultiple`.
- Without `USE_LIS` the class comes from `NO_STScalarFieldLis_Class.F90`,
  an empty extension of `STScalarField_` (native storage).
