from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Lookup(t, env):
    """ Get the handle for a file via the LOOKUP rpc
    

    FLAGS: nfsv3 lookup all
    DEPEND:
    CODE: LOOKUP1 
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s " % test_file)
    test_file_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.lookup(test_dir_fh, test_file)
    
    check(res, msg="LOOKUP - file %s" % test_file)
    if res.object.data != test_file_fh:
        t.fail.support(" ".join([
            "LOOKUP - file handle returned [%s]" % res.object.data ,
            "is different than return of CREATE [%s]"  % test_file_fh]))


### ToDo: Add basic negative cases ... follow pattern set up in nfs4.  Beef up coverage
