# ScalarField: Setting and Getting values

**Purpose.** Set and read the values of a native `ScalarField_`
(engine `NATIVE_SERIAL`): by node number (`Set`, `Get`), by index of
the value vector (`SetSingle`, `SetAll`, `SetMultiple`, `GetSingle`,
`GetMultiple`), from another field (`=`, `Set(VALUE=field)`, `COPY`)
and through `GetPointer`.

**Classes.** `ScalarField_` (`ScalarField_Class`), which extends
`AbstractNodeField_` (`AbstractNodeField_Class`). Interfaces:
`classes:src/modules/ScalarField/src/ScalarField_Class.F90`,
`classes:src/modules/AbstractNodeField/src/AbstractNodeField_Class.F90`
(index methods). LIS storage (`ScalarFieldLis_`):
[ScalarFieldLis: Getting values](scalarfieldlis-get.md),
[ScalarFieldLis: Setting values](scalarfieldlis-set.md),
[ScalarFieldLis: BLAS methods](scalarfieldlis-blas.md).

## Steps

1. **Index layout.** A scalar field has one value per DOF of its FEDOF:
   the DOF object gets `tNodes = fedof%GetTotalDOF()`
   (`ScalarField_Class@ConstructorMethods.F90` in
   `classes:src/submodules/ScalarField/src/`).
   With one component, node `n` maps to index `n` in both storage
   formats (`GetNodeLoc` in
   `base:src/submodules/DOF/src/DOF_GetMethods@Methods.F90`), so
   "node", "DOF" and "index" are the same number. `Size()` returns
   `local_n`; it is 6 for `square_3x2.h5` with order 1
   (`classes:src/modules/ScalarField/examples/Set_test_5.F90`).
2. **Initiate from TOML.** `dom%ImportFromToml(filename=, tomlName=
   "domain")`, then `u%ImportFromToml(fedof=, geofedof=, dom=,
   filename=, tomlName="u")`. Further fields on the same FEDOF:
   `v%Initiate(NAME=, engine="NATIVE_SERIAL", fedof=, geofedof=)`.
3. **Set by node** (`Set` generic of `ScalarField_`; `VALUE` becomes
   `scale * VALUE`, or is added when `addContribution` is true; `scale`
   defaults to 1):
   - `Set(globalNode, islocal, VALUE, [scale, addContribution])`: one
     node (Set1, calls `SetSingle`).
   - `Set(VALUE, [scale, addContribution])`, scalar: all (Set2,
     `SetAll`).
   - `Set(VALUE(:), ...)`: all, from a vector, `SIZE(VALUE) >= Size()`
     (Set3, `SetMultiple` on the range).
   - `Set(globalNode(:), islocal, VALUE, ...)`: selected nodes to one
     value (Set4); with `VALUE(:)` one value per node (Set5); with a
     nodal `FEVariable_` (Set6, constant or space).
4. **Set by index** (`AbstractNodeField_`; all take optional `scale`,
   `addContribution`):
   - `SetSingle(indx, VALUE)`, `SetAll(VALUE)`.
   - `SetMultiple(indx(:), VALUE(:))` (SetMultiple1).
   - `SetMultiple(istart, iend, stride, VALUE(:))`: one value per index
     (SetMultiple2).
   - `SetMultiple(istart, iend, stride, VALUE(:), istart_value,
     iend_value, stride_value)`: from a range of an array (SetMultiple3).
   - `SetMultiple(istart, iend, stride, VALUE)`, scalar: one value in
     the range (SetMultiple4).
   - `SetMultiple(istart, iend, stride, VALUE=field, istart_value,
     iend_value, stride_value)`: from a range of another node field
     (SetMultiple5).
5. **From another field.** `v = u` and `v%Set(VALUE=u)` (Set7, also
   in the `Set` generic) call `v%Set(VALUE=u, scale=1,
   addContribution=.FALSE.)`, i.e. Set8. `v%Set(VALUE=u, scale=,
   addContribution=)` (Set8): here `scale` and `addContribution` are
   **required**. Both fields must have the same FEDOF.
   `v%COPY(obj2=u)` copies the values with BLAS (same engine only).
6. **Get by node.** `Get(VALUE, globalNode, islocal)` (Get1, one
   value), `Get(VALUE(:), tsize)` (Get2, all), `Get(VALUE(:),
   globalNode(:), islocal, tsize)` (Get3), `Get(VALUE=fevar,
   globalNode(:), islocal)` (Get4, nodal space `FEVariable_`, which must
   be initiated with enough room).
7. **Get by index.** `GetSingle(indx, VALUE)`; `GetMultiple(indx(:),
   VALUE, tsize)`; `GetMultiple(istart, iend, stride, VALUE, tsize)`;
   `GetMultiple(istart, iend, stride, VALUE, istart_value, iend_value,
   stride_value, tsize)` (into a range of `VALUE`); and GetMultiple4,
   the same without `tsize` but with optional `scale`,
   `addContribution`: `VALUE(range) = [VALUE(range) +] scale *
   obj(range)`.
8. **Pointer.** `ptr => x%GetPointer()` points at the value vector;
   writing through it changes the field
   (`classes:src/modules/AbstractNodeField/examples/GetPointer_test_1.F90`).

By node (trimmed from `Set_test_1`, `Set_test_2` and `Set_test_4` of
`ScalarField`; the three TOML files are identical):

```fortran
USE BaseType, ONLY: math => TypeMathOpt
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE ScalarField_Class, ONLY: ScalarField_
USE Test_Method, ONLY: OK

CHARACTER(*), PARAMETER :: tomlFileName = "Set_test_2.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(ScalarField_) :: u, v
REAL(DFP) :: val, found(6), want(6)
INTEGER(I4B) :: tsize

CALL e%SetQuietMode(math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                      filename=tomlFileName, tomlName="u")
CALL v%Initiate(NAME="v", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof)

! one node: 5, then 2 * 5, then + 3 * 1
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=5.0_DFP)
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=5.0_DFP, &
           scale=2.0_DFP)
CALL u%Set(globalNode=2, islocal=math%yes, VALUE=1.0_DFP, &
           scale=3.0_DFP, addContribution=math%yes)
CALL u%Get(VALUE=val, globalNode=2, islocal=math%yes)
CALL OK(ABS(val - 13.0_DFP) .LT. tol, "Set single: add 3 * 1")

! all from a vector, then selected nodes
want = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL u%Set(VALUE=want)
CALL u%Set(globalNode=[1, 3, 5], islocal=math%yes, VALUE=0.0_DFP)
CALL u%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - [0.0_DFP, 2.0_DFP, 0.0_DFP, 4.0_DFP, &
                         0.0_DFP, 6.0_DFP]) .LT. tol), &
        "Set selected: one value")
CALL u%Set(globalNode=[2, 4], islocal=math%yes, &
           VALUE=[20.0_DFP, 40.0_DFP])
CALL u%Get(VALUE=found, globalNode=[2, 4], islocal=math%yes, &
           tsize=tsize)
CALL OK(tsize .EQ. 2, "Get selected: tsize")

! from another field
CALL u%Set(VALUE=want)
v = u
CALL v%Set(VALUE=u, scale=2.0_DFP, addContribution=math%yes)
CALL v%Get(VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found - 3.0_DFP * want) .LT. tol), "v = v + 2 * u")
```

By index (trimmed from `SetMultiple_test_1` and `SetMultiple_test_3`
of `AbstractNodeField`, which use `AbstractNodeField_test.toml`):

```fortran
! USE items, dom, fedof, geofedof, tol: as in the first snippet
TYPE(ScalarField_) :: x, y
REAL(DFP) :: found(6), src(6)
INTEGER(I4B) :: tsize

! ... dom%ImportFromToml, x%ImportFromToml with AbstractNodeField_test.toml
CALL y%Initiate(NAME="y", engine="NATIVE_SERIAL", fedof=fedof, &
                geofedof=geofedof)
src = [1.0_DFP, 2.0_DFP, 3.0_DFP, 4.0_DFP, 5.0_DFP, 6.0_DFP]
CALL x%SetAll(VALUE=0.0_DFP)

CALL x%SetMultiple(indx=[2, 4], VALUE=[20.0_DFP, 40.0_DFP])
CALL x%GetMultiple(indx=[4, 2], VALUE=found, tsize=tsize)
CALL OK(ALL(ABS(found(1:2) - [40.0_DFP, 20.0_DFP]) .LT. tol), &
        "SetMultiple indx")
CALL x%SetMultiple(istart=1, iend=5, stride=2, &
                   VALUE=[1.0_DFP, 3.0_DFP, 5.0_DFP])
CALL x%SetMultiple(istart=2, iend=6, stride=2, VALUE=0.0_DFP)
! x(2:6:2) = src(1:3)
CALL x%SetMultiple(istart=2, iend=6, stride=2, VALUE=src, &
                   istart_value=1, iend_value=3, stride_value=1)
CALL x%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - [1.0_DFP, 1.0_DFP, 3.0_DFP, 2.0_DFP, &
                         5.0_DFP, 3.0_DFP]) .LT. tol), &
        "SetMultiple range: range of value")

CALL y%SetMultiple(istart=1, iend=6, stride=1, VALUE=src)
! found(2:6:2) = found(2:6:2) + 2 * y(1:5:2)   (GetMultiple4)
found = 1.0_DFP
CALL y%GetMultiple(istart=1, iend=5, stride=2, VALUE=found, &
                   istart_value=2, iend_value=6, stride_value=2, &
                   scale=2.0_DFP, addContribution=math%yes)
CALL OK(ALL(ABS(found - [1.0_DFP, 3.0_DFP, 1.0_DFP, 7.0_DFP, &
                         1.0_DFP, 11.0_DFP]) .LT. tol), &
        "GetMultiple: add")
! x(2:6:2) = 3 * y(1:3)   (SetMultiple5)
CALL x%SetAll(VALUE=7.0_DFP)
CALL x%SetMultiple(istart=2, iend=6, stride=2, VALUE=y, &
                   istart_value=1, iend_value=3, stride_value=1, &
                   scale=3.0_DFP)
CALL x%GetMultiple(istart=1, iend=6, stride=1, VALUE=found, &
                   tsize=tsize)
CALL OK(ALL(ABS(found - [7.0_DFP, 3.0_DFP, 7.0_DFP, 6.0_DFP, &
                         7.0_DFP, 9.0_DFP]) .LT. tol), &
        "SetMultiple field: set")
! same field, ranges do not overlap: y(1:3) = y(4:6)
CALL y%SetMultiple(istart=1, iend=3, stride=1, VALUE=y, &
                   istart_value=4, iend_value=6, stride_value=1)

CALL y%DEALLOCATE()
CALL x%DEALLOCATE()
```

## Example files (run from the `examples` directory)

- `classes:src/modules/ScalarField/examples/Set_test_1.F90` (single,
  all)
- `classes:src/modules/ScalarField/examples/Set_test_2.F90` (vector,
  selected nodes)
- `classes:src/modules/ScalarField/examples/Set_test_3.F90`
  (`FEVariable_`, `GetFEVariable`)
- `classes:src/modules/ScalarField/examples/Set_test_4.F90` (`v = u`,
  add)
- `classes:src/modules/ScalarField/examples/Set_test_5.F90` (`Size`,
  `v = scale * u`)
- `classes:src/modules/ScalarField/examples/Import_test_1.F90`
- `classes:src/modules/ScalarField/examples/ScalarField_test.toml`
- `classes:src/modules/AbstractNodeField/examples/SetMultiple_test_1.F90`
  to `SetMultiple_test_3.F90`, `SetSingle_test_1.F90`,
  `GetPointer_test_1.F90`, `COPY_test_1.F90` (index methods)

## Pitfalls

- `globalNode` must hold **local** node (DOF) numbers. Set and Get pass
  it on unchanged; a debug build raises "global nodes are not local
  nodes" when `islocal` is false
  (`classes:src/submodules/ScalarField/src/include/localNodeError.F90`).
  Pass `islocal=math%yes`. `islocal` is a required argument in every
  `Set`/`Get` form.
- Without `addContribution` the result is `scale * VALUE`, not `VALUE`
  (SetMultiple applies `scale` since 2026-10-29, see the `Changes`
  notes in `AbstractNodeField_Class.F90`).
- Set8 (`Set(VALUE=field, ...)`) has no optional arguments: give both
  `scale` and `addContribution`, or use `v = u` or `v%Set(VALUE=u)`.
- SetMultiple5 and GetMultiple4: the number of values is set by the
  range of `obj`; `iend_value` is recomputed as `istart_value + (tsize
  - 1) * stride_value`.
- GetMultiple with a range of `VALUE` (GetMultiple3) has
  `INTENT(OUT) :: VALUE`; do not rely on entries outside the range.
  GetMultiple4 is `INTENT(INOUT)` and keeps them.
- `obj` and `VALUE` of SetMultiple5 may be the same field only if the
  two ranges do not overlap.
- Other engines as source: SetMultiple5 writes into the native vector
  through `VALUE%GetMultiple4`, and Set8 reads a non-native `VALUE`
  into a temporary array with `GetMultiple` (a native `VALUE` through
  `GetPointer`), so `VALUE` may use any engine. `COPY` and the other
  BLAS methods need the same engine on both fields (checked only in a
  debug build); use `=` or `Set` across engines.
