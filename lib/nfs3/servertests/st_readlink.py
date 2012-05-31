from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3ReadLink(t, env):
    """ Create a symlink to a file and read the link via the READLINK rpc 

        
    FLAGS: nfsv3 readlink all
    DEPEND:
    CODE: RDLINK1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    test_link=t.name + "_link_1"
    mount_path='/' + '/'.join(env.mc.opts.path[:-1])
    link_path='/'.join([mount_path, test_dir, test_file])
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                file_mode_val=0777)
    check(res, msg="CREATE - file %s " % test_file)
    res = env.c1.symlink(test_dir_fh, test_link, mode_set=1, mode_val=0777, 
        size_set=1, size_val=len(link_path), data=link_path)
    check(res, msg="SYMLINK - link %s" % test_link)
    res = env.c1.lookup(test_dir_fh, test_link)
    check(res, msg="LOOKUP of test symlink %s" % test_link)
    test_link_fh = res.object.data
    
    ### Execution Phase ###
    res = env.c1.readlink(test_link_fh)
        
    ### Verification Phase ###
    check(res, msg="READLINK on existing file %s" % test_file)
    if res.resok.type != NF3LNK:
        t.fail_support(" ".join([
            "READLINK - data type returned [%s]" % res.resok.type,
            "does not match expected NF3LNK[%s]." % NF3LNK]))
    if res.resok.data != link_path:
        t.fail_support(" ".join([
            "READLINK - data returned [%s]" % res.resok.data,
            "does not match expected [%s]."  % link_path]))
    if len(res.resok.data) != len(link_path):
        t.fail_support(" ".join([
            "READLINK - bytes returned [%d]" % len(res.resok.data),
            "does not match expected bytes [%d]." % len(link_path)]))
    
###### Other variations:
### Linking to dir
### Linking to read-only file
### Linking to a file that user doesn't have perms on
### Link over-writting existing file
### Link over-writting existing link
### etc.
