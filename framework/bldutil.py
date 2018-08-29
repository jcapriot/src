import glob, os, sys, re,  py_compile
import configure

# The following adds all SCons SConscript API to the globals of this module.
import SCons
version = list(map(int,SCons.__version__.split('.')[:3]))
if version[0] >= 1  or version[1] >= 97 or \
   (version[1] == 96 and version[2] >= 90):
    from SCons.Script import *
else:  # old style
    import SCons.Script.SConscript
    globals().update(SCons.Script.SConscript.BuildDefaultGlobals())

################################################################################

# Constants used in multiple functions. Internal to module.

__py_success = 0 # user-defined
__include = re.compile(r'#include\s*\"([^\"]+)\.h\"')
__local_include = re.compile(r'\s*\#include\s*\"([^\"]+)')

################################################################################

def __includes(list,file):
    global __local_include
    fd = open(file,'r')
    for line in fd.readlines():
         match = __local_include.match(line)
         if match:
             other = os.path.join(os.path.dirname(file),match.group(1))
             if not other in list:
                 __includes(list,other)
    list.append(file)
    fd.close()

def __read_version_file(fname=None):
    if fname == None:
        return ''
    else:
        inp = open(fname, 'r')
        known_version = inp.readline().rstrip()
        inp.close()
        return known_version

def __version(target=None,source=None,env=None):
    label=env.get('version')
    fd = open(str(target[0]),'w')
    fd.write('#ifndef _RSF_VERSION\n')
    fd.write('#define _RSF_VERSION "%s"\n' % label)
    fd.write('#endif')
    fd.close()
    return __py_success

def __merge(target=None,source=None,env=None):
    global __local_include
    sources = list(map(str,source))
    incs = []
    for src in sources:
        if not src in incs:
            __includes(incs,src)
    out = open(str(target[0]),'w')
    for src in incs:
        inp = open(src,'r')
        for line in inp.readlines():
            if not __local_include.match(line):
                out.write(line)
        inp.close()
    out.close()
    return __py_success

################################################################################

def __included(node,env,path):
    file = os.path.basename(str(node))
    file = re.sub('\.[^\.]+$','',file)
    contents = node.get_contents()
    includes = __include.findall(contents)
    if file in includes:
        includes.remove(file)
    return [x + '.h' for x in includes]

Include = Scanner(name='Include', function=__included, skeys=['.c'])

################################################################################

def __header(target=None,source=None,env=None):
    'generate a header file'
    inp = open(str(source[0]),'r')
    text = ''.join(inp.readlines())
    inp.close()
    file = str(target[0])
    prefix = env.get('prefix','')
    define = prefix + os.path.basename(file).replace('.','_')
    out = open(file,'w')
    out.write('/* This file is automatically generated. DO NOT EDIT! */\n\n')
    out.write('#ifndef _' + define + '\n')
    out.write('#define _' + define + '\n\n')
    toheader = re.compile(r'\n((?:\n[^\n]+)+)\n'
                          '\s*\/\*(\^|\<(?:[^>]|\>[^*]|\>\*[^/])*\>)\*\/')
    kandr = re.compile(r'\s*\{?\s*$') # K&R style function defs end with {
    for extract in toheader.findall(text):
        if extract[1] == '^':
            out.write(extract[0]+'\n\n')
        else:
            function = kandr.sub('',extract[0])
            out.write(function+';\n')
            out.write('/*'+extract[1]+'*/\n\n')
    out.write('#endif\n')
    out.close()
    return __py_success

Header = Builder (action = Action(__header,varlist=['prefix']),
                  src_suffix='.c',suffix='.h')

################################################################################

def __docmerge(target=None,source=None,env=None):
    outfile = target[0].abspath
    out = open(outfile,'w')
    out.write('import rsf.doc\n\n')
    for src in map(str,source):
        inp = open(src,'r')
        for line in inp.readlines():
                out.write(line)
        inp.close()
    alias = env.get('alias',{})
    for prog in list(alias.keys()):
        out.write("rsf.doc.progs['%s']=%s\n" % (prog,alias[prog]))
    out.close()
#    print outfile
    py_compile.compile(outfile,outfile+'c')
    return __py_success

def __pycompile_emit(target, source, env):
    target.append(str(target[0])+'c')
    return target,source

Docmerge = Builder(action=Action(__docmerge,varlist=['alias']),
                   emitter=__pycompile_emit)

################################################################################

def __placeholder(target=None,source=None,env=None):
    filename = str(target[0])
    out = open(filename,'w')
    var = env.get('var')
    out.write('#!/usr/bin/env python\n')
    out.write('import sys\n\n')
    out.write('sys.stderr.write(\'\'\'\n%s is not installed.\n')
    if var:
        out.write('Check $RSFROOT/share/madagascar/etc/config.py for ' + var)
        out.write('\nand reinstall if necessary.')
    message = env.get('message')
    if message:
        out.write(message)
    package = env.get('package')
    if package:
        out.write('\nPossible missing packages: ' + package)
    out.write('\n\'\'\' % sys.argv[0])\nsys.exit(1)\n')
    out.close()
    os.chmod(filename,0o775)
    return __py_success

Place = Builder (action = Action(__placeholder,varlist=['var','package']))

################################################################################

def __pycompile(target, source, env):
    "convert py to pyc "
    for i in range(0,len(source)):
        py_compile.compile(source[i].abspath,target[i].abspath)
    return __py_success

Pycompile = Builder(action=__pycompile)

################################################################################

def Debug():
    'Environment for debugging'
    env = Environment()
    srcroot = os.environ.get('RSFSRC', '../..')
    opts = configure.options(os.path.join(srcroot,'config.py'))
    opts.Update(env)
    env['CFLAGS'] = env.get('CFLAGS','').replace('-O2','-g')
    if  env['PLATFORM'] == 'sunos':
        env['CFLAGS'] = env.get('CFLAGS','').replace('-xO2','-g')
    env['CXXFLAGS'] = env.get('CXXFLAGS','').replace('-O2','-g')
    env['F90FLAGS'] = env.get('F90FLAGS','').replace('-O2','-g')
    env['version'] = __read_version_file(os.path.join(srcroot,'VERSION.txt'))
    env.SConsignFile(None)
    env.Append(BUILDERS={'RSF_Include':Header,
                         'RSF_Place':Place},
               SCANNERS=[Include])
    return env

################################################################################

def depends(env,list,file):
    'Find dependencies for C'
    filename = env.File(file+'.c').abspath
    # replace last occurence of build/
    last = filename.rfind('build/')
    if last >= 0:
        filename = filename[:last] + filename[last+6:]
    fd = open(filename,'r')
    for line in fd.readlines():
        for inc in __include.findall(line):
            if inc not in list and inc[0] != '_':
                list.append(inc)
                depends(env,list,inc)
    fd.close()

################################################################################

def depends90(env,list,file):
    'Find dependencies for Fortran-90'

    include90 = re.compile(r'^[^!]*use\s+(\S+)')
    filename = env.File(file+'.f90').abspath
    # replace last occurence of build/
    last = filename.rfind('build/')
    if last >= 0:
        filename = filename[:last] + filename[last+6:]
    fd = open(filename,'r')
    for line in fd.readlines():
        for inc in include90.findall(line):
            if inc not in list+['rsf','iso_c_binding']:
                list.append(inc)
                depends90(env,list,inc)
    fd.close()

################################################################################

def chk_exists(prog, ext='c', mainprog=True):
    'Check if file corresponding to program name exists'

    ext = ext.lstrip('.') # In case the user put a dot
    prognm = prog + '.' + ext
    if mainprog:
        prognm = 'M' + prognm
    try:
        assert os.path.isfile(prognm)
    except:
        msg = 'Missing file: ' + os.path.join(os.getcwd(),prognm)
        configure.stderr_write(msg,'yellow_on_red')
        sys.exit(configure.unix_failure)

################################################################################

def build_install_c_mpi(env, progs_c, srcroot, bindir, glob_build, bldroot):
    'Build and install C programs with MPI'
    tenv = env.Clone()
    tenv.Prepend(
                CPPPATH=[os.path.join(srcroot,'include')],
                LIBPATH=[os.path.join(srcroot,'lib')],
                LIBS=[env.get('DYNLIB','')+'rsf'])
    mpicc = tenv['MPICC']
    tenv['CC'] = mpicc

    mains_c = Split(progs_c)
    for prog in mains_c:
        if not glob_build:
            chk_exists(prog)
        sources = ['M' + prog]
        depends(tenv, sources, 'M'+prog)
        if mpicc:
            prog = tenv.Program(prog, [x + '.c' for x in sources])
        else:
            prog = env.RSF_Place('sf'+prog,None,var='MPICC',package='mpi')

        if glob_build:
            tenv.Install(bindir,prog)

    if glob_build:
        docs_c = [env.Doc(prog,'M'+prog) for prog in mains_c]
    else:
        docs_c = None

    return docs_c

################################################################################

def build_install_c(env, progs_c, srcroot, bindir, libdir, glob_build, bldroot):
    'Build and install C programs'

    dynlib = env.get('DYNLIB','')

    env.Prepend(CPPPATH=[os.path.join(srcroot,'include')],
                LIBPATH=[os.path.join(srcroot,'lib')],
                LIBS=[dynlib+'rsf'])

    src = Glob('[a-z]*.c')

    for source in src:
        inc = env.RSF_Include(source,prefix='')
        obj = env.StaticObject(source)
        env.Ignore(inc,inc)
        env.Depends(obj,inc)

    mains_c = Split(progs_c)
    for prog in mains_c:
        if not glob_build:
            chk_exists(prog)
        sources = ['M' + prog]
        depends(env, sources, 'M'+prog)
        prog = env.Program(prog, [x + '.c' for x in sources])
        if glob_build:
            install = env.Install(bindir,prog)

            if dynlib and env['PLATFORM'] == 'darwin':
                env.AddPostAction(install,
                'install_name_tool -change '
                'build/api/c/libdrsf.dylib '
                '%s/libdrsf.dylib %s' % (libdir,install[0]))

    if glob_build:
        docs_c = [env.Doc(prog,'M'+prog) for prog in mains_c]
    else:
        docs_c = None

    return docs_c

################################################################################

def build_install_f90(env, progs_f90, srcroot, bindir, api, bldroot, glob_build):
    'Build and install Fortran90 programs'

    mains_f90 = Split(progs_f90)

    if 'f90' in api:

        F90 = env.get('F90')
        assert F90 != None # The configure step should have found the compiler

        env.Prepend(LIBS=['rsff90','rsf'], # order matters when linking
                    LIBPATH=[os.path.join(srcroot,'lib')],
                    F90PATH=os.path.join(srcroot,'include'))

        for prog in mains_f90:
            if not glob_build:
                chk_exists(prog, 'f90')
            obj_dep = []
            sources = ['M' + prog]
            # Allow concatenating all modules in one file and injecting job
            # parameters for job-specific optimization:
            run_depends90 = True
            if 'findF90depends' in env:
                if env['findF90depends'] == 'n':
                    run_depends90 = False
            if run_depends90:
                depends90(env,sources,'M'+prog)
            for f90_src in sources:
                obj = env.StaticObject(f90_src+'.f90')
                # SCons mistakenly treats ".mod" files as ".o" files, and
                # tries to build them the same way (which fails). So we
                # explicitly keep just the ".o" files as dependencies:
                for fname in obj:
                    if os.path.splitext(fname.__str__())[1] == '.o':
                        obj_dep.append(fname)
            # Using obj_dep instead of the list of sources because when two
            # mains used the same module, object files for the module were
            # created in both places, hence endless "double-define" warnings
            prog = env.Program(prog, obj_dep, LINK=F90)
            if glob_build:
                env.Install(bindir,prog)

    else: # Put in a placeholder
        for prog in mains_f90:
            prog = env.RSF_Place('sf'+prog,None,package='Fortran90+API=F90')
            if glob_build:
                env.Install(bindir,prog)

    if glob_build:
        docs_f90 = [env.Doc(prog,'M'+prog+'.f90',lang='f90') for prog in mains_f90]
    else:
        docs_f90 = None

    return docs_f90

################################################################################

def install_py_mains(env, progs_py, bindir):
    'Copy Python programs to bindir, generate list of self-doc files'

    mains_py = Split(progs_py)

    if sys.platform[:6] == 'cygwin':
        exe = '.exe'
    else:
        exe = ''

    for prog in mains_py:
        binary = os.path.join(bindir,'sf'+prog+exe)
        # Copy the program to the right location
        env.InstallAs(binary,'M'+prog+'.py')
        # Fix permissions for executable python files
        env.AddPostAction(binary,Chmod(str(binary),0o755))
    env.RSF_Pycompile('M'+prog+'.py')

    # Self-doc
    user = os.path.basename(os.getcwd())
    main = 'sf%s.py' % user
    docs_py = [env.Doc(prog,'M'+prog+'.py',lang='python') for prog in mains_py]

    return docs_py

################################################################################

def install_jl_mains(env, progs_jl, bindir):
    'Copy Julia programs to bindir'

    mains_jl = Split(progs_jl)

    if sys.platform[:6] == 'cygwin':
        exe = '.exe'
    else:
        exe = ''

    for prog in mains_jl:
        binary = os.path.join(bindir,'sf'+prog+exe)
        # Copy the program to the right location
        env.InstallAs(binary,'M'+prog+'.jl')
        # Fix permissions for executable python files
        env.AddPostAction(binary,Chmod(str(binary),0o755))

################################################################################

def install_py_modules(env, py_modules, pkgdir):
    'Compile Python modules and install to pkgdir/user'

    rsfuser = os.path.join(pkgdir,'user')
    for module in Split(py_modules):
        env.RSF_Pycompile(module+'.pyc',module+'.py')
        env.Install(rsfuser,[module+'.py',module+'.pyc'])

################################################################################

def py_install(src, env, targetdir):
    'Compile and install py module'

    [filenm, ext] = os.path.splitext(src)

    if ext == '.py':
        source = filenm
    elif ext == '':
        source = src

    py = source+'.py'
    pyc = py+'c'
    env.RSF_Pycompile(pyc,py)
    env.Install(targetdir,[py,pyc])

################################################################################

def install_self_doc(env, libdir, docs_c=None, docs_py=None, docs_f90=None, docs_c_mpi=None):

    docs = []
    if docs_c != None:
        docs += docs_c
    if docs_py != None:
        docs += docs_py
    if docs_f90 != None:
        docs += docs_f90
    if docs_c_mpi != None:
        docs += docs_c_mpi

    env.Depends(docs,'#/framework/rsf/doc.py')

    user = os.path.basename(os.getcwd())
    main = 'sf%s.py' % user
    doc = env.RSF_Docmerge(main,docs)
    env.Install(libdir,doc)

################################################################################

def add_ext_lib(env, libnm, root=None, libdir='lib', static=True):

    if not root:
        root = env.get('RSFROOT',os.environ.get('RSFROOT'))

    if static:
        ext = '.a'
    else:
        ext = '.so'

    env['LIBS'].append(File(os.path.join(root, libdir, 'lib'+libnm+ext)))
    env['CPPPATH'].append(os.path.join(root,'include'))

################################################################################

class UserSconsTargets:
    'Describes and builds targets that can be found in user SConstructs'
    def __init__(self):
        self.c = None # C mains
        self.c_mpi = None # C with MPI
        self.c_place = None # C with placeholders
        self.c_libs = None
        self.f90 = None # F90 mains
        self.py = None # Python mains
        self.py_modules = None # Python modules that do not need SWIG and numpy
        self.jl = None # Julia mains
    def build_all(self, env, glob_build, srcroot, bindir, libdir, pkgdir):
        if glob_build:
            env = env.Clone()

        # Needed for both C and F90 programs:
        bldroot = '../..' # aka RSFSRC/build

        if not glob_build:
            bldroot = env.get('RSFROOT',os.environ.get('RSFROOT',sys.prefix))
            if self.f90:
                SConscript(os.path.join(srcroot, 'api', 'f90', 'SConstruct'))
            else:
                SConscript(os.path.join(srcroot, 'api', 'c', 'SConstruct'))

        if not self.c:
            docs_c = []
        else:
            docs_c = build_install_c(env, self.c, srcroot, bindir, libdir, glob_build, bldroot)

        if self.c_place:
            docs_c += [env.Doc(prog,'M'+prog) for prog in Split(self.c_place)]

        if not self.c_mpi:
            docs_c_mpi = None
        else:
            docs_c_mpi = build_install_c_mpi(env,self.c_mpi, srcroot, bindir,glob_build,bldroot)

        api = env.get('API',[])
        if not self.f90:
            docs_f90 = None
        else:
            docs_f90 = build_install_f90(env, self.f90, srcroot, bindir, api, bldroot,
                                         glob_build)

        if glob_build:
            if not self.py:
                docs_py = None
            else:
                docs_py = install_py_mains(env, self.py, bindir)
            if self.py_modules:
                install_py_modules(env, self.py_modules, pkgdir)

            if self.jl:
                install_jl_mains(env, self.jl, bindir)

            install_self_doc(env, pkgdir, docs_c, docs_py, docs_f90, docs_c_mpi)

# Additions by Hui Wang

class HuiSconsTargets:
    '''Simple wrapper for convinent building'''
    docs = []
    has_lapack = False
    has_nvcc = False
    def __init__(self, cfiles=None, ccfiles=None, cufiles=None, cmpifiles=None):
        self.c = cfiles
        self.cc = ccfiles
        self.cu = cufiles
        self.c_mpi = cmpifiles

# -----------------------------------------------------------------------------
    @classmethod
    def install_docs(cls,env,pkgdir,glob_build):
        if glob_build and cls.docs:
            env.Depends(cls.docs, '#/framework/rsf/doc.py')
            user = os.path.basename(os.getcwd())
            main = 'sf%s.py' % user
            doc = env.RSF_Docmerge(main,cls.docs)
            env.Install(pkgdir,doc)

# -----------------------------------------------------------------------------

    def build_c(self, env, glob_build, srcroot, bindir, libdir, pkgdir):
        bldroot = '../..'
        if not glob_build:
            bldroot = env.get('RSFROOT', os.environ.get('RSFROOT',sys.prefix))
            # SConscript(os.path.join(srcroot, 'api', 'c', 'SConstruct'))
        if not self.c:
            docs_c = None
        else:
            docs_c = build_install_c(env, self.c, srcroot, bindir, libdir, glob_build, bldroot)
        if glob_build:
            HuiSconsTargets.docs.append(docs_c)

# -----------------------------------------------------------------------------

    def build_cc(self, env, glob_build, srcroot, bindir, libdir, pkgdir):
        if not self.cc:
            docs_cc = None
        else:
            docs_cc = self.build_install_cc(env, self.cc, srcroot, bindir, libdir, glob_build)
        if glob_build:
            HuiSconsTargets.docs.append(docs_cc)

# -----------------------------------------------------------------------------
    def build_cu(self, env, glob_build, srcroot, bindir, libdir, pkgdir):
        # Assume using C API rather than CPP API
        if not self.cu:
            docs_cu = None
        else:
            docs_cu = self.build_install_cu(env, self.cu, srcroot, bindir, libdir, glob_build)
        if glob_build:
            HuiSconsTargets.docs.append(docs_cu)

# -----------------------------------------------------------------------------
    def build_c_mpi(self, env, glob_build, srcroot, bindir, libdir, pkgdir):
        bldroot = '../..'
        if not glob_build:
            bldroot = env.get('RSFROOT', os.environ.get('RSFROOT',sys.prefix))
        if not self.c_mpi:
            docs_c_mpi = None
        else:
            docs_c_mpi = build_install_c_mpi(env, self.c_mpi, srcroot, bindir, glob_build, bldroot)
        if glob_build:
            HuiSconsTargets.docs.append(docs_c_mpi)

# -----------------------------------------------------------------------------

    # @classmethod
    def build_install_cc(self,env, progs_cc, srcroot, bindir, libdir, glob_build):
        'Build and install CC programs'
        dynlib = env.get('DYNLIB','')
        env.Prepend(CPPPATH=[os.path.join(srcroot,'include')],
                    LIBPATH=[os.path.join(srcroot,'lib')],
                    LIBS=[dynlib+'rsf'])
        if 'c++' in env.get('API',[]):
            env.Prepend(LIBS=[dynlib+'rsf++'])
        mains_cc = Split(progs_cc)
        for prog in mains_cc:
            sources = ['M' + prog]
            if 'c++' in env.get('API',[]) and self.has_lapack:
                prog = env.Program(prog,[x + '.cc' for x in sources])
            else:
                prog = env.RSF_Place('sf'+prog,None,var='LAPACK',package='lapack')

            if glob_build:
                install = env.Install(bindir,prog)
                if dynlib and env['PLATFORM'] == 'darwin':
                    env.AddPostAction(install,
                    'install_name_tool -change '
                    'build/api/c/libdrsf.dylib '
                    'build/api/c++/libdrsf++.dylib '
                    '%s/libdrsf.dylib %s' % (libdir,install[0]))
        if glob_build:
            docs_cc = [env.Doc(prog,'M'+prog+'.cc') for prog in mains_cc]
        else:
            docs_cc = None

        return docs_cc

# -----------------------------------------------------------------------------

    # @classmethod
    def build_install_cu(self,env, progs_cu, srcroot, bindir, libdir, glob_build):
        'Build and install CUDA programs'
        dynlib = env.get('DYNLIB','')

        env.Prepend(CPPPATH=[os.path.join(srcroot,'include')],
                    LIBPATH=[os.path.join(srcroot,'lib')],
                    LIBS=[dynlib+'rsf'])

        mains_cu = Split(progs_cu)
        for prog in mains_cu:
            if not glob_build:
                chk_exists(prog,'cu')

            sources = env.Command(prog+'.cpp','M'+prog+'.cu','cp $SOURCE $TARGET')
            if self.has_nvcc:
                prog = env.Program(prog,sources)
            else:
                prog = env.RSF_Place('sf'+prog,None,var='CUDA Toolkit',package='CUDA Toolkit')

            if glob_build:
                install = env.Install(bindir,prog)
                if dynlib and env['PLATFORM'] == 'darwin':
                    env.AddPostAction(install,
                    'install_name_tool -change '
                    'build/api/c/libdrsf.dylib '
                    '%s/libdrsf.dylib %s' % (libdir,install[0]))
        if glob_build:
            docs_cu = [env.Doc(prog,'M'+prog+'.cu') for prog in mains_cu]
        else:
            docs_cu = None

        return docs_cu

# -----------------------------------------------------------------------------
