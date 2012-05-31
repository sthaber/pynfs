from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3MkNod(t, env):
    """Create a special device file via the MKNOD rpc.
        ... requires nfs root user to be mapped to root instead of nobody
        
    FLAGS: nfsv3 mknod all
    DEPEND:
    CODE: MKNOD1
    """
    ### Setup Phase ###
    test_dir=t.name + "_dir_1"
    type_list = [NF3BLK, NF3CHR, NF3SOCK, NF3FIFO]
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR of new test dir %s" % test_dir)
    res = env.c1.lookup(mnt_fh, test_dir)
    check(res, msg="LOOKUP of new dir %s" % test_dir)
    test_dir_fh = res.object.data
    
    ### Execution Phase ###
    for type in type_list:
        # remove mode_set and _val args once bug #76982 is closed
        test_file = "".join([t.name, "_", ftype3[type]])
        #test_file = "".join([mount_path, "/", test_dir, "/", t.name, "_", ftype3[type], "/"])
        res = env.c1.mknod(test_dir_fh, test_file, type, mode_set=1, mode_val=0777)
        #res = env.c1.mknod(mnt_fh, test_file, type, mode_set=1, mode_val=0777)
        check(res, msg="MKNOD of test file %s" % test_file)
    
    ### Verification Phase ###
    for type in type_list:
        test_file = "".join([t.name, "_", ftype3[type]])
        res = env.c1.lookup(test_dir_fh, test_file)
        #res = env.c1.lookup(mnt_fh, test_file)
        check(res, msg="LOOKUP test file %s" % test_file)
        

### Variations:
#    Overwrite existing file
#    Overwrite existing dir
#    Overwrite file without permissions
#    Overwrite non-empty
