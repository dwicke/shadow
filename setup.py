#!/usr/bin/env python2.7

import sys, os, argparse, subprocess, shlex, shutil, urllib2, tarfile, gzip, stat
from datetime import datetime

BUILD_PREFIX="build"
INSTALL_PREFIX="/usr/local"

TOR_URL="https://archive.torproject.org/tor-package-archive/tor-0.2.2.15-alpha.tar.gz"
TOR_PATCH_URL="http://shadow.cs.umn.edu/tor-0.2.2.15-alpha.scallion.patch.gz"
RESOURCES_URL="http://shadow.cs.umn.edu/shadow-resources.tar.gz"

def main():
    parser_main = argparse.ArgumentParser(description='Utility to help setup the scallion plug-in for the shadow simulator', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_main.add_argument('-q', '--quiet', action="store_true", dest="be_quiet",
          help="this script will not display its actions", default=False)
    
    # setup our commands
    subparsers_main = parser_main.add_subparsers(help='run a subcommand (for help use <subcommand> --help)')
    
    # configure subcommand
    parser_build = subparsers_main.add_parser('build', help='configure and build scallion', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_build.set_defaults(func=build, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser_build.add_argument('-p', '--prefix', action="store", dest="prefix",
          help="path to root directory for scallion installation", metavar="PATH", default=INSTALL_PREFIX)
    parser_build.add_argument('-i', '--include', action="append", dest="extra_includes", metavar="PATH",
          help="include PATH when searching for headers. useful if dependencies are installed to non-standard locations.")
    parser_build.add_argument('-l', '--library', action="append", dest="extra_libraries", metavar="PATH",
          help="include PATH when searching for libraries. useful if dependencies are installed to non-standard locations.")
    parser_build.add_argument('-g', '--debug', action="store_true", dest="do_debug",
          help="turn on debugging for verbose program output", default=False)
    
    # install subcommand
    parser_install = subparsers_main.add_parser('install', help='install scallion', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_install.set_defaults(func=install, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser_auto = subparsers_main.add_parser('auto', help='build to ./build, install to ./install. useful for quick local setup during development.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_auto.set_defaults(func=auto, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # get arguments, accessible with args.value
    args = parser_main.parse_args()
    # run chosen command
    args.func(args)
    
def get_outfile(args):
    # check if we redirect to null
    if(args.be_quiet): return open("/dev/null", 'w')
    else: return None

def build(args):
    outfile = get_outfile(args)
    
    filepath=os.path.abspath(__file__)
    rootdir=filepath[:filepath.rfind("/")]
    builddir=os.path.abspath(BUILD_PREFIX)
    installdir=os.path.abspath(args.prefix)
    
    # clear cmake cache
    if(os.path.exists(builddir+"/scallion")): shutil.rmtree(builddir+"/scallion")
    if not os.path.exists(builddir+"/scallion"): os.makedirs(builddir+"/scallion")
    if not os.path.exists(installdir): os.makedirs(installdir)
    
    # we will run from build directory
    rundir = os.getcwd()
    os.chdir(builddir)

    if setup_dependencies(args) != 0: return
    if setup_tor(args) != 0: return
    
    os.chdir(builddir+"/scallion")

    # build up args string for cmake
    cmake_cmd = "cmake " + rootdir + " -DCMAKE_BUILD_PREFIX=" + builddir + " -DCMAKE_INSTALL_PREFIX=" + installdir
    
    if args.extra_includes is None: args.extra_includes = []
    if args.extra_libraries is None: args.extra_libraries = []
    
    # hack to make passing args to CMAKE work... doesnt seem to like the first arg
    args.extra_includes.insert(0, "./")
    args.extra_libraries.insert(0, "./")
    
    cmake_cmd += " -DCMAKE_EXTRA_INCLUDES=\"" + ';'.join(args.extra_includes) + "\""
    cmake_cmd += " -DCMAKE_EXTRA_LIBRARIES=\"" + ';'.join(args.extra_libraries) + "\""
    if(args.do_debug): cmake_cmd += " -DSCALLION_DEBUG=ON"
    
    # call cmake to configure the make process, wait for completion
    log(args, "running \'" + cmake_cmd + "\' from " + builddir)
    retcode = subprocess.call(shlex.split(cmake_cmd), stdout=outfile)
    log(args, "cmake returned " + str(retcode))
    
    if retcode == 0:
        # call make, wait for it to finish
        log(args, "calling \'make\'")
        retcode = subprocess.call(["make"], stdout=outfile)
        log(args, "make returned " + str(retcode))
        log(args, "now run \'python setup.py install\'")

    # go back to where we came from
    os.chdir(rundir)
    return retcode

def install(args):
    outfile = get_outfile(args)
    
    builddir=os.path.abspath(BUILD_PREFIX)
    if not os.path.exists(builddir): 
        log(args, "ERROR: please build before installing!")
        return

    # go to build dir and install from makefile
    rundir = os.getcwd()
    os.chdir(builddir+"/scallion")
    
    # call make install, wait for it to finish
    log(args, "calling \'make install\'")
    retcode = subprocess.call(["make", "install"], stdout=outfile)
    log(args, "make install returned " + str(retcode))
    if retcode == 0: log(args, "run \'shadow -d src/scallion.dsim -l build/scallion/src/libshadow-plugin-scallion-preload.so\'")
    
    # go back to where we came from
    os.chdir(rundir)
    return retcode

def auto(args):
    args.prefix = "./install"
    args.do_debug = False
    args.extra_includes = None
    args.extra_libraries = None
    if build(args) == 0: install(args)
    
def setup_tor(args):
    rundir = os.getcwd()
    outfile = get_outfile(args)

    # if we already have a directory, dont rebuild
    if(os.path.exists(args.tordir+"/src/or/tor")): 
        include_tor(args)
        return 0

    cflags = "-fPIC -I/usr/local/include"
    if args.extra_includes is not None:
        for i in args.extra_includes: cflags += " -I" + i.strip()
    
    ldflags = "-L/usr/local/lib"
    if args.extra_libraries is not None:
        for l in args.extra_libraries: ldflags += " -L" + l.strip()

    patch = "patch -Np1 --batch -i " + args.patchfile
    configure = "./configure --disable-static-vars --disable-transparent --disable-threads --disable-asciidoc CFLAGS=\"" + cflags + "\" LDFLAGS=\"" + ldflags + "\" LIBS=-lrt"
    gen = "./autogen.sh"
    build = "make"
    
    rundir = os.getcwd()
    os.chdir(args.tordir)
    
    log(args, patch)
    retcode = subprocess.call(shlex.split(patch), stdout=outfile)
    if(retcode == 0):
        os.chmod("autogen.sh", stat.S_IREAD|stat.S_IEXEC);
        log(args, gen)
        retcode = subprocess.call(shlex.split(gen), stdout=outfile)
    
    if retcode != 0:
        os.chdir(rundir)
        shutil.rmtree(args.tordir)
        return -1
    
    retcode = -1
    if(os.path.exists(args.tordir)):
        # configure
        os.chdir(args.tordir)
        log(args, configure)
        if subprocess.call(shlex.split(configure), stdout=outfile) == 0:
            log(args, build)
            retcode = subprocess.call(shlex.split(build), stdout=outfile)

    os.chdir(rundir)
    if retcode != 0:
        shutil.rmtree(args.tordir)
        return -1
    
    include_tor(args)        
    
    return retcode

def include_tor(args):
    if args.extra_includes is None: args.extra_includes = []
    args.extra_includes.extend([args.tordir, args.tordir+"/src/or", args.tordir+"/src/common"])
    
    if args.extra_libraries is None: args.extra_libraries = []
    args.extra_libraries.extend([args.tordir, args.tordir+"/src/or", args.tordir+"/src/common"])
    
def setup_dependencies(args):
    outfile = get_outfile(args)
    
    log(args, "downloading resources...")
    
    args.target_resources = os.path.abspath(os.path.basename(RESOURCES_URL))
    args.target_tor = os.path.abspath(os.path.basename(TOR_URL))
    args.tordir = args.target_tor[:args.target_tor.rindex(".tar.gz")]
    args.target_tor_patch = os.path.abspath(os.path.basename(TOR_PATCH_URL))
    args.patchfile = args.target_tor_patch[:args.target_tor_patch.rindex('.')]
    
    # download and extract
#    if not os.path.exists(args.target_resources) and download(RESOURCES_URL, args.target_resources) != 0:
#        log(args, "failed to download " + RESOURCES_URL)
#        return -1
#    if tarfile.is_tarfile(args.target_resources):
#        tar = tarfile.open(args.target_resources, "r:gz")
#        tar.extractall()
#        tar.close()
#    else: return -1

    if not os.path.exists(args.target_tor):
        if download(TOR_URL, args.target_tor) != 0:
            log(args, "failed to download " + TOR_URL)
            return -1
    if not os.path.exists(args.tordir):
        if tarfile.is_tarfile(args.target_tor):
            tar = tarfile.open(args.target_tor, "r:gz")
            tar.extractall()
            tar.close()
        else: return -1

    if not os.path.exists(args.target_tor_patch):
        if download(TOR_PATCH_URL, args.target_tor_patch) != 0:
            log(args, "failed to download " + TOR_PATCH_URL)
            return -1
    if not os.path.exists(args.patchfile):
        fin = gzip.open(args.target_tor_patch, 'r')
        fout = open(args.patchfile, 'w')
        fout.writelines(fin)
        fout.close()
        fin.close()
    
    return 0

def download(url, target_path):
    try:
        u = urllib2.urlopen(url)
        localfile = open(target_path, 'w')
        localfile.write(u.read())
        localfile.close()
        return 0
    except urllib2.URLError:
        return -1

def log(args, msg):
    if not args.be_quiet:
        color_start_code = "\033[94m" # red: \033[91m"
        color_end_code = "\033[0m"
        prefix = "[" + str(datetime.now()) + "] setup: "
        print >> sys.stderr, color_start_code + prefix + msg + color_end_code

if __name__ == '__main__':
    main()