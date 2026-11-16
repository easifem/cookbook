# STScalarFieldLis: BLAS methods

**Purpose.** Vector operations on space-time scalar fields stored in a
LIS vector (`STScalarFieldLis_`): `AXPY`, `SCAL`, `COPY`, `Swap`,
`Norm1`, `Norm2`, `Normi`, `Norm`, `DOT_PRODUCT`, `PMUL`, `Reciprocal`.

**Classes.** `STScalarFieldLis_` (`STScalarFieldLis_Class`) overrides
the BLAS bindings of `AbstractNodeField_` (`AbstractNodeField_Class`)
with LIS calls. `LisOmpEngine_` (`LisOmpEngine_Class`) starts and stops
LIS. Interfaces:
`classes:src/modules/STScalarFieldLis/src/STScalarFieldLis_Class.F90`,
`classes:src/modules/AbstractNodeField/src/AbstractNodeField_Class.F90`
(generic `AXPY`, `Norm`). Implementation: `@BlasMethods.F90` in
`classes:src/submodules/STScalarFieldLis/src/`.
Start-up: [STScalarFieldLis: Getting values](stscalarfieldlis-get.md).

## Steps

1. **Same engine.** Every field argument must use the LIS engine, like
   `obj`. The dummies are `CLASS(AbstractNodeField_)`; the methods use
   `x%lis_ptr` directly. To combine a native and a LIS field, move the
   values first with `Set(VALUE=field)`
   ([STScalarFieldLis: Setting values](stscalarfieldlis-set.md)), or
   use Set14, which is an AXPY across engines:
   `w%Set(VALUE=n, scale=, addContribution=math%yes)` gives
   `w = w + scale * n`.
2. **Methods** (all fields of the same size):
   - `AXPY(x, scale)`: `obj = obj + scale * x` (`lis_vector_axpy`).
   - `AXPY(x1, x2, a1, a2)`, `AXPY(x1, x2, x3, a1, a2, a3)`:
     `obj = obj + a1 * x1 + a2 * x2 [+ a3 * x3]`, one `lis_vector_axpy`
     per term.
   - `SCAL(scale)`: `obj = scale * obj` (`lis_vector_scale`).
   - `COPY(obj2)`: `obj = obj2` (`lis_vector_copy`).
   - `Swap(obj2)`: exchange the values (`lis_vector_swap`).
   - `Norm1()`, `Norm2()`, `Normi()`: L1, L2 and infinity norms
     (`lis_vector_nrm1`, `nrm2`, `nrmi`). `Norm(normType)` of
     `AbstractNodeField_` selects one of them with
     `TypeConvergenceOpt%normL1`, `normL2` or `normInfinity`
     (`USE BaseType, ONLY: TypeConvergenceOpt`).
   - `DOT_PRODUCT(obj2)`: `lis_vector_dot`.
   - `PMUL(obj1, obj2)`: `obj = obj1 * obj2`, entry by entry
     (`lis_vector_pmul`).
   - `Reciprocal()`: `obj = 1 / obj`, entry by entry
     (`lis_vector_reciprocal`).
3. **Check results** with `GetMultiple` (no `GetPointer` for LIS).

Trimmed from `AXPY_test_1` of `STScalarFieldLis` (x holds 1..12, y = 1,
z = 10; 12 values, `STScalarFieldLis_test.toml`) and Test 4 of
`Set_test_1` (cross-engine add):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE LisOmpEngine_Class, ONLY: LisOmpEngine_
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
TYPE(STScalarFieldLis_) :: x, y, z, w
TYPE(STScalarField_) :: n
REAL(DFP) :: src(12), found(12)
INTEGER(I4B) :: ii, tsize

CALL e%SetQuietMode(math%yes)
CALL lis%Initiate()
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL x%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
CALL y%Initiate(NAME="y", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
CALL z%Initiate(NAME="z", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
CALL w%Initiate(NAME="w", engine="LIS_OMP", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)

src = [(REAL(ii, DFP), ii=1, 12)]
CALL x%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)
CALL y%SetAll(VALUE=1.0_DFP)
CALL z%SetAll(VALUE=10.0_DFP)

CALL w%SetAll(VALUE=0.0_DFP)
CALL w%AXPY(x=x, scale=2.0_DFP)                       ! w = 2 x
CALL w%AXPY(x1=x, x2=y, a1=1.0_DFP, a2=-1.0_DFP)     ! w = 3 x - 1
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - (3.0_DFP * src - 1.0_DFP)) .LT. tol), &
        "AXPY: w + a1 * x1 + a2 * x2")

CALL w%COPY(obj2=x)
CALL w%SCAL(scale=-2.0_DFP)                           ! w = -2 x
CALL w%COPY(obj2=x)
CALL w%Swap(obj2=y)                                   ! w = 1, y = x

CALL OK(ABS(x%Norm1() - 78.0_DFP) .LT. tol, "Norm1")
CALL OK(ABS(x%Norm2() - SQRT(650.0_DFP)) .LT. tol, "Norm2")
CALL OK(ABS(x%Normi() - 12.0_DFP) .LT. tol, "Normi")
CALL OK(ABS(x%DOT_PRODUCT(obj2=z) - 780.0_DFP) .LT. tol, "DOT_PRODUCT")

CALL w%PMUL(obj1=x, obj2=z)                           ! w = 10 x
CALL w%Reciprocal()                                   ! w = 0.1 / x
CALL w%GetMultiple(istart=1, iend=12, stride=1, VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - 0.1_DFP / src) .LT. tol), "Reciprocal")

! native n: no BLAS with w; add it with Set14 (any engine)
CALL n%Initiate(NAME="n", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof, timefedof=timefedof)
CALL n%SetMultiple(istart=1, iend=12, stride=1, VALUE=src)
CALL w%SetAll(VALUE=1.0_DFP)
CALL w%Set(VALUE=n, scale=0.5_DFP, addContribution=math%yes)

CALL n%DEALLOCATE()
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

## Example files (run from the `examples` directory)

- `classes:src/modules/STScalarFieldLis/examples/AXPY_test_1.F90` (all
  BLAS methods except `Norm`)
- `classes:src/modules/STScalarFieldLis/examples/Set_test_1.F90` (Test
  4: `Set(VALUE=, scale=, addContribution=)` across engines)
- `classes:src/modules/AbstractNodeField/examples/Norm_test_1.F90`
  (`Norm(normType)`, native engine)
- `classes:src/modules/STScalarFieldLis/examples/STScalarFieldLis_test.toml`

## Pitfalls

- The engine check (`obj%GetEngineName() .EQ. x%GetEngineName()`, in
  `AXPY`, `COPY`, `Swap`, `DOT_PRODUCT`, `PMUL`) runs in debug builds
  only, with the message "use Set(VALUE=x) between engines". In
  release a native argument passes its `lis_ptr`, which is 0
  (`AbstractField_` default); a native `obj` with a LIS argument
  reads the argument's `realVec`, which is not up to date.
- Only the engine name is compared, not the type or the size. Only
  `Swap` checks `Size()` (debug builds); for the others a size mismatch
  is left to LIS, whose error code is checked in debug builds only.
- `COPY` copies values only: both fields must be initiated with LIS
  vectors. To create a copy use `Initiate(obj2=, copyFull=math%yes)`.
- `Reciprocal` divides by every entry; no entry may be zero.
- `Norm(normType)` is not overridden; it calls the overridden `Norm1`,
  `Norm2` or `Normi` (code). No LIS test calls it (unverified for LIS).
