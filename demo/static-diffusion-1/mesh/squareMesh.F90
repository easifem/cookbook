! In fortran we have following native TYPES:
!
! 1. CHARACTER
! 2. INTEGER
! 3. REAL
! 4. LOGICAL, boolean
!
! Every other type is defined in EASIFEM.
!
PROGRAM main
USE Display_Method, ONLY: Display
!! Import Display method, which is write or print method in easifem, from Display module:
!! You can call Display method for anything, almost...
USE Display_Method, ONLY: ToString
!! ToString can convert anything into string
!! 1 --> "1"
!! 1.0 => "1.0"
USE GlobalData, ONLY: DFP
!! DFP is defaupt floating point, which is usually Real64
USE GlobalData, ONLY: I4B
!! I4B, 4 byte integer
USE GlobalData, ONLY: LGT
!! LGT: just kind for boolean, i do not know why I called it LGT
USE Gmsh_Class, ONLY: Gmsh_
!! Import Gmsh_ class from Gmsh_Class module:
!! Gmsh_ will be used to make mesh.
USE HDF5File_Class, ONLY: HDF5File_
!! Import HDF5File_ class from module,
!! HDF5File_ definers HDF5 file, please read about this file
!! on internet by yourself. this file type is super cool and
!! fast for scientific computing.
USE MSHFile_Class, ONLY: MSHFile_
!! MSHFile_ is the mesh file used by Gmsh, this format
!! is defined by Gmsh. Easifem read the gmsh mesh file
!! and store data inside MSHFile_.
!! User should not worry about this file. This
!! is just between Gmsh and easifem.
USE BaseType, ONLY: math => TypeMathOpt
!! This is importing something from module and renaming it.
!! So TypeMathOpt is defined in BaseType. We import it, and
!! rename it to math. math is easy to type.
!! We can get things defined in math (TypeMathOpt) by using
!! % symbol
IMPLICIT NONE

TYPE(Gmsh_) :: gmsh
!! Gmsh_ is the class also known as type.
!! and gmsh is the instance of Gmsh_ class.
!!   in simple words gmsh is variable of Gmsh_ type.
!!   In easifem all user types ends with underscore in eaisfem
CHARACTER(LEN=*), PARAMETER :: prefix = "square"
!! This is how we define string parameter in Fortran.
!!               This is not easifem feature.
!! A parameter in fortran is a constant, you cannot change
!! its value.
REAL(DFP), PARAMETER :: lx = 1.0_DFP
!! This is how we define real parameter. This is REAL number.
REAL(DFP), PARAMETER :: ly = 1.0_DFP
!! This is also fixed REAL number
INTEGER(I4B), PARAMETER :: order = math%one_i
!! This is fixed integer number.
!! order is order of mesh, this has nothing to do with solution
!! order. If you are dealing with curved geometry, may be you want
!! to use order=2. order=1 generate elements with straight edges.
!! Please think this as approximation for geometry:
REAL(DFP), PARAMETER :: meshSize = math%one
!! meshSize is size of mesh
REAL(DFP), PARAMETER :: corner(3) = math%zero
!! One corner of square domain, corner(3), means vector of
!! real number, and the size of this vector is 3.
!! So corder(3) has three components, (x,y,z).
!! Also, corner is parameter (constant)
!! meaning we cannot change this vector.
!! Also, corner=0.0 means all the components are set to zero.
INTEGER(I4B), PARAMETER :: nnod(2) = [4, 4]
!! integer, constant, vector of size 2.
!! In this case let see the meaning of [4, 4].
!! So, [ ] this is called array constructor in Fortran.
!! In older days, when out father used to be young, this
!! array constructor is given by \( \)
!! In older days, when out father used to be young, this
!! array constructor is given by \( \).
!! Do not use this array constructor for big arrays.
INTEGER(I4B) :: ierr
!! Finally, this is an integer variable,
!! we call this SCALAR integer variable.
REAL(DFP) :: x, y, z, lc
!! These are four SCALAR real variables
CHARACTER(:), ALLOCATABLE :: suffix, title
!! This dynamic rank 1 character array (basically vector of char)
!! In computer science this is often called string.
TYPE(MSHFile_) :: mshFile
!! Gmsh mesh file
TYPE(HDF5File_) :: hdf5file
!! HDF5 file:

!! What is happening here:
!! "hello " // "world" ==> "hello world"
suffix = ToString(nnod(1))//"x"//ToString(nnod(2))

!! preparing title of mesh file:
title = prefix//"_"//suffix

! Read about gmsh on internet.
! Start gmsh
ierr = gmsh%Initialize()

! add model by giving its name
ierr = gmsh%model%add(title)

! First we will make geometry
! Then we will generate mesh in that geometry.
x = corner(1)
y = corner(2)
z = corner(3)
lc = meshSize
ierr = gmsh%model%geo%addPoint(x=x, y=y, z=z, meshSize=lc, tag=1)

x = x + lx
y = y
z = z
lc = lc
ierr = gmsh%model%geo%addPoint(x=x, y=y, z=z, meshSize=lc, tag=2)

x = x
y = y + ly
z = z
lc = lc
ierr = gmsh%model%geo%addPoint(x=x, y=y, z=z, meshSize=lc, tag=3)

x = corner(1)
y = y
z = z
lc = lc
ierr = gmsh%model%geo%addPoint(x=x, y=y, z=z, meshSize=lc, tag=4)

! line 1 to 4
ierr = gmsh%model%geo%addLine(1, 2, 1)
ierr = gmsh%model%geo%addLine(2, 3, 2)
ierr = gmsh%model%geo%addLine(3, 4, 3)
ierr = gmsh%model%geo%addLine(4, 1, 4)

! add line loop
ierr = gmsh%model%geo%addCurveLoop([1, 2, 3, 4], tag=1)

! plane surface
ierr = gmsh%model%geo%addPlaneSurface([1], 1)

! This part you can ignore
! This is related to creating nice square mesh:
! Horizontal line, bottom
ierr = gmsh%model%geo%mesh%setTransfiniteCurve(1, nnod(1), &
                                               "Progression", 1.0_DFP)
! Horizontal line, top
ierr = gmsh%model%geo%mesh%setTransfiniteCurve(3, nnod(1), &
                                               "Progression", 1.0_DFP)
! Vertical, right
ierr = gmsh%model%geo%mesh%setTransfiniteCurve(2, nnod(2), &
                                               "Progression", 1.0_DFP)
! Vertical, left
ierr = gmsh%model%geo%mesh%setTransfiniteCurve(4, nnod(2), &
                                               "Progression", 1.0_DFP)

! The following sentense says that surface mesh is generate
! by transfinite lines that we have created above.
! May be you should read about transfinite meshes,
! they are supercool in computer graphics.
ierr = gmsh%model%geo%mesh%setTransfiniteSurface(1)

! Let us combine triangles into square.
! The line below will combine two triangles to make a square:
! Gmsh cannot generate square mesh directly.
! It always create triangles and then combine them to
! make quadrangle.
ierr = gmsh%model%geo%mesh%setRecombine(2, 1)

!
! At this point we are done, we have nothing to change or specify
! about the mesh. So we will ask gmsh to synch its model.
! This step is necessary before we ask gmsh to generate mesh.
ierr = gmsh%model%geo%synchronize()

! Now it safe to ask gmsh to generate mesh.
ierr = gmsh%model%mesh%generate(2)

! If you want higher order mesh. we can set the order.
! But please ignore this, just setOrder to 1:
ierr = gmsh%model%mesh%setOrder(order)

! Let us write data into mesh file.
ierr = gmsh%WRITE(title//'.msh')

! Stop gmsh
ierr = gmsh%Finalize()

! Now we have gmsh file on our system.
! We will read that file and store in
! hdf5file system.
! This because, easifem depends on hdf5file system.
! So we can create mesh from different software,
! read the file and convert it into hdf5file format.
! Basically eaisfem does not care which mesh generator is
! used. it only cares about hdf5file format, which specific to
! easifem.
! Please read fortran Open statement.
! Please read how to open a file in fortran.
CALL mshFile%Initiate(filename=title//'.msh', STATUS="OLD", ACTION="READ")
CALL mshFile%OPEN()
CALL mshFile%READ()
CALL hdf5file%Initiate(title//'.h5', MODE="NEW")
CALL hdf5file%OPEN()
CALL mshFile%Export(hdf5=hdf5file, group="")

! cleanup
CALL mshFile%DEALLOCATE()
CALL hdf5file%DEALLOCATE()
END PROGRAM main
