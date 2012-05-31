from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Remove(t, env):
    """ Create a file and remove it with the REMOVE rpc 
        
        
    FLAGS: nfsv3 remove all
    DEPEND:
    CODE: REMOVE1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s " % test_file)
        
    ### Execution Phase ###
    res = env.c1.remove(test_dir_fh, test_file)
        
    ### Verification Phase ###
    check(res, msg="REMOVE - file %s" % test_file)
    res = env.c1.lookup(test_dir_fh, test_file)
    if res.status == NFS3_OK:
        t.fail_support("REMOVE FAILED:  File [%] still exists." % test_file)
    
###### Other variations:
### verify removing a file that was written to
###     ... different params
###     ... different file types
###     ... directories (even though))
