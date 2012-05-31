from nfs3.mount_const import *
from environment import check, checklist, checkdict, get_invalid_utf8strings
from nfs3.mountlib import *

def testMountNull(t, env):
    """ MOUNTPROC3_NULL

    FLAGS: mount nfsv3
    DEPEND:
    CODE: MOUNT_NULL
    """
    res = env.mc.mount_null()
    print "MNT_NULL RESULTS:", res, "\n"

def testMountMnt(t, env):
    """ MOUNTPROC3_MNT

    FLAGS: mount nfsv3
    DEPEND: MOUNT_NULL
    CODE: MOUNT_MNT
    """
    res = env.mc.mount_mnt('/' + '/'.join(env.mc.opts.path[:-1]))
    print "MNT RESULTS:", res, "\n"

def testMountDump(t, env):
    """ MOUNTPROC3_DUMP

    FLAGS: mount nfsv3
    DEPEND: MOUNT_NULL
    CODE: MOUNT_DUMP
    """
    res = env.mc.mount_dump()
    print "DUMP results: ", res, "\n"

def testMountExport(t, env):
    """ MOUNTPROC3_EXPORT

    FLAGS: mount nfsv3
    DEPEND: MOUNT_NULL
    CODE: MOUNT_EXPORT
    """
    c = env.rootclient
    res = env.mc.mount_export()
    print "EXPORT results: ", res, "\n"
