from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Rename(t, env):
    """ Rename a file with the RENAME rpc 
    
    
    FLAGS: nfsv3 rename all
    DEPEND:
    CODE: RENAME1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    new_test_file=test_file + "_renamed"
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    
    ### Execution Phase ###
    res = env.c1.rename(test_dir_fh, test_file, test_dir_fh, new_test_file)
    
    ### Verification Phase ###
    check_msg="RENAME - file %s" % test_file
    check(res, msg=check_msg)
    res = env.c1.lookup(test_dir_fh, new_test_file)
    check(res, msg="LOOKUP - file %s" % new_test_file)
    if res.status != NFS3_OK:
        t.fail_support("RENAME FAILED: File [%s] does not exist." \
                       % new_test_file)
    
    #ToDo: Add negative LOOKUP call to verify old file/dir is gone 
    
###### Other variations:
### Rename dir
### Rename non-existant file
### Rename over existing file
### Rename without permissions
### Rename over existing file without permissions on the target file
