PROGRAM main
USE BaseType, ONLY: math => TypeMathOpt
USE Display_Method, ONLY: Display
USE Display_Method, ONLY: BlankLines
USE GlobalData, ONLY: DFP
USE GlobalData, ONLY: I4B
USE GlobalData, ONLY: LGT
USE ReallocateUtility, ONLY: Reallocate
IMPLICIT NONE

REAL(DFP), ALLOCATABLE :: avec(:)
!! variable, real, dynamic, array of rank 1 (vector)
REAL(DFP), ALLOCATABLE :: mat2(:, :)
!! variable, real, dynamic, array of rank 2 (matrix)
REAL(DFP), ALLOCATABLE :: mat3(:, :, :)
!! variable, real, dynamic, array of rank 3
REAL(DFP), ALLOCATABLE :: math4(:, :, :, :)
!! variable, real, dynamic, array of rank 4
INTEGER(I4B), ALLOCATABLE :: nodeNumber(:)
!! this integer dynamic array of rank 1 (vector)
LOGICAL(LGT) :: isok
!! Logical

!! So far the memory for avec, mat2, mat3, mat4, nodeNumber is
!! not allocated.
!!
!! If you try to read or write in these variable
!! before allocating memory, you will get segmentation
!! fault: Most popular error in C and Fortran, and C++:

ALLOCATE (avec(2))
! Set first component
avec(1) = math%one
! Crime
! Set third component
! avec(3) = math%one

! Crime, why?
! ALLOCATE (avec(3))
! avec(3) = math%one
!
! Ans, deallocate before allocating.
!
! 1. How to check if allocated.
! 2. if allocated we deallocate.
! 3. After deallocating we can allocate
!
!
! 1. Check if allocated
isok = ALLOCATED(avec)

! 2. if allocated deallocate
! IF (isok) DEALLOCATE (avec)
IF (isok) THEN
  DEALLOCATE (avec)
END IF

! now we can allocate
ALLOCATE (avec(3))
avec(3) = math%one

! But easifem can take care of this.
! Just use Reallocate() method
! defined inside ReallocateUtility

CALL Reallocate(avec, 5)
avec = 5.0
CALL Display(avec, "avec: ")

CALL Reallocate(mat2, 2, 3)
!! Reallocate is from easifem
CALL RANDOM_NUMBER(mat2)
!! RANDOM_NUMBER is from fortran

CALL Display(mat2, "mat2: ")

CALL BlankLines()
CALL Reallocate(mat2, 0, 0)
CALL Display(mat2, "zero size mat2: ")

CALL BlankLines()
CALL Reallocate(mat3, 2, 3, 2)
CALL RANDOM_NUMBER(mat3)
CALL Display(mat3, "mat3: ")

END PROGRAM main
