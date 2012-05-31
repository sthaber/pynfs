from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Read(t, env):
    """ Read the contents of a file with the READ rpc 
    
        
    FLAGS: nfsv3 read all
    DEPEND:
    CODE: READ1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    test_data = "Test String"
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    res = env.c1.write(test_file_fh, offset=0, count=len(test_data), stable=FILE_SYNC, data=test_data)
    check(res, msg="WRITE - file %s" % test_file)
    
    ### Execution Phase ###
    res = env.c1.read(test_file_fh, offset=0, count=len(test_data))
    
    ### Verification Phase ###
    check(res, msg="READ - file %s" % test_file)
    if res.resok.data != test_data:
        t.fail.support(" ".join([
            "READ - verification: Data returned [%s]" % res.resok.data,
            "did not match expected [%s]." % test_data]))
    if len(res.resok.data) != len(test_data):
        t.fail.support(" ".join([
            "READ - verification: [%d] bytes returned" % len(res.resok.data),
            "[%d] bytes expected." % len(test_data)]))

    if res.eof != True:
        t.fail("No EOF sent!")

    ### Clean-up Phase? ###

### ToDo: Add basic negative cases.  Beef up coverage
