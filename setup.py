# For development work, execute this via:
# $ python3 setup.py develop
#
# To generate source distribution
# $ python3 setup.py sdist
#
# To generate pre-compiled binary wheel
# $ python3 setup.py bdist_wheel

# Alternate binary builds:
#   macOS: build "normally", with shared libs for fftw3, gsl, nlopt;
#       then use delocate-wheel to copy shared libs into wheel
#   Linux: build on user's machine using static libs for fftw3, gsl, nlopt
#
# To restart process from scratch (compile libimfit.a, then run Cython, then
# compile binary library:
# $ python setup.py

import os
import sys
import tempfile
import subprocess
import shutil
import re, io
import numpy as np
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
from setuptools import Command

try:
    from Cython.Build import cythonize
    CYTHON_PRESENT = True
except ImportError:
    CYTHON_PRESENT = False


if not sys.version_info[0] >= 3:
    sys.exit("setup.py: Python 3 required for pyimfit!")

baseDir = os.getcwd() + "/"
if sys.platform == 'darwin':
    MACOS_COMPILATION = True
    PREBUILT_PATH = baseDir + "prebuilt/macos/"
else:
    MACOS_COMPILATION = False
    PREBUILT_PATH = baseDir + "prebuilt/linux64/"
    EXTRA_PATH = baseDir + "extra_libs/"
    EXTRA_LIBS_PATH = EXTRA_PATH + "lib_linux64/"


# Stuff related to making sure which compiler we're using, and if it's
# capable of doing what we want:
#   1. Compiler must support OpenMP
#   2. If compiler is GCC, it must be version 5 or newer
if MACOS_COMPILATION:
    DEFAULT_CPP = "clang++"
else:
    DEFAULT_CPP = "g++"

# We assume that *if* CXX is defined, then both it and CC are pointing
# to the user-defined C++ compiler, which is what we should use.
# Note that we need CC to point to the *same* OpenMP-compatible C++ compiler,
# otherwise the standard setuptools extension-building code will try to
# compile pyimfit_lib.cpp with "g++"
try:
    compilerName = os.environ["CXX"]
except KeyError:
    # This should be OK for Linux (but probably not for macOS)
    os.environ["CXX"] = DEFAULT_CPP
    os.environ["CC"] = DEFAULT_CPP
    compilerName = DEFAULT_CPP


# Code to make sure the C++ compiler can handle OpenMP
OPENMP_TEST_CODE = \
r"""
#include <omp.h>
#include <stdio.h>
int main() {
#pragma omp parallel
printf("Hello from thread %d, nthreads %d\n", omp_get_thread_num(), omp_get_num_threads());
}
"""

def check_for_openmp(compilerName=compilerName):
    """Returns True if C++ compiler specified by compilerName can handle OpenMP,
    False if not.
    """
    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    filename = 'test.cpp'
    with open(filename, 'w') as file:
        file.write(OPENMP_TEST_CODE)
    with open(os.devnull, 'w') as fnull:
        if MACOS_COMPILATION and (compilerName == "clang++"):
            args = [compilerName, '-Xpreprocessor', '-fopenmp', '-lomp', filename]
        else:
            args = [compilerName, '-fopenmp', filename]
        result = subprocess.call(args, stdout=fnull, stderr=fnull)
    os.chdir(curdir)
    #clean up
    shutil.rmtree(tmpdir)
    return (result == 0)

NON_OPENMP_MESSAGE = """setup.py: ERROR: The C++ compiler does not appear to be OpenMP compatible!"
   Try defining the environment variables CC *and* CXX with the name of a C++ compiler
   which *does* handle OpenMP. E.g.,
      $ CC=<c++-compiler-command> CXX=<c++-compiler-command> python setup.py ...
"""

# The following currently only works for gcc. We assume the output of
# "<compilerName> --version" looks something like
#    gcc-8 (Homebrew GCC 8.3.0) 8.3.0
#    gcc (Ubuntu 5.4.0-6ubuntu1~16.04.11) 5.4.0
# This should return True if GCC version is 5.0.0 or higher
findVersion = re.compile(r"^gcc[^(]*\([^)]*\)\s*(?P<vnum>\d+\.\d+\.\d+)")
def check_gcc_version( compilerName="gcc", getVersionNum=False ):
    try:
        output = subprocess.check_output([compilerName, '--version'])
    except FileNotFoundError as err:
        print(err)
        return False
    output = output.decode()
    versionNumString = findVersion.match(output).group("vnum")
    if getVersionNum:
        return versionNumString
    if versionNumString is not None:
        return versionNumString >= "5.0.0"
    else:
        return False

BAD_GCC_VERSION_MESSAGE = """setup.py: ERROR: GCC version 5.0 or later required!
(Detected version: {0})
"""




NAME = "pyimfit"           # Name for whole project and for "distribution package"
                           # = how it will be listed on PyPI
SRC_DIR = "pyimfit"        # This will be package ("import package") name (e.g., >>> import pyimfit)
IMFIT_SOURCE_DIR = "imfit"
PACKAGES = [SRC_DIR]


# Stuff for finding imfit headers and static library
IMFIT_HEADER_PATH = "imfit"
IMFIT_LIBRARY_PATH = baseDir + "libimfit/"

libPath = [IMFIT_LIBRARY_PATH]
#headerPath = [IMFIT_HEADER_PATH, IMFIT_HEADER_PATH+"/function_objects", IMFIT_HEADER_PATH+"/core",
#              ".", np.get_include()]
headerPath = [IMFIT_LIBRARY_PATH + "include", ".", np.get_include()]
if not MACOS_COMPILATION:
    headerPath.append(EXTRA_PATH + "include")
    libPath.append(EXTRA_LIBS_PATH)
# Note two versions of NLopt library ("nlopt_cxx" is for case of version with extra C++
# interfaces (e.g., CentOS package)
libraryList = ["imfit", "gsl", "gslcblas", "nlopt", "fftw3", "fftw3_threads"]
if MACOS_COMPILATION and (compilerName == "clang++"):
	libraryList.append("omp")

# note that to link the libimfit.a library, we have to
#    A. Refer to it using the usual truncated form ("imfit" for filename "libimfit.a")
#    B. Provide a path to the library file via the library_dirs keyword of the Extension
#       class


# Special code to ensure we compile libimfit.a using SCons *before* attempting to do any
# other builds
SCONS_CMD = "scons {0} libimfit.a"
SCONS_CLANG_CMD = "scons --clang-openmp libimfit.a"
SCONS_ERR = "*** Unable to build initial static library (libimfit.a)!\nTerminating build...."
EXTRA_SCONS_FLAGS = "--cpp={0}".format(compilerName)

def build_library_with_scons( extraFlags=EXTRA_SCONS_FLAGS ):
    """Simple command to call SCons in order to build libimfit.a in the Imfit
    source directory.
    """
    print("\n** Building static Imfit library (libimfit.a) with SCons ...")
    cwd = os.getcwd()
    os.chdir(IMFIT_SOURCE_DIR)
    # Insert check for existing libraries (fftw3, GSL, etc.) here?
    if MACOS_COMPILATION and (compilerName == "clang++"):
        sconsCommand = SCONS_CLANG_CMD
    else:
        sconsCommand = SCONS_CMD.format(extraFlags)
    out = subprocess.run(sconsCommand, shell=True, stdout=subprocess.PIPE)
    txt = out.stdout.decode()
    print(txt)
    os.chdir(cwd)
    if out.returncode != 0:
        return False
    else:
        shutil.copy(IMFIT_SOURCE_DIR + "/" + "libimfit.a", IMFIT_LIBRARY_PATH + "libimfit.a")
        return True

class my_build_ext( build_ext ):
    """Subclass of build_ext which ensures that libimfit.a exists prior to trying build
    any of the Python extensions. If a prebuilt version *is* found, it is copied to
    IMFIT_LIBRARY_PATH; if no prebuilt version is found, then build_library_with_scons
    is called (which will, after building the library, copy it to IMFIT_LIBRARY_PATH)."""
    def run(self):
        # Check to see if we have usable compilers (also good for compiling previously
        # generated Cython C++ files):
        if not check_for_openmp():
            sys.exit(NON_OPENMP_MESSAGE)
        if (not MACOS_COMPILATION) and (not check_gcc_version()):
            gccVersionNum = check_gcc_version(getVersion=True)
            sys.exit(BAD_GCC_VERSION_MESSAGE.format(gccVersionNum))
        
        # Check to see if libimfit.a already exists
        if not os.path.exists(PREBUILT_PATH + "libimfit.a"):
            # first, build the static C++ library with SCons and copy it to IMFIT_LIBRARY_PATH
            success = build_library_with_scons()
            if not success:
                print(SCONS_ERR)
                sys.exit(1)
        else:
            shutil.copy(PREBUILT_PATH + "libimfit.a", IMFIT_LIBRARY_PATH + "libimfit.a")

        # now call the parent class's run() method, which will use *this* instance's list of
        # extensions (e.g., the cythonized extensions) and do standard build_ext things with them.
        super().run()




# http://docs.cython.org/en/latest/src/userguide/source_files_and_compilation.html#distributing-cython-modules
ext = '.pyx' if CYTHON_PRESENT else '.cpp'

# Defining one or more "extensions modules" (single-file C/C++-based modules, usually
# with a .so file suffix. This includes Cython-based modules, since those are
# are translated to C/C++ before being compiled.)
if MACOS_COMPILATION and compilerName == "clang++":
    # the first pair is magic stuff to get Apple's clang++ to work with OpenMP;
    # the second turns off linker warnings (to avoid getting pages of
    # "could not create compact unwind" and other unhelpful warnings)
    extraCompileArgs = ["-Xpreprocessor", "-fopenmp", '-std=c++11']
    extraLinkerArgs = ["-Xpreprocessor", "-fopenmp", "-Xlinker", "-w"]
else:
    extraCompileArgs = ["-fopenmp", '-std=c++11']
    extraLinkerArgs = ["-fopenmp"]
extensions = [
    # specify how to create the Cython-based extension module pyimfit_lib.so
    Extension(SRC_DIR + ".pyimfit_lib",     # [= pyimfit.pyimfit_lib] = base name for .so file
                                            # (e.g., pyimfit_lib.cpython-37m-darwin.so)
                [SRC_DIR + "/pyimfit_lib" + ext],       # source code files
                libraries=libraryList,
                include_dirs=headerPath,
                library_dirs=libPath,
                extra_compile_args=extraCompileArgs,
                extra_link_args=extraLinkerArgs,
                #define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
                language="c++")
]

if CYTHON_PRESENT:
    # the include_path specification is necessary for Cython to find the *.pxd files
    # which are included via "cimport" in the *.pyx files
    extensions = cythonize(extensions, include_path=["pyimfit"])



# Modified cleanup command to remove build subdirectory
# Based on: https://stackoverflow.com/questions/1710839/custom-distutils-commands
class CleanCommand(Command):
    description = "custom clean command that forcefully removes dist/build directories"
    user_options = []
    def initialize_options(self):
        self.cwd = None
    def finalize_options(self):
        self.cwd = os.getcwd()
    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
        os.system('rm -rf ./build ./dist')

class CleanAllCommand(Command):
    description = "custom clean command forcefully removes libimfit.a and Cython-generated files (and dist/build directories)"
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
        os.system('rm -rf ./build ./dist')
        libimfit0 = "./imfit/libimfit.a"
        libimfit1 = PREBUILT_PATH + "libimfit.a"
        libimfit2 = "./libimfit/libimfit.a"
        cython_generated = "./pyimfit/pyimfit_lib.cpp"
        cmd = 'rm -f {0} {1} {2} {3}'.format(libimfit0, libimfit1, libimfit2, cython_generated)
        print(cmd)
        os.system(cmd)



        # Define package metadata
with open("README_pyimfit.md", "r") as f:
    long_description = f.read()

# Get the version string from pyimfit/__init__.py
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',  # It excludes inline comment too
    io.open('pyimfit/__init__.py', encoding='utf_8_sig').read()
    ).group(1)

setup(
    name=NAME,   # name for distribution package (aka "distribution"), as listed on PyPI
    version=__version__,
    author="Peter Erwin",
    author_email="erwin@sigmaxi.net",
    description="Python wrapper for astronomical image-fitting program Imfit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/perwin/pyimfit",
    project_urls={"Documentation": "https://pyimfit.readthedocs.io/en/latest/",
                  "Source": "https://github.com/perwin/pyimfit"},
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "Programming Language :: C++",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Intended Audience :: Science/Research",
    ],
    python_requires='>=3.5',
    # setup_requires = temporary local installation in order to run this script
    # install_requires = standard pip installation for general future use
    setup_requires=['scons'],
    install_requires=['numpy', 'scipy'],
    cmdclass={'build_ext': my_build_ext, 'clean': CleanCommand, 'cleanall': CleanAllCommand},
    ext_modules=extensions
)
