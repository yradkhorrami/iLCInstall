##################################################
#
# Marlin module
#
# Author: Jan Engels, DESY
# Date: Jan, 2007
#
##################################################

# custom imports
from baseilc import BaseILC
from util import *


class Marlin(BaseILC):
    """ Responsible for the Marlin software installation process. """
    
    def __init__(self, userInput):
        BaseILC.__init__(self, userInput, "Marlin", "Marlin")

        self.reqfiles = [ ["lib/libMarlin.a", "lib/libMarlin.so", "lib/libMarlin.dylib"], ["bin/Marlin"] ]

        # list of packages ( MarlinUtil, MarlinReco ... )
        self.pkgs = []

        # LCIO is required for building Marlin
        self.reqmodules = [ "LCIO" ]

        # optional modules
        self.optmodules = [ "MarlinUtil", "CEDViewer", "MarlinReco", "PandoraPFA", "SiliconDigi", "LCFIVertex", "GEAR", "CLHEP", "LCCD", "RAIDA" ]

        # supported cmake "build_with" modules
        self.cmakebuildmodules = [ "GEAR", "CLHEP", "LCCD", "RAIDA" ]
    
    def compile(self):
        """ compile Marlin """
        
        os.chdir( self.env["MARLINWORKDIR"] )
        
        # write userlib.gmk
        f = open( "userlib.gmk", 'w')
        f.write( 80*'#' + "\n# Environment generated by ilcsoft-install on " + time.ctime() + '\n' )
        f.write( "# for " + self.name + " located at [ " + self.installPath + " ]\n" + 80*'#' + '\n' )
        self.writeBuildEnv(f, [])
        f.close()

        # write userlib_workdir.gmk
        f = open( "userlib_workdir.gmk", 'w')
        f.write( 80*'#' + "\n# Environment generated by ilcsoft-install on " + time.ctime() + '\n' )
        f.write( "# for " + self.name + " located at [ " + self.installPath + " ]\n" + 80*'#' + '\n' )
        chk = []
        for pkg in self.pkgs:
            # write build flags for packages
            pkg.writeBuildEnv(f, [], True, False)
            # avoid writing duplicate build flags of packages
            chk.append( pkg.name )
        # write the rest of the build flags
        self.writeBuildEnv(f, chk)
        f.close()

        # create packages directory
        trymakedir( self.env["MARLINWORKDIR"] + "/packages" )
        # remove all package links
        os.chdir( self.env["MARLINWORKDIR"] + "/packages" )
        # get a list of all files inside packages directory
        files = glob.glob("*")
        for file in files:
            if( file != "CVS" ):
                if( os.path.islink(file) ):
                    os.unlink( file )
                else:
                    print "*** WARNING: [ " + dereflinks(file) + " ] is NOT a symbolic link!!" \
                            + " Marlin will rebuild itself with this package!!"
    
        # create links to packages
        os.chdir( self.env["MARLINWORKDIR"] + "/packages" )
        for pkg in self.pkgs:
            if( not os.path.exists(pkg.name) ):
                print "* Creating Link " + pkg.name + " to [ " + pkg.installPath + " ]"
                os.symlink( pkg.installPath, pkg.name )
            else:
                print "*** WARNING: [ " + dereflinks(pkg.name) + " ] is NOT a symbolic link!!" \
                        + " Marlin will be built with this package and not the one defined in your config file!! " 
    
        os.chdir( self.installPath )

        if( self.useCMake ):
            os.chdir( "build" )

        if( self.rebuild ):
            if( self.useCMake ):
                tryunlink( "CMakeCache.txt" )
            else:
                os.system( "make clean" )

        # build software
        if( self.useCMake ):
            if( os.system( "cmake " + self.genCMakeCmd() + " .. 2>&1 | tee -a " + self.logfile ) != 0 ):
                self.abort( "failed to configure!!" )
        
        if( os.system( "make 2>&1 | tee -a " + self.logfile ) != 0 ):
            self.abort( "failed to compile!!" )

        if( self.useCMake ):
            if( os.system( "make install 2>&1 | tee -a " + self.logfile ) != 0 ):
                self.abort( "failed to install!!" )
        
    def buildDocumentation(self):
        # build documentation
        if( self.buildDoc ):
            if( self.useCMake ):
                # create packages directory
                trymakedir( self.env["MARLINWORKDIR"] + "/packages" )
                os.chdir( self.env["MARLINWORKDIR"] + "/packages" )
                # create links to packages
                for pkg in self.parent.modules:
                    if( pkg.isMarlinPKG ):
                        if( not os.path.exists(pkg.name) ):
                            print "* Creating Link " + pkg.name + " to [ " + pkg.installPath + " ]"
                            os.symlink( pkg.installPath, pkg.name )
    
            if(isinPath("doxygen")):
                os.chdir( self.env["MARLINWORKDIR"] )
                print 80*'*' + "\n*** Creating C++ API documentation for " + self.name + " with doxygen...\n" + 80*'*'
                if( os.system( "make doc 2>&1 | tee -a " + self.logfile ) != 0 ):
                    self.abort( "failed to build documentation!!" )

    def cleanupInstall(self):
        BaseILC.cleanupInstall(self)
        for pkg in self.pkgs:
            pkg.cleanupInstall()
    
    def init(self):

        BaseILC.init(self)

        self.env["MARLIN"] = self.installPath
        
        # if MARLINWORKDIR not set, set it to MARLIN
        if( not self.env.has_key("MARLINWORKDIR") ):
                self.env["MARLINWORKDIR"] = self.installPath

        if( self.mode == "install" ):
            # compatibility issues for older versions
            # check if marlin version is older or equal to v00-09-06
            if( self.evalVersion("v00-09-06") != 2 ):
                if( "MarlinUtil" in self.optmodules ):
                    marlinutil = self.parent.module("MarlinUtil")
                    if( marlinutil != None ):
                        marlinutil.envbuild["USERINCLUDES"].append( "-I" \
                                + marlinutil.installPath + "/include" )

            if( self.debug ):
                self.env["MARLINDEBUG"] = "1"

            # check for doc tools
            if( self.buildDoc ):
                if( not isinPath("doxygen")):
                    print "*** WARNING: doxygen was not found!! " + self.name + " documentation will not be built!!! "

    def preCheckDeps(self):
        BaseILC.preCheckDeps(self)
        if( self.mode == "install" ):
            if( self.env.has_key("MARLIN_GUI")):
                if( str(self.env["MARLIN_GUI"]) == "1" ):
                    self.addExternalDependency( ["QT"] )
                    self.reqfiles.append(["bin/MarlinGUI"])
            if( self.useCMake ):
                packages = []
                for modname in self.optmodules:
                    mod = self.parent.module( modname )
                    if( mod != None and mod.isMarlinPKG ):
                        packages.append( modname )
                self.buildWithout( packages )
            else:
                self.reqfiles.append( ["bin/marlin_libs.sh"] )
                self.reqfiles.append( ["bin/marlin_includes.sh"] )


    def postCheckDeps(self):
        if( self.mode == "install" ):
            if( self.env.has_key("MARLIN_GUI")):
                if( str(self.env["MARLIN_GUI"]) == "1" ):
                    qt = self.parent.module("QT")
                    # check for qt version 4
                    if( qt != None and qt.evalVersion("4.0") != 2 ):
                        self.abort( "you need QT 4!! QT version " + qt.version + " found..." )
            
            # enable AIDA
            if( "RAIDA" in self.optmodules or "AIDAJNI" in self.optmodules ):
                self.env["MARLIN_USE_AIDA"] = "1"
