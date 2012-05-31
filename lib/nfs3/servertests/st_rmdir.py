from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Rmdir(t, env):
    """ Remove a directory with the RMDIR rpc 
    
    
    FLAGS: nfsv3 rmdir all
    DEPEND:
    CODE: RMDIR1
    """
    ### Setup Phase ###
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    
    ### Execution Phase ###
    res = env.c1.rmdir(mnt_fh, test_dir)
    
    ### Verification Phase ###
    check(res, msg="RMDIR - dir %s" % test_dir)
    res = env.c1.lookup(mnt_fh, test_dir)
    if res.status == NFS3_OK:
        t.fail_support("REMOVE FAILED:  Dir [%] still exists." % test_dir)
    

###### Other variations:
### Removing a dir with contents
### Removing a dir without permissions
