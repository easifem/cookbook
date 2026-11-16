# VectorField: BLAS methods

**Purpose.** Combine and measure the values of `VectorField_` objects
with the BLAS-1 methods: `AXPY` (one, two or three fields), `SCAL`,
`COPY`, `Swap`, `Norm1`, `Norm2`, `Normi`, `Norm`, `DOT_PRODUCT`,
`PMUL` and `Reciprocal`; and move values between engines first when
the fields use different engines.

**Classes.** The methods belong to `AbstractNodeField_`
(`AbstractNodeField_Class`); `VectorField_` inherits them unchanged and
`VectorFieldLis_` overrides them with LIS calls. Interfaces:
`classes:src/modules/AbstractNodeField/src/AbstractNodeField_Class.F90`,
`classes:src/modules/VectorFieldLis/src/VectorFieldLis_Class.F90`.
Implementations: `@BlasMethods.F90` in
`classes:src/submodules/AbstractNodeField/src/` (BLAS of
`RealVector_` on `realVec`) and in
`classes:src/submodules/VectorFieldLis/src/` (`lis_vector_*` on
`lis_ptr`).

## Steps

1. **Same engine.** All fields of one call must use the same engine
   (`GetEngineName()`). Check it, or move the values first with
   `Set(VALUE=field)` (see step 4).
2. **Methods.** All act on every entry of the value vector (all
   components of all DOFs, layout of
   [VectorField: Setting values](vectorfield-set.md)).
   - `obj%AXPY(x=, scale=)`: `obj = obj + scale * x`.
   - `obj%AXPY(x1=, x2=, a1=, a2=)`: `obj = obj + a1 x1 + a2 x2`.
   - `obj%AXPY(x1=, x2=, x3=, a1=, a2=, a3=)`: three fields.
   - `obj%SCAL(scale=)`: `obj = scale * obj`.
   - `obj%COPY(obj2=)`: `obj = obj2` (values only).
   - `obj%Swap(obj2=)`: exchange the values.
   - `obj%Norm1()`, `obj%Norm2()`, `obj%Normi()`: `SUM(ABS(obj))`,
     `SQRT(SUM(obj**2))`, `MAXVAL(ABS(obj))`; `obj%Norm(normType)`
     with `TypeConvergenceOpt%normL1`, `normL2` or `normInfinity`
     (`BaseType`).
   - `obj%DOT_PRODUCT(obj2)`: `SUM(obj * obj2)`.
   - `obj%PMUL(obj1=, obj2=)`: `obj = obj1 * obj2`, entry by entry.
   - `obj%Reciprocal()`: `obj = 1 / obj`, entry by entry.
3. **Arguments.** All scales are required (no defaults). `x`, `x1`,
   `x2`, `x3` are `INTENT(INOUT)`; `obj2` of `COPY`, `DOT_PRODUCT` and
   `obj1`, `obj2` of `PMUL` are `INTENT(IN)`. They are
   `CLASS(AbstractNodeField_)`, so a `ScalarField_` of the same size
   type-checks too.
4. **Mixed engines.** Copy the LIS field into a native one (or the
   other way) with `Set(VALUE=)` (Set13) or the assignment `n = u`,
   which calls Set13; then call the BLAS method on fields of one
   engine.

All BLAS methods, LIS engine (trimmed from `AXPY_test_1` of
`VectorFieldLis`; 12 values, 6 nodes, `spaceCompo = 2`). For a native
`VectorField_` the calls are the same: declare `TYPE(VectorField_)`,
use `engine="NATIVE_SERIAL"` and `VectorField_test.toml`, and drop
`lis`, as in the native test
`classes:src/modules/VectorField/examples/AXPY_test_1.F90` (same values,
plus `Norm(normType)`).

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
USE Test_Method, ONLY: OK
USE VectorFieldLis_Class, ONLY: VectorFieldLis_

CHARACTER(*), PARAMETER :: tomlFileName = "VectorFieldLis_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(LisOmpEngine_) :: lis
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(VectorFieldLis_) :: x, y, z, w
REAL(DFP) :: src(12), found(12)
INTEGER(I4B) :: ii, tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL x%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL y%Initiate(NAME="y", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
CALL z%Initiate(NAME="z", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)
CALL w%Initiate(NAME="w", engine="LIS_OMP", spaceCompo=2, &
                fedof=fedof, geofedof=geofedof)

src = [(REAL(ii, DFP), ii=1, 12)]
CALL x%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)
CALL y%SetAll(VALUE=1.0_DFP)
CALL z%SetAll(VALUE=10.0_DFP)

CALL w%SetAll(VALUE=0.0_DFP)
CALL w%AXPY(x=x, scale=2.0_DFP)
CALL w%AXPY(x1=x, x2=y, a1=1.0_DFP, a2=-1.0_DFP)
CALL w%AXPY(x1=y, x2=z, x3=x, a1=1.0_DFP, a2=0.1_DFP, a3=-1.0_DFP)
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - (2.0_DFP * src + 1.0_DFP)) .LT. tol), &
        "AXPY: w + a1 * x1 + a2 * x2 + a3 * x3")

CALL w%COPY(obj2=x)
CALL w%SCAL(scale=-2.0_DFP)
CALL w%COPY(obj2=x)
CALL w%Swap(obj2=y)                 ! w = 1, y = src

CALL OK(ABS(x%Norm1() - 78.0_DFP) .LT. tol, "Norm1")
CALL OK(ABS(x%Norm2() - SQRT(650.0_DFP)) .LT. tol, "Norm2")
CALL OK(ABS(x%Normi() - 12.0_DFP) .LT. tol, "Normi")
CALL OK(ABS(x%DOT_PRODUCT(obj2=z) - 780.0_DFP) .LT. tol, "DOT_PRODUCT")

CALL w%PMUL(obj1=x, obj2=z)         ! w = 10 * src
CALL w%Reciprocal()                 ! w = 0.1 / src
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - 0.1_DFP / src) .LT. tol), "Reciprocal")

CALL w%DEALLOCATE()
CALL z%DEALLOCATE()
CALL y%DEALLOCATE()
CALL x%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()
CALL lis%DEALLOCATE()
```

Mixed engines: first copy, then BLAS (the copy is Test 1 of
`Set_test_2` of `VectorFieldLis`; the `AXPY` line is not in a test,
(unverified); `n`, `m` are native):

```fortran
TYPE(VectorFieldLis_) :: u            ! engine LIS_OMP
TYPE(VectorField_) :: n, m            ! engine NATIVE_SERIAL

CALL n%Set(VALUE=u)                   ! native <- LIS (Set13)
CALL m%AXPY(x=n, scale=2.0_DFP)       ! native + native
! not: CALL m%AXPY(x=u, scale=2.0_DFP)
```

## Example files (run from the `examples` directory)

- `classes:src/modules/VectorFieldLis/examples/AXPY_test_1.F90` (all
  BLAS methods, LIS)
- `classes:src/modules/VectorField/examples/AXPY_test_1.F90` (all BLAS
  methods and `Norm(normType)`, native `VectorField_`)
- `classes:src/modules/VectorFieldLis/examples/Set_test_2.F90` (copy
  across engines)
- `classes:src/modules/VectorFieldLis/examples/VectorFieldLis_test.toml`
- `classes:src/modules/AbstractNodeField/examples/AXPY_test_1.F90`,
  `SCAL_test_1.F90`, `COPY_test_1.F90`, `Swap_test_1.F90`,
  `Norm_test_1.F90`, `DOT_PRODUCT_test_1.F90`, `PMUL_test_1.F90`,
  `Reciprocal_test_1.F90` (native, with `ScalarField_`)

## Pitfalls

- The engine check (`obj%GetEngineName() .EQ. x%GetEngineName()`) is
  in debug builds only: AXPY, COPY, Swap, DOT_PRODUCT and PMUL raise
  "... uses another engine than obj, use Set(VALUE=...) between
  engines". A release build does not check. The method runs for the
  engine of `obj` (dynamic dispatch on `obj` only) and reads `realVec`
  or `lis_ptr` of the other fields, so mixing engines gives wrong
  values: a LIS field does not keep `realVec` up to date (see the type
  docblock in `VectorFieldLis_Class.F90`).
- `COPY` is not `Set(VALUE=)`: it copies values only between fields
  of the same engine. `Set(VALUE=)` and `Get(VALUE=)` work for every
  engine pair.
- Sizes are not checked, except by `Swap` (debug builds). Use fields
  on the same FEDOF with the same `spaceCompo`.
- `Norm*` and `DOT_PRODUCT` take all entries, so they mix the
  components; they are not a vector norm per node.
- `Reciprocal`: no entry may be zero.
- `Norm(normType)` with another `normType` leaves the result
  undefined; a debug build raises "No case found for normType".
