from nfs3.nfs3_const import *
from environment import check, checkvalid, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Create_AllUnset(t, env):
    """ Create a file with all _set bits = 0
        Failure is expected due to bug #76982

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)

    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=0, 
                        file_mode_val=0777)
    #print "###DEBUG - CREATE_ALLUNSET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    #test_file_fh = res.resok.obj.handle.data

def testNfs3Create_FileModeSet(t, env):
    """ Create a file with file_mode_set=1
        Use this as a work around until bug #76982 is closed 

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE2
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.mode == 0777,
               "CREATE - file %s (mode=%d expected %d)" %
               (test_file, res.attributes.mode, 0777))

def testNfs3Create_FileModeReset(t, env):
    """ Create a file with one mode and then recreate it with another mode.
    Expect the first mode to remain. (Unchecked is the default creation type.)

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE2R
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0321)
    check(res, msg="CREATE(1) - file %s" % test_file)
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0654)
    check(res, msg="CREATE(2) - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.mode == 0321,
               "CREATE - file %s (mode=%d expected %d)" %
               (test_file, res.attributes.mode, 0321))

def testNfs3Create_SizeSet(t, env):
    """ Create a file with file_mode_set=1 and Size

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE3
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777, size_set=1, size_val=9876543210)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.size == 9876543210,   \
      "CREATE - file %s (size=%d expected %d)" %    \
      (test_file, res.attributes.size, 9876543210))    

def testNfs3Create_SizeTruncate(t, env):
    """ Create a file with a specified size and then truncate it with
    another create. (Unchecked is the default creation type.)

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE3T
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777, size_set=1, size_val=9876543210)
    check(res, msg="CREATE(1) - file %s" % test_file)
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0777, size_set=1, size_val=1234567890)
    check(res, msg="CREATE(2) - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.size == 9876543210,
               "CREATE - file %s (size=%d expected %d)" %
               (test_file, res.attributes.size, 9876543210))

    ### Execution Phase 2 ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1,
                        file_mode_val=0777, size_set=1, size_val=0)
    check(res, msg="CREATE(3) - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"

    ### Verification Phase 2 ###
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.size == 0,
               "CREATE - file %s (size=%d expected %d)" %
               (test_file, res.attributes.size, 0))

def testNfs3Create_MtimeSet(t, env):
    """ Create a file with mtime_set=2

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE4
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777, mtime_set=2, mtime_val=nfstime3(1234, 5678))
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.mtime.seconds == 1234 and \
       res.attributes.mtime.nseconds == 5678,           \
      "CREATE - file %s (mtime=%s expected %s)"         \
      % (test_file, str(res.attributes.mtime),          \
      str(nfstime3(1234, 5678))))


def testNfs3Create_AtimeSet(t, env):
    """ Create a file with atime_set=2

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE5
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777,
                        mtime_set=2, mtime_val=nfstime3(1234, 5678),
                        atime_set=2, atime_val=nfstime3(1234, 5678))
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    checkvalid(res.attributes.atime.seconds == 1234 and \
       res.attributes.atime.nseconds == 5678,           \
      "CREATE - file %s (atime=%s expected %s)"         \
      % (test_file, str(res.attributes.atime),          \
      str(nfstime3(1234, 5678))))


def testNfs3Create_UidRoot(t, env):
    """ Create a file with uid_set=1 as root

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE6
    """
    ### Setup Phase ###
    c = env.rootclient
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777,
                        uid_set=1, uid_val=1234,
                        gid_set=1, gid_val=5678)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c1.getattr(test_file_fh)
    # Allow maproot=nobody
    checkvalid(res.attributes.uid == 1234 or  \
      res.attributes.uid == 65534,            \
      "CREATE - file %s (uid=%d expected %d)" \
      % (test_file, res.attributes.uid, 1234))
    checkvalid(res.attributes.gid == 5678 or  \
      res.attributes.gid == 0,                \
      "CREATE - file %s (gid=%d expected %d)" \
      % (test_file, res.attributes.gid, 5678))


def testNfs3Create_UidAdmin(t, env):
    """ Create a file with uid_set=1 as second user

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE7
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c3.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777,
                        uid_set=1, uid_val=10,
                        gid_set=1, gid_val=10)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c3.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c3.getattr(test_file_fh)
    note = "Is vfs.nfsrv.create_attributes_ids_enabled set?"
    checkvalid(res.attributes.uid == 10,           \
      "CREATE - file %s (uid=%d expected %d) %s"   \
      % (test_file, res.attributes.uid, 10, note))
    checkvalid(res.attributes.gid == 10,           \
      "CREATE - file %s (gid=%d expected %d) %s"   \
      % (test_file, res.attributes.gid, 10, note))


def testNfs3Create_UidAdminFail(t, env):
    """ Create a file with uid_set=1 as second user

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE8
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c3.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777,
                        uid_set=1, uid_val=1234,
                        gid_set=1, gid_val=5678)
    test_file_fh = res.resok.obj.handle.data
    #print "###DEBUG - CREATE_FILEMODESET RESULTS:", res, "\n"
    
    ### Verification Phase ###
    check(res, msg="CREATE - file %s" % test_file)
    res = env.c3.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)
    res = env.c3.getattr(test_file_fh)
    checkvalid(res.attributes.uid == 10,      \
      "CREATE - file %s (uid=%d expected %d)" \
      % (test_file, res.attributes.uid, 10))
    checkvalid(res.attributes.gid == 10 or    \
      res.attributes.gid == 0,                \
      "CREATE - file %s (gid=%d expected %d)" \
      % (test_file, res.attributes.gid, 10))

def testNfs3Create_Exclusive(t, env):
    """ Create a file in exclusive mode

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE9
    """
    ### Setup Phase ###
    #verf = '12345678'
    verf = str(0x3B9ACA01)
    wrongverf = '87654321'
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)

    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - test dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data

    ### Execution Phase ###
    res = env.c1.create(test_dir_fh, test_file,
        nfs3_mode=EXCLUSIVE, exclusive_verf=verf)
    check(res, msg="CREATE - file %s" % test_file)
    fh1 = res.resok.obj.handle.data

    res = env.c1.lookup(test_dir_fh, test_file)
    check(res, msg="LOOKUP - file %s" % test_file)

    # Create with same verifier should return same object
    res = env.c1.create(test_dir_fh, test_file,
        nfs3_mode=EXCLUSIVE, exclusive_verf=verf)
    check(res, msg="2nd CREATE with correct verifier")
    fh2 = res.resok.obj.handle.data

    # Compare file handles
    checkvalid(fh1 == fh2, "Filehandle changed on 2nd exclusive create"
        "(fh1 = %s, fh2 = %s)" % (fh1, fh2))

    # Create the file again, should return an error
    res = env.c1.create(test_dir_fh, test_file,
        nfs3_mode=EXCLUSIVE, exclusive_verf=wrongverf)
    check(res, NFS3ERR_EXIST, msg="3rd CREATE with wrong verifier")

    # Create with same verifier should return same object
    res = env.c1.create(test_dir_fh, test_file,
        nfs3_mode=EXCLUSIVE, exclusive_verf=verf)
    check(res, msg="3rd CREATE with correct verifier")
    fh2 = res.resok.obj.handle.data

    # Compare file handles
    checkvalid(fh1 == fh2, "Filehandle changed on 3rd exclusive create"
        "(fh1 = %s, fh2 = %s)" % (fh1, fh2))


def testNfs3Create_ExclusiveSupported(t, env):
    """ Test for support for exclusive mode

    FLAGS: nfsv3 create all
    DEPEND:
    CODE: CREATE9a
    """
    ### Setup Phase ###
    verf = '12345678'
    verf = str(0x3B9ACA01)
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)

    ### Execution Phase ###
    res = env.c1.create(mnt_fh, test_file,
        nfs3_mode=EXCLUSIVE, exclusive_verf=verf)
    check(res, msg="CREATE - file %s" % test_file)


### ToDo: Add basic negative cases.  Beef up coverage
