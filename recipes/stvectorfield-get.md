# STVectorField: Getting values

**Purpose.** Read the values of a space-time vector field
`STVectorField_` (and of `STVectorFieldLis_`, same API on a LIS vector):
by node, space component and time component (`Get`, Get1..Get7), in a
`FEVariable_` (`GetFEVariable`), into a `VectorField_`
(`SetToVectorField`), and by index of the value vector (`GetSingle`,
`GetMultiple`).

**Classes.** `STVectorField_` (`STVectorField_Class`), which extends
`AbstractNodeField_`; `STVectorFieldLis_` (`STVectorFieldLis_Class`),
which extends `STVectorField_`. Interfaces:
`classes:src/modules/STVectorField/src/STVectorField_Class.F90`,
`classes:src/modules/AbstractNodeField/src/AbstractNodeField_Class.F90`
(index methods). Implementation:
`classes:src/submodules/STVectorField/src/STVectorField_Class@GetMethods.F90`.
Setting values: [STVectorField: Setting values](stvectorfield-set.md).

## Steps

1. **Data layout.** One physical variable, `spaceCompo` space and
   `timeCompo` time components (`timeCompo = timefedof%GetTotalDOF()`
   when `timefedof` is given and initiated). `Size()` is
   `fedof%GetTotalDOF() * spaceCompo * timeCompo`. Values are stored in
   DOF format: component `(s, t)` is the local DOF
   `idof = (t - 1) * spaceCompo + s`, and DOF `i` of it is index
   `(idof - 1) * tNodes + i` (`tNodes = fedof%GetTotalDOF()`; interface
   docblock of `obj_Initiate2`). With `STVectorField_test.toml` (six
   nodes, `spaceCompo = 2`, order 1 in space and time) `timeCompo = 2`
   and `Size() = 24`
   (`classes:src/modules/STVectorField/examples/Initiate_test_1.F90`);
   node 2 is index 2, 8, 14, 20
   (`classes:src/modules/STVectorField/examples/Set_test_1.F90`).
2. **Get1** `Get(VALUE(:), tsize, [globalNode, spaceCompo, timeCompo])`:
   the arguments present select the values (no `islocal`; `globalNode`
   is a local node number):
   - node, space, time: one value, `tsize = 1`;
   - node: all values of the node in the order `(s, t) = (1, 1), (2, 1),
     (1, 2), (2, 2)`, `tsize = spaceCompo * timeCompo`;
   - node, space: the time components, `tsize = timeCompo`;
   - node, time: the space components, `tsize = spaceCompo`;
   - space, time: all nodes, `tsize = tNodes`;
   - space: all time components of `s`, time 1 first,
     `tsize = tNodes * timeCompo`;
   - time: all space components of `t`, space 1 first,
     `tsize = tNodes * spaceCompo`.
3. **Other forms** (all pass `islocal`):
   - Get5 `Get(VALUE, globalNode, islocal, spaceCompo, timeCompo)`: one
     value (`GetSingle`).
   - Get6 `Get(VALUE(:, :), nrow, ncol, globalNode, islocal)`: one node,
     `VALUE(s, t)`, `nrow = spaceCompo`, `ncol = timeCompo`.
   - Get4 `Get(VALUE(:), tsize, globalNode(:), islocal, spaceCompo,
     timeCompo)`: one component of the selected nodes,
     `tsize = SIZE(globalNode)`.
   - Get2 `Get(VALUE(:, :, :), storageFMT, dim1, dim2, dim3)`: all values.
     `NODES_FMT`: `VALUE(s, t, i)`, dims `(spaceCompo, timeCompo,
     tNodes)`; `DOF_FMT`: `VALUE(i, s, t)`, dims `(tNodes, spaceCompo,
     timeCompo)`.
   - Get3 `Get(VALUE(:, :, :), storageFMT, globalNode(:), islocal, dim1,
     dim2, dim3)`: the same for the selected nodes.
   - Get7 `Get(VALUE=fevar, globalNode(:), islocal)` and
     `GetFEVariable(globalNode, islocal, VALUE, [ivar])`: nodal, vector,
     space-time `FEVariable_`, shape `(spaceCompo, SIZE(globalNode),
     timeCompo)`. `VALUE` is assigned, so it need not be initiated.
4. **Into a vector field.** `u%SetToVectorField(VALUE=w, timeCompo,
   [scale, addContribution])` writes time component `timeCompo` of `u`
   into the `VectorField_` `w` (`w%spaceCompo = u%spaceCompo`, same
   FEDOF). `u` and `w` may use any engine.
5. **By index** (`AbstractNodeField_`): `GetSingle(indx, VALUE)`,
   `GetMultiple(indx(:), VALUE, tsize)`, `GetMultiple(istart, iend,
   stride, VALUE, tsize)`, with a range of `VALUE`, and GetMultiple4
   (`VALUE(range) = [VALUE(range) +] scale * obj(range)`). See
   [ScalarField: Setting and Getting values](scalarfield-set-get.md).

Trimmed from `Get_test_1`, `Set_test_1`, `Set_test_3` and `Set_test_4`
of `STVectorField` (all use `STVectorField_test.toml`;
`f(s, t, i) = 100 s + 10 t + i`):

```fortran
USE BaseType, ONLY: FEVariable_
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

CHARACTER(*), PARAMETER :: tomlFileName = "STVectorField_test.toml"
REAL(DFP), PARAMETER :: tol = 1.0E-12_DFP
TYPE(FEDomain_) :: dom
TYPE(FEDOF_), TARGET :: fedof, geofedof
TYPE(TimeFEDOF_), TARGET :: timefedof
TYPE(STVectorField_) :: u
TYPE(FEVariable_) :: fevar
REAL(DFP) :: found(24), val, mat(2, 2), g3(2, 2, 6), found3(6, 2, 2), &
             w3(2, 2, 3)
INTEGER(I4B) :: tsize, ii, s, t, nrow, ncol, dim1, dim2, dim3

CALL e%SetQuietMode(math%yes)
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")
CALL u%ImportFromToml(tomlName="u", filename=tomlFileName, &
                      fedof=fedof, geofedof=geofedof, &
                      timefedof=timefedof, dom=dom)
DO t = 1, 2
  DO s = 1, 2
    CALL u%Set(VALUE=[(f(s, t, ii), ii=1, 6)], spaceCompo=s, timeCompo=t)
  END DO
END DO

! Get1: node; node and space; space and time; time
CALL u%Get(VALUE=found, tsize=tsize, globalNode=3)
CALL OK(tsize .EQ. 4, "node: tsize")
CALL u%Get(VALUE=found, tsize=tsize, globalNode=3, spaceCompo=2)
CALL OK(ALL(ABS(found(1:2) - [f(2, 1, 3), f(2, 2, 3)]) .LT. tol), &
        "node, space: values")
CALL u%Get(VALUE=found, tsize=tsize, spaceCompo=1, timeCompo=2)
CALL OK(tsize .EQ. 6, "space, time: tsize")
CALL u%Get(VALUE=found, tsize=tsize, timeCompo=2)
CALL OK(tsize .EQ. 12, "time: tsize")

! Get5 (one value), Get6 (one node), Get4 (one component, some nodes)
CALL u%Get(VALUE=val, globalNode=3, islocal=math%yes, spaceCompo=2, &
           timeCompo=1)
CALL u%Get(VALUE=mat, nrow=nrow, ncol=ncol, globalNode=2, &
           islocal=math%yes)
CALL u%Get(VALUE=found, tsize=tsize, globalNode=[3, 5], &
           islocal=math%yes, spaceCompo=2, timeCompo=2)

! Get2 (all), Get3 (selected nodes)
CALL u%Get(VALUE=g3, storageFMT=NODES_FMT, dim1=dim1, dim2=dim2, &
           dim3=dim3)
CALL OK(dim1 .EQ. 2 .AND. dim2 .EQ. 2 .AND. dim3 .EQ. 6, &
        "Get all, NODES: dims")
CALL u%Get(VALUE=found3, storageFMT=DOF_FMT, dim1=dim1, dim2=dim2, &
           dim3=dim3)
CALL OK(dim1 .EQ. 6 .AND. dim2 .EQ. 2 .AND. dim3 .EQ. 2, &
        "Get all, DOF: dims")
CALL u%Get(VALUE=w3, storageFMT=NODES_FMT, globalNode=[6, 4, 1], &
           islocal=math%yes, dim1=dim1, dim2=dim2, dim3=dim3)

! Get7: nodal space-time FEVariable of nodes 1, 5, 2
CALL u%Get(VALUE=fevar, globalNode=[1, 5, 2], islocal=math%yes)

CALL u%DEALLOCATE()
CALL timefedof%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL dom%DEALLOCATE()

CONTAINS

PURE FUNCTION f(sc, tc, nd) RESULT(ans)
  INTEGER(I4B), INTENT(IN) :: sc, tc, nd
  REAL(DFP) :: ans
  ans = 100.0_DFP * sc + 10.0_DFP * tc + nd
END FUNCTION f
```

## Example files (run from the `examples` directory)

- `classes:src/modules/STVectorField/examples/Get_test_1.F90` (all Get1
  cases)
- `classes:src/modules/STVectorField/examples/Set_test_1.F90` (Get5,
  Get6)
- `classes:src/modules/STVectorField/examples/Set_test_3.F90` (Get2,
  Get3, Get4)
- `classes:src/modules/STVectorField/examples/Set_test_4.F90` (Get7,
  `GetFEVariable`)
- `classes:src/modules/STVectorField/examples/SetFromVectorField_test_1.F90`
  (`SetToVectorField`)
- `classes:src/modules/STVectorField/examples/STVectorField_test.toml`
- `classes:src/modules/STVectorFieldLis/examples/Set_test_1.F90` (Get on
  a LIS field)
- `classes:src/modules/STVectorFieldLis/examples/Set_test_2.F90`
  (`SetToVectorField` from a LIS field into native and LIS vector
  fields)
- `classes:src/modules/STVectorFieldLis/examples/SetMultiple_test_1.F90`
  (`GetSingle`, `GetMultiple` on LIS)

## Pitfalls

- Pass `islocal=math%yes` and local node numbers. `islocal` is not used
  by any Get (no `localNodeError` check: the include
  `classes:src/submodules/STVectorField/src/localNodeError.F90` is
  empty), so a global number is read as a local one.
- No size checks, even in debug builds: `VALUE` must have room for
  `tsize` (or `nrow x ncol`, `dim1 x dim2 x dim3`) entries; it is not
  reallocated.
- Get1 with none of `globalNode`, `spaceCompo`, `timeCompo` raises an
  error only in a debug build; in release `tsize` is not set.
- Get1 for one node uses a fixed buffer of 128 indices:
  `spaceCompo * timeCompo` must not exceed 128 (not checked).
- The Get7 `FEVariable_` is `(spaceCompo, nodes, timeCompo)`; the rank 3
  arrays of Get2/Get3 (`NODES_FMT`) are `(spaceCompo, timeCompo,
  nodes)`. Set10 swaps back, so `Set(VALUE=fevar, ...)` takes a Get7
  result unchanged (`Set_test_4`).
- LIS: all Get forms reach the LIS vector through the overridden
  `GetSingle`/`GetMultiple`. `GetPointer` of a `STVectorFieldLis_`
  returns `NULL()` (error in debug builds); `realVec` is filled only by
  `Display` and `Export`.
