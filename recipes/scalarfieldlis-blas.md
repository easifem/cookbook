# ScalarFieldLis: BLAS methods

**Purpose.** Vector operations on the values of a `ScalarFieldLis_`:
`AXPY` (with one, two or three fields), `SCAL`, `COPY`, `Swap`,
`Norm1`, `Norm2`, `Normi`, `Norm(normType)`, `DOT_PRODUCT`, `PMUL` and
`Reciprocal`. They call the LIS vector routines on `lis_ptr`, so every
field argument must also use the LIS engine. Values are moved between
engines with `Set`, not with the BLAS methods.

**Classes.** `ScalarFieldLis_` (`ScalarFieldLis_Class`), which extends
`ScalarField_` and `AbstractNodeField_`; `LisOmpEngine_`
(`LisOmpEngine_Class`) starts and stops LIS. Interfaces:
`classes:src/modules/ScalarFieldLis/src/ScalarFieldLis_Class.F90`
(section `@BlasMethods`). Implementation:
`ScalarFieldLis_Class@BlasMethods.F90` in
`classes:src/submodules/ScalarFieldLis/src/`. The native versions (for
`NATIVE_SERIAL` fields, on `realVec`) are in
`AbstractNodeField_Class@BlasMethods.F90` in
`classes:src/submodules/AbstractNodeField/src/`. Getting and setting
values: [ScalarFieldLis: Getting values](scalarfieldlis-get.md),
[ScalarFieldLis: Setting values](scalarfieldlis-set.md).

## Steps

1. **Start LIS and initiate the fields.** `lis%Initiate()` first, then
   the fields with `engine="LIS_OMP"` on the same `fedof` (same size),
   e.g. `x%ImportFromToml(...)` and `y%Initiate(NAME=, engine=
   "LIS_OMP", fedof=, geofedof=)`. Fill them with `Set`/`SetMultiple`
   (see [ScalarFieldLis: Setting values](scalarfieldlis-set.md)).
2. **Call the method on the result field.** The type of `obj` selects
   the implementation; `x`, `obj1`, `obj2` must have the engine of
   `obj`.

   | Call | Result | LIS routine |
   |---|---|---|
   | `w%AXPY(x=, scale=)` | `w = w + scale * x` | `lis_vector_axpy` |
   | `w%AXPY(x1=, x2=, a1=, a2=)` | `w = w + a1 x1 + a2 x2` | axpy, twice |
   | `w%AXPY(x1=, x2=, x3=, a1=, a2=, a3=)` | also `+ a3 x3` | axpy, 3 times |
   | `w%SCAL(scale=)` | `w = scale * w` | `lis_vector_scale` |
   | `w%COPY(obj2=)` | `w = obj2` | `lis_vector_copy` |
   | `w%Swap(obj2=)` | values exchanged | `lis_vector_swap` |
   | `x%Norm1()` | `SUM(ABS(x))` | `lis_vector_nrm1` |
   | `x%Norm2()` | `SQRT(SUM(x**2))` | `lis_vector_nrm2` |
   | `x%Normi()` | `MAXVAL(ABS(x))` | `lis_vector_nrmi` |
   | `x%DOT_PRODUCT(obj2=)` | `SUM(x * obj2)` | `lis_vector_dot` |
   | `z%PMUL(obj1=, obj2=)` | `z(i) = obj1(i) * obj2(i)` | `lis_vector_pmul` |
   | `z%Reciprocal()` | `z(i) = 1 / z(i)` | `lis_vector_reciprocal` |

   `AXPY` is a generic (`AXPY1`, `AXPY2`, `AXPY3`) of
   `AbstractNodeField_`; `ScalarFieldLis_` overrides the specific
   bindings. `Norm(normType)` is not overridden: the `AbstractNodeField_`
   version selects `Norm1`, `Norm2` or `Normi` from
   `TypeConvergenceOpt%normL1`, `normL2`, `normInfinity` (BaseType), so
   it reaches the LIS norms by dynamic dispatch
   (`classes:src/modules/ScalarFieldLis/examples/Norm_test_1.F90`).
3. **Between engines use Set.** `x%Set(VALUE=n)` or `x = n` (LIS <-
   native), `n%Set(VALUE=x)` (native <- LIS), `Set(VALUE=, scale=,
   addContribution=)` to scale or add, `SetMultiple(..., VALUE=field,
   ...)` for ranges
   (`classes:src/modules/ScalarFieldLis/examples/COPY_test_1.F90`).
4. **Read the result** with `Get` or `GetMultiple` (not `GetPointer`,
   which returns `NULL()` for LIS). Deallocate the fields, then call
   `lis%DEALLOCATE()`.

Trimmed from `AXPY_test_1`, `Norm2_test_1` and `COPY_test_1` of
`ScalarFieldLis` (six DOFs: `square_3x2.h5`, order 1, from
`ScalarFieldLis_test.toml`):

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
TYPE(ScalarFieldLis_) :: x, y, z, w
TYPE(ScalarField_) :: n
REAL(DFP) :: src(6), ysrc(6), found(6)
INTEGER(I4B) :: tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL x%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL y%Initiate(NAME="y", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
CALL z%Initiate(NAME="z", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
CALL w%Initiate(NAME="w", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof)
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof)

src = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL x%SetMultiple(istart=1, iend=6, stride=1, VALUE=src)
CALL y%SetAll(VALUE=1.0_DFP)
CALL z%SetAll(VALUE=10.0_DFP)

! AXPY with one, two and three fields
CALL w%SetAll(VALUE=0.0_DFP)
CALL w%AXPY(x=x, scale=2.0_DFP)
CALL w%AXPY(x1=x, x2=y, a1=1.0_DFP, a2=-1.0_DFP)
CALL w%AXPY(x1=y, x2=z, x3=x, a1=1.0_DFP, a2=0.1_DFP, a3=-1.0_DFP)
CALL w%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - (2.0_DFP * src + 1.0_DFP)) .LT. tol), &
        "AXPY: w + a1 * x1 + a2 * x2 + a3 * x3")

! COPY, SCAL, Swap
CALL w%COPY(obj2=x)
CALL w%SCAL(scale=-2.0_DFP)
CALL w%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found + 2.0_DFP * src) .LT. tol), "SCAL")
CALL w%COPY(obj2=x)
CALL w%Swap(obj2=y)
CALL y%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - src) .LT. tol), "Swap: y = old w")

! norms, dot product, PMUL, Reciprocal
src = [1.0_DFP, -2.0_DFP, 3.0_DFP, -4.0_DFP, 5.0_DFP, -6.0_DFP]
ysrc = [1.0_DFP, 1.0_DFP, 1.0_DFP, 2.0_DFP, 2.0_DFP, 2.0_DFP]
CALL x%SetMultiple(istart=1, iend=6, stride=1, VALUE=src)
CALL y%SetMultiple(istart=1, iend=6, stride=1, VALUE=ysrc)
CALL OK(ABS(x%Norm1() - 21.0_DFP) .LT. tol, "Norm1")
CALL OK(ABS(x%Norm2() - SQRT(91.0_DFP)) .LT. tol, "Norm2")
CALL OK(ABS(x%Normi() - 6.0_DFP) .LT. tol, "Normi")
CALL OK(ABS(x%DOT_PRODUCT(obj2=y) + 8.0_DFP) .LT. tol, "DOT_PRODUCT")
CALL z%PMUL(obj1=x, obj2=y)
CALL z%Reciprocal()
CALL z%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - 1.0_DFP / (src * ysrc)) .LT. tol), &
        "Reciprocal")

! another engine: Set, not COPY or AXPY
CALL n%SetMultiple(istart=1, iend=6, stride=1, VALUE=-src)
CALL x%Set(VALUE=n)                    ! LIS <- native
CALL n%Set(VALUE=x)                    ! native <- LIS
CALL n%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found + src) .LT. tol), "native <- LIS <- native")

CALL n%DEALLOCATE()
CALL w%DEALLOCATE()
CALL z%DEALLOCATE()
CALL y%DEALLOCATE()
CALL x%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/ScalarFieldLis/examples/AXPY_test_1.F90` (AXPY,
  SCAL, COPY, Swap)
- `classes:src/modules/ScalarFieldLis/examples/Norm2_test_1.F90`
  (norms, DOT_PRODUCT, PMUL, Reciprocal)
- `classes:src/modules/ScalarFieldLis/examples/Norm_test_1.F90`
  (`Norm(normType)`)
- `classes:src/modules/ScalarFieldLis/examples/COPY_test_1.F90` (COPY
  between LIS fields, Set between engines)
- `classes:src/modules/ScalarFieldLis/examples/ScalarFieldLis_test.toml`
- Native counterparts: `AXPY_test_1.F90`, `SCAL_test_1.F90`,
  `COPY_test_1.F90`, `Swap_test_1.F90`, `Norm_test_1.F90`,
  `DOT_PRODUCT_test_1.F90`, `PMUL_test_1.F90`, `Reciprocal_test_1.F90`
  in `classes:src/modules/AbstractNodeField/examples/`

## Pitfalls

- **Same engine.** `AXPY`, `COPY`, `Swap`, `DOT_PRODUCT` and `PMUL`
  compare `GetEngineName()` of the fields only in a debug build
  ("... uses another engine than obj, use Set(VALUE=...) between
  engines"). A release build does not check. A native field passed to
  a LIS method has `lis_ptr = 0` (default in `AbstractField_`), and
  the LIS error code is checked (`CHKERR`) only in debug builds. A LIS
  field passed to a native method is read from its `realVec`, which is
  stale, so the result is silently wrong.
- **Sizes are not checked**, except by `Swap` (debug build,
  `AssertError2` on `Size()`). Use fields on the same `fedof`.
- The BLAS methods change only the LIS vector; `realVec` of a LIS field
  is filled only by `Display` and `Export`. Read values with `Get` or
  `GetMultiple`.
- `Swap` exchanges the values only; name, `fedof`, DOF data stay.
- `Reciprocal`: no entry may be zero (docblock of `obj_Reciprocal`).
- `Normi` needs a LIS built after the 2026-11-14 fix of
  `lis_vector_nrmi` in the OpenMP build (`Changes` of `obj_Normi`);
  older LIS builds return a wrong value.
- `x`, `x1`, `x2`, `x3` of `AXPY` and `obj2` of `Swap` are
  `INTENT(INOUT)`: an `INTENT(IN)` dummy argument cannot be passed.
  `obj2` of `COPY` and `DOT_PRODUCT`, `obj1`/`obj2` of `PMUL` are
  `INTENT(IN)`.
- Start LIS (`LisOmpEngine_%Initiate`) before initiating a LIS field
  and stop it (`LisOmpEngine_%DEALLOCATE`) after all LIS fields are
  deallocated.
