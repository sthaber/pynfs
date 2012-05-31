from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3MkDir(t, env):
    """ Create a target dir and execute the LOOKUP RPC to verify success


    FLAGS: nfsv3 mkdir all
    DEPEND:
    CODE: MKDIR1
    """
    ### Setup Phase ###
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    ### Execution Phase ###
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    
    ### Verification Phase ###
    check(res, msg="MKDIR - dir %s" % test_dir)
    res = env.c1.lookup(mnt_fh, test_dir)
    check(res, msg="LOOKUP - dir %s" % test_dir)
    
    
### ToDo: Add basic negative cases.  Beef up coverage

