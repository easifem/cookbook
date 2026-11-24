!> author: Vikas Sharma, Ph. D.
! date: 2026-11-20
! summary: Day-02: of DGM
!
! Day-01: Create mesh in mesh
!
! Day-02: of DGM
!
! [x] Read mesh
! [x] Create scalar field
! [ ] Create diffusion matrix
!
!
! USE BaseType, ONLY: math => TypeMathOpt
! !! TypeMathOpt is in BaseType, but we renamed as math
! USE ExceptionHandler_Class, ONLY: e
! !! e is just for checking error, nothing to do with
! !! calculation
! USE FEDOF_Class, ONLY: FEDOF_
! !! FEDOF is a class for finite element degrees of freedom.
! !! This is a very important concept in FEM
! USE FEDomain_Class, ONLY: FEDomain_
! !! FEDomain contains information of mesh and domain.
! !! What is the different between a mesh and a domain.
! !! Simple answer: Domain contains mesh of 1D, 2D, 3D objects.
! USE GlobalData, ONLY: I4B
! !! I4B is 4 byte integer.
! USE GlobalData, ONLY: LGT
! USE ScalarField_Class, ONLY: ScalarField_
! !! ScalarField is field of scalar variable. it contains
! !! unknowns of scalar field on mesh or domain.
! USE AbstractMesh_Class, ONLY: AbstractMesh_
! USE Display_Method, ONLY: Display
! ! USE Display_Method, ONLY: BlankLines
! USE Display_Method, ONLY: ToString

PROGRAM main
USE AbstractFE_Class, ONLY: AbstractFE_
USE AbstractMesh_Class, ONLY: AbstractMesh_
USE BaseType, ONLY: math => TypeMathOpt
USE BaseType, ONLY: ElemShapeData_
USE BaseType, ONLY: QuadraturePoint_
USE DiffusionMatrix_Method, ONLY: DiffusionMatrix_
USE DiffusionMatrix_Method, ONLY: DiffusionMatrix_
USE Display_Method, ONLY: Display
USE Display_Method, ONLY: ToString
USE Display_Method, ONLY: BlankLines
USE ElemShapeData_Method, ONLY: ElemShapeDataDisplay => Display
USE ExceptionHandler_Class, ONLY: e
USE FEDOF_Class, ONLY: FEDOF_
USE FEDomain_Class, ONLY: FEDomain_
USE GlobalData, ONLY: I4B
USE GlobalData, ONLY: LGT
USE GlobalData, ONLY: DFP
USE QuadraturePoint_Method, ONLY: QuadraturePointDisplay => Display
USE QuadraturePoint_Method, ONLY: QuadraturePoint
USE ReallocateUtility, ONLY: Reallocate
USE ScalarField_Class, ONLY: ScalarField_
IMPLICIT NONE

CHARACTER(*), PARAMETER :: tomlFileName = "config.toml"
!! This is a TOML file, please read on internet about toml file.
TYPE(FEDomain_) :: dom
!! dom is a variable of type FEDomain. our domain will be inside dom.
!! domain has mesh of cell, line, and points.
!! mesh of points is useless.
CLASS(AbstractMesh_), POINTER :: cellMesh, boundaryMesh
!! mesh pointer
CLASS(AbstractFE_), POINTER :: feptr, geofeptr
!! AbstractFE
TYPE(FEDOF_), TARGET :: fedof, geofedof
!! fedof and geofedof are finite element degrees of freedom for solution and
!! geometry.
TYPE(ScalarField_) :: sol, rhs, u0
!! sol is solution of the problem
!! rhs is the right hand side of Ax=b,
!! u0 is same as sol
INTEGER(I4B) :: nsd, iel, xij_nrow, xij_ncol, maxGeoCon, maxFeCon, &
                elemDiffMat_nrow, elemDiffMat_ncol
!! number of spatial dimension, 1D, 2D, 3D
LOGICAL(LGT) :: isok
TYPE(ElemShapeData_) :: elemsd, geoelemsd
TYPE(QuadraturePoint_) :: quad
REAL(DFP), ALLOCATABLE :: xij(:, :), elemDiffMat(:, :)

!! Do you want so much message from the library
CALL e%SetQuietMode(math%yes)

!! Import domain from mesh file in hdf5 format.
CALL dom%ImportFromToml(filename=tomlFileName, tomlName="domain")

!! Display information
! CALL BlankLines()
! CALL dom%DisplayDomainInfo(msg="domain: ")
! CALL dom%Display(msg="domain: ")

!! Get number of spatial dimension
nsd = dom%GetNSD()

!! get pointer to mesh of cells
cellMesh => dom%GetMeshPointer(dim=nsd)
! CALL BlankLines(nol=2)
! CALL cellMesh%DisplayMeshInfo(msg="cellMesh: ")
! CALL cellMesh%Display(msg="cellMesh: ")

!! get pointer to mesh of boundary
boundaryMesh => dom%GetMeshPointer(dim=nsd - 1)
! CALL BlankLines(nol=2)
! CALL boundaryMesh%DisplayMeshInfo(msg="boundaryMesh: ")
! CALL cellMesh%Display(msg="cellMesh: ")

! Let us initiate sol
! CALL BlankLines()
! CALL Display(fedof%IsInitiated(), "fedof IsInitiated before: ")
! CALL Display(geofedof%IsInitiated(), "geofedof IsInitiated before: ")
! CALL Display(sol%IsInitiated(), "sol IsInitiated before: ")
! CALL BlankLines()

CALL sol%ImportFromToml(fedof=fedof, geofedof=geofedof, dom=dom, &
                        filename=tomlFileName, tomlName="sol")

! CALL BlankLines()
! CALL Display(fedof%IsInitiated(), "fedof IsInitiated after: ")
! CALL Display(geofedof%IsInitiated(), "geofedof IsInitiated after: ")
! CALL Display(sol%IsInitiated(), "sol IsInitiated after: ")
! CALL BlankLines()

! Let us initiate rhs by copying from sol
CALL rhs%Initiate(sol)
CALL rhs%SetName("rhs")

! Let us initiate u0 by copying from sol
CALL u0%Initiate(sol)
CALL u0%SetName("u0")

! let us display
! CALL BlankLines()
! CALL sol%Display("sol: ")

! Some important functions
CALL Display(sol%SIZE(), "size of sol: ")

! Create diffusion matrix
maxGeoCon = geofedof%GetMaxTotalConnectivity()
maxFeCon = fedof%GetMaxTotalConnectivity()
CALL Reallocate(xij, 3, maxGeoCon)
CALL Reallocate(elemDiffMat, maxFeCon, maxFeCon)

DO iel = 1, cellMesh%GetTotalElements()
  CALL Display("iel  = "//ToString(iel))
  CALL Display(cellMesh%GetGlobalElemNumber(iel), "globalElemNumber:")

  isok = cellMesh%IsElementActive(globalElement=iel, islocal=math%yes)
  CALL Display(isok, "isActive: ")

  ! Set the finite element of local element iel for sol
  CALL fedof%SetFE(globalElement=iel, islocal=math%yes)
  feptr => fedof%GetFEPointer(globalElement=iel, islocal=math%yes)
  ! CALL feptr%Display("feptr for iel = "//ToString(iel), 10)

  ! Set the finite element of local element iel for geometry
  CALL geofedof%SetFE(globalElement=iel, islocal=math%yes)
  geofeptr => geofedof%GetFEPointer(globalElement=iel, islocal=math%yes)
  ! CALL geofeptr%Display("geofeptr for iel = "//ToString(iel), 10)

  ! Let us start from here on Day 03
  ! Let us get nodal coordinates of element
  CALL cellMesh%GetNodeCoord(nodeCoord=xij, globalElement=iel, &
                             islocal=math%yes, &
                             nrow=xij_nrow, ncol=xij_ncol)

  CALL feptr%GetGlobalElemShapeData2(geofeptr=geofeptr, elemsd=elemsd, &
                                     geoelemsd=geoelemsd, &
                                     xij=xij, quad=quad)

  CALL DiffusionMatrix_(test=elemsd, trial=elemsd, ans=elemDiffMat, &
                        nrow=elemDiffMat_nrow, ncol=elemDiffMat_ncol)

  ! CALL BlankLines(10)
  ! CALL Display(elemDiffMat(1:elemDiffMat_nrow, &
  !                          1:elemDiffMat_ncol), "elemDiffMat: ")
  ! CALL BlankLines(10)
  ! CALL Display(xij(1:xij_nrow, 1:xij_ncol), "xij: ", 10)
  ! CALL BlankLines(10)
  ! CALL QuadraturePointDisplay(quad, "quad: ", 10)
  ! CALL BlankLines(10)
  ! CALL ElemShapeDataDisplay(elemsd, "elemsd: ", 10)
  ! CALL BlankLines(10)
  ! CALL ElemShapeDataDisplay(geoelemsd, "geoelemsd: ", 10)
  ! CALL BlankLines(10)
  ! STOP

END DO

CALL dom%DEALLOCATE()
CALL fedof%DEALLOCATE()
CALL geofedof%DEALLOCATE()
CALL sol%DEALLOCATE()
CALL rhs%DEALLOCATE()
CALL u0%DEALLOCATE()
END PROGRAM main
