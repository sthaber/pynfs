from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *
   
def testNfs3SetAttr(t, env):
    """ Set the attributes of a file via the SETATTR rpc 
        and verify they change correctly 

    FLAGS: nfsv3 setattr all
    DEPEND:
    CODE: SATTR1
    """
    ### Setup Phase ###
    test_file=t.name + "_file_1"
    test_dir=t.name + "_dir_1"
    mnt_fh = homedir_fh(env.mc, env.c1)
    old_mode=0777
    new_mode=0755
    old_size=111
    new_size=333
    
    res = env.c1.mkdir(mnt_fh, test_dir, dir_mode_set=1, dir_mode_val=0777)
    check(res, msg="MKDIR - %s" % test_dir)
    test_dir_fh = res.resok.obj.handle.data
    res = env.c1.create(test_dir_fh, test_file, 
                        file_mode_set=1, file_mode_val=old_mode, 
                        size_set=1, size_val=old_size)
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    res = env.c1.getattr(test_file_fh)
    check(res, msg="GETATTR - file %s" % test_file)
    if res.attributes.size != old_size:
        t.fail_support(" ".join([
            "GETATTR - Initial file size [%s]" % res.attributes.size,
            "does not match specified value [%s]" % old_size]))
    if res.attributes.mode != old_mode:
        t.fail_support(" ".join([
            "GETATTR - Initial file mode [%s]" % res.attributes.mode, 
            "does not match specified value [%s]" % old_mode]))
    
    ### Execution Phase ###
    res = env.c1.setattr(test_file_fh, 
                         mode_set=1, mode_val=new_mode, 
                         size_set=1, size_val=new_size)
    
    ### Verification Phase ###
    check(res, msg="SETATTR - file %s" % test_file)
    if res.wcc.after.attributes.mode != new_mode:
        t.fail_support(" ".join([
            "SETATTR - mode value [%s]" % res.wcc.after.attributes.mode, 
            "does not match specified value [%s]" % new_mode]))
    if res.wcc.after.attributes.size != new_size:
        t.fail_support(" ".join([
            "SETATTR - size attr value [%s]" % res.wcc.after.attributes.size,
            "does not match specified value [%s]" % new_size]))

 
### Expand to cover each attr change

