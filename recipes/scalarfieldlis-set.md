# ScalarFieldLis: Setting values

**Purpose.** Set the values of a scalar field stored in a LIS vector
(`ScalarFieldLis_`): by node (`Set`), by index of the value vector
(`SetSingle`, `SetAll`, `SetMultiple`) and from another scalar field
of any engine (`=`, `Set(VALUE=field)`, `SetMultiple(VALUE=field)`).
`Set` is also the way to move values between the LIS and the native
engine.

**Classes.** `ScalarFieldLis_` (`ScalarFieldLis_Class`), which extends
`ScalarField_` (`ScalarField_Class`), which extends
`AbstractNodeField_`. `LisOmpEngine_` (`LisOmpEngine_Class`) starts and
stops LIS. Interfaces:
`classes:src/modules/ScalarFieldLis/src/ScalarFieldLis_Class.F90`
(index methods, `Set8`),
`classes:src/modules/ScalarField/src/ScalarField_Class.F90` (`Set`).
Implementations: `ScalarFieldLis_Class@SetMethods.F90` in
`classes:src/submodules/ScalarFieldLis/src/` and
`ScalarField_Class@SetMethods.F90` in
`classes:src/submodules/ScalarField/src/`. Getting values:
[ScalarFieldLis: Getting values](scalarfieldlis-get.md); BLAS:
[ScalarFieldLis: BLAS methods](scalarfieldlis-blas.md); native field:
[ScalarField: Setting and Getting values](scalarfield-set-get.md).

## Steps

1. **Start LIS and initiate** (as in the Get recipe): `lis%Initiate()`,
   `dom%ImportFromToml`, `u%ImportFromToml` with `engine = "LIS_OMP"`
   or `v%Initiate(NAME=, engine="LIS_OMP", fedof=, geofedof=)`. A new
   LIS vector is zero (docblock of `obj_Initiate2`). One value per DOF;
   node, DOF and index are the same number.
2. **Rule for every form.** Without `addContribution` the entry becomes
   `scale * VALUE`; with `addContribution=math%yes` `scale * VALUE` is
   added. `scale` defaults to 1. The LIS code is `LIS_INS_VALUE` or
   `LIS_ADD_VALUE`.
3. **By node** (`Set` generic of `ScalarField_`, `NON_OVERRIDABLE`;
   each form calls an index method below, so it writes the LIS vector):
   - `Set(globalNode, islocal, VALUE, [scale, addContribution])`: one
     node (Set1, `SetSingle`).
   - `Set(VALUE, ...)`, scalar: all (Set2, `SetAll`).
   - `Set(VALUE(:), ...)`: all from a vector, `SIZE(VALUE) >= Size()`
     (Set3, `SetMultiple` on the range).
   - `Set(globalNode(:), islocal, VALUE, ...)`: selected nodes to one
     value (Set4, `SetSingle` per node); with `VALUE(:)` one value per
     node (Set5, `SetMultiple` with `indx`); with a nodal `FEVariable_`
     (Set6, constant or space).
4. **By index** (overridden by `ScalarFieldLis_`):

   | Call | LIS routine |
   |---|---|
   | `SetSingle(indx, VALUE)` | `lis_vector_set_value` |
   | `SetAll(VALUE)` | `lis_vector_set_all` (add: loop of `set_value`) |
   | `SetMultiple(indx(:), VALUE(:))` | `lis_vector_set_values4` |
   | `SetMultiple(istart, iend, stride, VALUE(:))` | `_set_values5` |
   | `SetMultiple(<range>, VALUE(:), <value range>)` | `_set_values8` |
   | `SetMultiple(istart, iend, stride, VALUE)`, scalar | `_set_values6` |
   | `SetMultiple(<range>, VALUE=field, <value range>)` | see step 5 |

   `<range>` is `istart, iend, stride`; `<value range>` is
   `istart_value, iend_value, stride_value`; `_set_values5` means
   `lis_vector_set_values5`. All take optional `scale` and
   `addContribution`; the ranges hold `(iend - istart) / stride + 1`
   entries.
5. **From another field.**
   - `v = u` and `v%Set(VALUE=u)` (Set7) call `v%Set(VALUE=u,
     scale=1, addContribution=.FALSE.)`, i.e. `Set8`.
   - `v%Set(VALUE=u, scale=, addContribution=)` (Set8, both arguments
     required). `ScalarFieldLis_` overrides it: a `ScalarFieldLis_`
     `VALUE` is copied LIS to LIS (`lis_vector_set_values9`, no
     temporary); a `ScalarField_` `VALUE` is read through its
     `GetPointer`.
   - `SetMultiple(istart, iend, stride, VALUE=field, istart_value,
     iend_value, stride_value, ...)` (SetMultiple5): a native `VALUE`
     passes its vector to SetMultiple3; a LIS `VALUE` uses
     `lis_vector_set_values9`; other engines go through a temporary
     array.
   - Native `n` from LIS `u`: `n = u`, `n%Set(VALUE=u, ...)`; the
     native `Set8` reads `u` with `GetMultiple` into a temporary array.

Trimmed from `Set_test_1` to `Set_test_3`, `SetMultiple_test_1` and
`SetMultiple_test_2` of `ScalarFieldLis`:

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE ScalarField_Class, ONLY: ScalarField_
USE ScalarFieldLis_Class, ONLY: ScalarFieldLis_
USE Test_Method, ONLY: OK

CHARACTER(*), PARAMETER :: tomlFileName = "ScalarFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(ScalarFieldLis_) :: u, v
TYPE(ScalarField_) :: n
REAL(DFP) :: val, found(6), want(6)
INTEGER(I4B) :: tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL v%Initiate(NAME="v", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof)

! by node: 5, then 2 * 5, then + 3 * 1
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=5.0_DFP)
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=5.0_DFP, &
           scale=2.0_DFP)
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=1.0_DFP, &
           scale=3.0_DFP, addContribution=math%yes)
CALL u%Get(VALUE=val, globalNode=2, islocal=math%yes)
CALL OK(ABS(val - 13.0_DFP) .LT. tol, "Set single: add 3 * 1")

want = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL u%Set(VALUE=want)
CALL u%Set(globalNode=[1, 3, 5], islocal=math%yes, VALUE=0.0_DFP)
CALL u%Set(globalNode=[2, 4], islocal=math%yes, &
           VALUE=[20.0_DFP, 40.0_DFP])

! by index
CALL u%SetAll(VALUE=7.0_DFP)
CALL u%SetSingle(indx=3, VALUE=2.0_DFP, scale=4.0_DFP)
CALL u%SetMultiple(indx=[2, 4], VALUE=[10.0_DFP, 20.0_DFP], &
                   scale=2.0_DFP)
CALL u%SetMultiple(istart=1, iend=6, stride=3, VALUE=8.0_DFP, &
                   scale=0.5_DFP)
CALL u%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - [4.0_DFP, 20.0_DFP, 8.0_DFP, 4.0_DFP, &
                         7.0_DFP, 7.0_DFP]) .LT. tol), "by index")

! from another field: LIS <- LIS, LIS <- native
CALL u%Set(VALUE=want)
v = u
CALL v%Set(VALUE=u, scale=2.0_DFP, addContribution=math%yes)
CALL v%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - 3.0_DFP * want) .LT. tol), "v = v + 2 * u")
CALL n%Set(VALUE=10.0_DFP * want)
CALL v%Set(VALUE=n, scale=0.5_DFP, addContribution=math%no)
CALL v%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - 5.0_DFP * want) .LT. tol), "v = 0.5 * n")

! ranges (SetMultiple3, SetMultiple5); n = 10 * want from above
! u(2:6:2) = -1 * want(4:6)
CALL u%SetMultiple(istart=2, iend=6, stride=2, VALUE=want, &
                   istart_value=4, iend_value=6, stride_value=1, &
                   scale=-1.0_DFP)
! LIS <- native, u(2:6:2) = 0.5 * n(1:3)
CALL u%SetAll(VALUE=7.0_DFP)
CALL u%SetMultiple(istart=2, iend=6, stride=2, VALUE=n, &
                   istart_value=1, iend_value=3, stride_value=1, &
                   scale=0.5_DFP)
CALL u%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - [7.0_DFP, 5.0_DFP, 7.0_DFP, 10.0_DFP, &
                         7.0_DFP, 15.0_DFP]) .LT. tol), &
        "LIS <- native")
! same LIS field, ranges do not overlap: u(1:3) = u(4:6)
CALL u%Set(VALUE=want)
CALL u%SetMultiple(istart=1, iend=3, stride=1, VALUE=u, &
                   istart_value=4, iend_value=6, stride_value=1)
CALL u%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - [4.0_DFP, 5.0_DFP, 6.0_DFP, 4.0_DFP, &
                         5.0_DFP, 6.0_DFP]) .LT. tol), &
        "LIS <- same LIS field")

CALL n%DEALLOCATE()
CALL v%DEALLOCATE()
CALL u%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/ScalarFieldLis/examples/Set_test_1.F90` (single,
  all)
- `classes:src/modules/ScalarFieldLis/examples/Set_test_2.F90` (vector,
  selected nodes)
- `classes:src/modules/ScalarFieldLis/examples/Set_test_3.F90` (LIS
  from LIS and from native: `=`, Set8)
- `classes:src/modules/ScalarFieldLis/examples/Set_test_4.F90` (native
  from LIS)
- `classes:src/modules/ScalarFieldLis/examples/SetMultiple_test_1.F90`
  (`SetSingle`, `SetMultiple` with indices and ranges)
- `classes:src/modules/ScalarFieldLis/examples/SetMultiple_test_2.F90`
  (SetMultiple5 between engines and within one LIS field)
- `classes:src/modules/ScalarFieldLis/examples/COPY_test_1.F90`
  (`Set(VALUE=field)` between engines)
- `classes:src/modules/ScalarFieldLis/examples/ScalarFieldLis_test.toml`

## Pitfalls

- Pass `islocal=math%yes`. `islocal` is required by every by-node
  form; `globalNode` is used as a local node number unchanged, and a
  debug build raises "global nodes are not local nodes" when `islocal`
  is false.
- Without `addContribution` the result is `scale * VALUE`, not `VALUE`.
- `Set8` has no optional arguments: give both `scale` and
  `addContribution`, or use `v = u` / `v%Set(VALUE=u)`.
- `Set8` on a LIS `obj` uses `SELECT TYPE`: only `TYPE IS
  (ScalarField_)` and `TYPE IS (ScalarFieldLis_)` are handled. Any other
  type (an extension of `ScalarField_`) raises an error in a debug
  build and does nothing in release.
- `Set8` takes the count from `obj` and does not compare the sizes of
  `obj` and `VALUE`; use fields on the same `fedof`.
- Use `Set`, not `COPY` or `AXPY`, between engines; the BLAS methods
  need the same engine on both fields
  ([ScalarFieldLis: BLAS methods](scalarfieldlis-blas.md)).
- SetMultiple5: the count comes from the range of `obj` and
  `iend_value` is recomputed as `istart_value + (tsize - 1) *
  stride_value`. `obj` and `VALUE` may be the same field only if the
  two ranges do not overlap.
- `SetAll` with `addContribution=math%yes` calls
  `lis_vector_set_value` once per entry; without it a single
  `lis_vector_set_all`.
- Size checks (Set3, Set5) and LIS error codes (`CHKERR`) exist only in
  a debug build.
- `realVec` is not updated by `Set`; read values with `Get` (see
  [ScalarFieldLis: Getting values](scalarfieldlis-get.md)).
