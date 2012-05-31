from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3SymLink(t, env):
    """ Create a symlink to a file via the SYMLINK rpc 
       
    
    FLAGS: nfsv3 symlink all
    DEPEND:
    CODE: SLINK1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    test_link=t.name + "_link_1"
    mount_path='/' + '/'.join(env.mc.opts.path[:-1])
    link_path='/'.join([mount_path, test_dir, test_file])
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - dir %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, file_mode_set=1, 
                        file_mode_val=0777)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    # once bug 76982 is closed, drop the mode arguments
    res = env.c1.symlink(test_dir_fh, test_link, mode_set=1, mode_val=0777, 
        size_set=1, size_val=len(link_path), data=link_path)
        
    ### Verification Phase ###
    check(res, msg="SYMLINK - link %s" % test_link)
    res = env.c1.lookup(test_dir_fh, test_link)
    check(res, msg="LOOKUP - link %s" % test_link)
    if res.status != NFS3_OK:
        t.fail_support("SYMLINK FAILED:  File [%] still exists." % test_link)


### Variations:
#    see hardlink (LINK) variations
#    create symlinks with different perms/groups/owners?
