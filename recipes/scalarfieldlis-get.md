# ScalarFieldLis: Getting values

**Purpose.** Read the values of a scalar field stored in a LIS vector
(`ScalarFieldLis_`): by node (`Get`, `GetFEVariable`) and by index of
the value vector (`GetSingle`, `GetMultiple`). `GetPointer` is not
available; values go to another engine with `Set`.

**Classes.** `ScalarFieldLis_` (`ScalarFieldLis_Class`), which extends
`ScalarField_` (`ScalarField_Class`), which extends
`AbstractNodeField_`. `LisOmpEngine_` (`LisOmpEngine_Class`) starts and
stops LIS. Interfaces:
`classes:src/modules/ScalarFieldLis/src/ScalarFieldLis_Class.F90`
(index methods),
`classes:src/modules/ScalarField/src/ScalarField_Class.F90` (`Get`).
Implementations: `ScalarFieldLis_Class@GetMethods.F90` in
`classes:src/submodules/ScalarFieldLis/src/` and
`ScalarField_Class@GetMethods.F90` in
`classes:src/submodules/ScalarField/src/`. Setting values:
[ScalarFieldLis: Setting values](scalarfieldlis-set.md); BLAS:
[ScalarFieldLis: BLAS methods](scalarfieldlis-blas.md); native field:
[ScalarField: Setting and Getting values](scalarfield-set-get.md).

## Steps

1. **Start LIS and initiate.** `lis%Initiate()` first, then
   `dom%ImportFromToml(filename=, tomlName="domain")` and
   `u%ImportFromToml(fedof=, geofedof=, dom=, filename=, tomlName=)`
   with `engine = "LIS_OMP"` in the table, or `u%Initiate(NAME=,
   engine="LIS_OMP", fedof=, geofedof=)`. `Initiate` always sets the
   engine to `"LIS_OMP"` (docblock of `obj_Initiate2`; `CALL
   OK(w%GetEngineName() .EQ. "LIS_OMP", ...)` after importing a native
   field in `classes:src/modules/ScalarFieldLis/examples/Import_test_1.F90`).
   Call `lis%DEALLOCATE()` after the last LIS field is deallocated.
2. **Layout.** One value per DOF of `fedof`; node, DOF and index are
   the same number. `Size()` returns `local_n`; it is 6 for
   `ScalarFieldLis_test.toml` (`square_3x2.h5`, order 1)
   (`CALL OK(u%SIZE() .EQ. 6, ...)` in
   `classes:src/modules/ScalarFieldLis/examples/Initiate_test_1.F90`).
3. **By node** (`Get` generic of `ScalarField_`, `NON_OVERRIDABLE`; it
   calls the index methods below, so it reads the LIS vector):
   - `Get(VALUE, globalNode, islocal)`: one value (Get1, `GetSingle`).
   - `Get(VALUE(:), tsize)`: all values (Get2, `GetMultiple` on the
     range of the DOF object).
   - `Get(VALUE(:), globalNode(:), islocal, tsize)`: selected nodes
     (Get3, `GetMultiple` with `indx`).
   - `Get(VALUE=fevar, globalNode(:), islocal)` (Get4) and
     `GetFEVariable(globalNode, islocal, VALUE)`: a nodal, space,
     scalar `FEVariable_`; `fevar` must be initiated with room for
     `SIZE(globalNode)` values
     (`classes:src/modules/ScalarFieldLis/examples/Get_test_1.F90`;
     native: `classes:src/modules/ScalarField/examples/Set_test_3.F90`).
4. **By index** (overridden by `ScalarFieldLis_`; `tsize = (iend -
   istart) / stride + 1` for the ranges):
   - `GetSingle(indx, VALUE)`: `lis_vector_get_value`.
   - `GetMultiple(indx(:), VALUE, tsize)`: `VALUE(1:tsize) =
     obj(indx)`, `tsize = SIZE(indx)` (`lis_vector_get_values_from_index`).
   - `GetMultiple(istart, iend, stride, VALUE, tsize)`: `VALUE(1:tsize)
     = obj(istart:iend:stride)` (`lis_vector_get_values_from_range`).
   - `GetMultiple(istart, iend, stride, VALUE, istart_value,
     iend_value, stride_value, tsize)`: into a range of `VALUE`
     (`lis_vector_get_values_from_range2`).
   - `GetMultiple(istart, iend, stride, VALUE, istart_value,
     iend_value, stride_value, [scale, addContribution])` (no `tsize`):
     `VALUE(range) = [VALUE(range) +] scale * obj(range)`, `scale`
     defaults to 1 (GetMultiple4).
5. **Into a native field**: `n%Set(VALUE=u)` or `n = u`; the native
   `Set8` reads `u` with `GetMultiple` into a temporary array
   (`classes:src/modules/ScalarFieldLis/examples/Set_test_4.F90`).

Trimmed from `Set_test_1`, `Set_test_2`, `SetMultiple_test_1` and
`SetMultiple_test_2` of `ScalarFieldLis`:

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE ScalarFieldLis_Class, ONLY: ScalarFieldLis_
USE Test_Method, ONLY: OK

CHARACTER(*), PARAMETER :: tomlFileName = "ScalarFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(ScalarFieldLis_) :: u
REAL(DFP) :: val, found(6), want(6)
INTEGER(I4B) :: tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
want = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL u%Set(VALUE=want)

! by node
CALL u%Get(VALUE=val, globalNode=2, islocal=math%yes)
CALL OK(ABS(val - 2.0_DFP) .LT. tol, "Get single")
CALL u%Get(VALUE=found, tsize=tsize)
CALL OK(tsize .EQ. 6, "Get all: tsize")
CALL u%Get(VALUE=found, globalNode=[2, 4], islocal=math%yes, &
           tsize=tsize)
CALL OK(tsize .EQ. 2, "Get selected: tsize")

! by index
CALL u%GetSingle(indx=3, VALUE=val)
CALL u%GetMultiple(indx=[4, 2], VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found(1:2) - [4.0_DFP, 2.0_DFP]) .LT. tol), &
        "GetMultiple indx")
! found(4:6) = u(1:3)
found = 0.0_DFP
CALL u%GetMultiple(istart=1, iend=3, stride=1, VALUE=found, &
                   istart_value=4, iend_value=6, stride_value=1, &
                   tsize=tsize)
CALL OK(tsize .EQ. 3, "GetMultiple range of value: tsize")
! found(2:6:2) = found(2:6:2) + 2 * u(1:5:2)   (GetMultiple4)
found = 1.0_DFP
CALL u%GetMultiple(istart=1, iend=5, stride=2, VALUE=found, &
                   istart_value=2, iend_value=6, stride_value=2, &
                   scale=2.0_DFP, addContribution=math%yes)
CALL OK(ALL(ABS(found - [1.0_DFP, 3.0_DFP, 1.0_DFP, 7.0_DFP, &
                         1.0_DFP, 11.0_DFP]) .LT. tol), &
        "GetMultiple: add")

CALL u%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/ScalarFieldLis/examples/Set_test_1.F90` (Get
  single)
- `classes:src/modules/ScalarFieldLis/examples/Set_test_2.F90` (Get
  all, Get selected)
- `classes:src/modules/ScalarFieldLis/examples/SetMultiple_test_1.F90`
  (`GetSingle`, `GetMultiple` with indices and ranges)
- `classes:src/modules/ScalarFieldLis/examples/SetMultiple_test_2.F90`
  (GetMultiple4)
- `classes:src/modules/ScalarFieldLis/examples/Set_test_4.F90` (native
  field from a LIS field)
- `classes:src/modules/ScalarFieldLis/examples/Get_test_1.F90` (Get4,
  `GetFEVariable`)
- `classes:src/modules/ScalarFieldLis/examples/Initiate_test_1.F90`
  (`Size`)
- `classes:src/modules/ScalarFieldLis/examples/Import_test_1.F90`
  (engine forced to `LIS_OMP`, values after `IMPORT`)
- `classes:src/modules/ScalarFieldLis/examples/ScalarFieldLis_test.toml`

## Pitfalls

- Pass `islocal=math%yes`. `islocal` is required by every `Get` form;
  `globalNode` is used as a local node number unchanged, and a debug
  build raises "global nodes are not local nodes" when `islocal` is
  false (`localNodeError.F90` in
  `classes:src/submodules/ScalarField/src/include/`).
- `GetPointer()` returns `NULL()` (and raises an error in a debug
  build). `realVec` is allocated but stale: only `Display` and `Export`
  fill it from the LIS vector. Do not read `realVec` directly.
- `VALUE` is not reallocated and its size is not checked: it must hold
  at least `tsize` entries (or the range `istart_value:` of the
  output).
- The range forms ignore `iend_value`: the count comes from the range
  of `obj`, and LIS writes from `istart_value` with `stride_value`
  (`obj_GetMultiple3`, `obj_GetMultiple4`).
- `VALUE` is `INTENT(OUT)` in `GetMultiple` with `tsize`; do not rely
  on entries outside the written ones. GetMultiple4 is `INTENT(INOUT)`
  and keeps them.
- The LIS error code (`CHKERR(ierr)`) is checked only in a debug
  build; in release a failing LIS call is not reported.
