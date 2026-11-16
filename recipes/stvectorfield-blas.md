# STVectorField: BLAS methods

**Purpose.** Combine and measure space-time vector fields with the
BLAS1 methods: `AXPY` (one, two or three fields), `SCAL`, `COPY`,
`Swap`, `Norm1`, `Norm2`, `Normi`, `Norm(normType)`, `DOT_PRODUCT`,
`PMUL`, `Reciprocal`. They act on all values of the field at once.

**Classes.** `STVectorField_` (`STVectorField_Class`) has no BLAS code
of its own: it inherits the methods of `AbstractNodeField_`, which work
on `realVec`. `STVectorFieldLis_` (`STVectorFieldLis_Class`) overrides
all of them except `Norm(normType)` with LIS calls (`lis_vector_axpy`,
`lis_vector_copy`, ...). Interfaces:
`classes:src/modules/AbstractNodeField/src/AbstractNodeField_Class.F90`,
`classes:src/modules/STVectorFieldLis/src/STVectorFieldLis_Class.F90`.
Implementations: `@BlasMethods.F90` in
`classes:src/submodules/AbstractNodeField/src/` and
`classes:src/submodules/STVectorFieldLis/src/`.

## Steps

1. **Fields.** Initiate all fields on the same `fedof`, `geofedof`,
   `timefedof` and `spaceCompo`, **and with the same engine** (see
   [STVectorField: Setting values](stvectorfield-set.md)).
2. **Update.**
   - `y%AXPY(x=, scale=)`: `y = y + scale * x`.
   - `y%AXPY(x1=, x2=, a1=, a2=)`: `y = y + a1 * x1 + a2 * x2`.
   - `y%AXPY(x1=, x2=, x3=, a1=, a2=, a3=)`: three fields.
   - `y%SCAL(scale=)`: `y = scale * y`.
   - `y%COPY(obj2=x)`: `y = x` (values only).
   - `y%Swap(obj2=x)`: exchange the values.
   - `z%PMUL(obj1=x, obj2=y)`: `z = x * y`, entry by entry.
   - `y%Reciprocal()`: `y = 1 / y`, entry by entry (no zero check).
3. **Measure** (functions returning `REAL(DFP)`): `x%Norm1()`
   (`SUM(ABS(x))`), `x%Norm2()`, `x%Normi()` (`MAXVAL(ABS(x))`),
   `x%Norm(normType)` with `TypeConvergenceOpt%normL1`, `normL2` or
   `normInfinity` (`BaseType`), `x%DOT_PRODUCT(obj2=y)`.
4. **Different engines.** Move the values first with `Set(VALUE=)`
   (Set14), which works between engines, then call BLAS on fields of
   one engine.

Trimmed from `AXPY_test_1` of `STVectorFieldLis` (24 values: 6 nodes,
`spaceCompo = 2`, `timeCompo = 2`):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE STVectorFieldLis_Class, ONLY: STVectorFieldLis_
USE Test_Method, ONLY: OK
USE TimeFEDOF_Class, ONLY: TimeFEDOF_

CHARACTER(*), PARAMETER :: tomlFileName = "STVectorFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STVectorFieldLis_) :: x, y, z, w
REAL(DFP) :: src(24), found(24)
INTEGER(I4B) :: ii, tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL x%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
CALL y%Initiate(NAME="y", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof, timefedof=timefedof)
CALL z%Initiate(NAME="z", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof, timefedof=timefedof)
CALL w%Initiate(NAME="w", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof, timefedof=timefedof)

src = [(REAL(ii, DFP), ii=1, 24)]
CALL x%SetMultiple(istart=1, iend=24, stride=1, VALUE=src)
CALL y%SetAll(VALUE=1.0_DFP)
CALL z%SetAll(VALUE=10.0_DFP)

CALL w%SetAll(VALUE=0.0_DFP)
CALL w%AXPY(x=x, scale=2.0_DFP)
CALL w%AXPY(x1=x, x2=y, a1=1.0_DFP, a2=-1.0_DFP)
CALL w%AXPY(x1=y, x2=z, x3=x, a1=1.0_DFP, a2=0.1_DFP, a3=-1.0_DFP)
CALL w%GetMultiple(istart=1, iend=24, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - (2.0_DFP * src + 1.0_DFP)) .LT. tol), &
        "AXPY: w + a1 * x1 + a2 * x2 + a3 * x3")

CALL w%COPY(obj2=x)
CALL w%SCAL(scale=-2.0_DFP)
CALL w%COPY(obj2=x)
CALL w%Swap(obj2=y)                     ! w = 1, y = src

CALL OK(ABS(x%Norm1() - 300.0_DFP) .LT. tol, "Norm1")
CALL OK(ABS(x%Norm2() - SQRT(4900.0_DFP)) .LT. tol, "Norm2")
CALL OK(ABS(x%Normi() - 24.0_DFP) .LT. tol, "Normi")
CALL OK(ABS(x%DOT_PRODUCT(obj2=z) - 3000.0_DFP) .LT. tol, "DOT_PRODUCT")

CALL w%PMUL(obj1=x, obj2=z)             ! w = 10 * src
CALL w%Reciprocal()                     ! w = 0.1 / src

CALL w%DEALLOCATE()
CALL z%DEALLOCATE()
CALL y%DEALLOCATE()
CALL x%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

Native `STVectorField_` (unverified: no test of BLAS on a native
`STVectorField_`; the native methods are tested on `ScalarField_` in
`classes:src/modules/AbstractNodeField/examples/`): the same calls with
`TYPE(STVectorField_)`, `STVectorField_test.toml`,
`engine="NATIVE_SERIAL"` and without `lis`. Mixing engines (trimmed
from `Set_test_2` of `STVectorFieldLis`; `u` is LIS, `n` native):

```fortran
! want(24): values; u: STVectorFieldLis_; n: STVectorField_, NATIVE_SERIAL
CALL n%SetMultiple(istart=1, iend=24, stride=1, VALUE=want)
CALL u%Set(VALUE=n)                     ! LIS <- native, then BLAS on LIS
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STVectorFieldLis/examples/AXPY_test_1.F90` (all
  BLAS methods, LIS)
- `classes:src/modules/STVectorFieldLis/examples/Set_test_2.F90` (Set14
  between engines)
- `classes:src/modules/STVectorFieldLis/examples/STVectorFieldLis_test.toml`
- `classes:src/modules/AbstractNodeField/examples/AXPY_test_1.F90`,
  `SCAL_test_1.F90`, `COPY_test_1.F90`, `Swap_test_1.F90`,
  `Norm_test_1.F90`, `DOT_PRODUCT_test_1.F90`, `PMUL_test_1.F90`,
  `Reciprocal_test_1.F90` (native methods, on `ScalarField_`)

## Pitfalls

- **Same engine.** `AXPY`, `COPY`, `Swap`, `DOT_PRODUCT` and `PMUL`
  require every field to use the engine of `obj`. This is checked only
  in debug builds ("x uses another engine than obj, use Set(VALUE=x)
  between engines"). In release a native `obj` reads `x%realVec` of a
  LIS `x`, which is not up to date, and a LIS `obj` reads `lis_ptr` of a
  native `x`, which is not created (from reading the code; no test).
  Use Set14 to move values between engines.
- Sizes: only `Swap` checks `obj%Size() = obj2%Size()` (debug builds).
  `AXPY`, `DOT_PRODUCT` and `PMUL` do not check; fields on the same
  FEDOFs and `spaceCompo` have the same size.
- `COPY` copies values only, not the FEDOF or DOF data; use
  `Initiate(obj2=)` for a new field and `Set(VALUE=)` between engines.
- `Norm(normType)` is not overridden by `STVectorFieldLis_`; it calls
  `obj%Norm1`, `Norm2` or `Normi`, which are. An unknown `normType`
  raises an error only in debug builds (`ans` is not set in release).
- LIS: the LIS library must be initiated (`LisOmpEngine_%Initiate`)
  before the fields and finalized after they are deallocated.
