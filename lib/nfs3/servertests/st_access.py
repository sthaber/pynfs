from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Access_Read(t, env):
    """ Create a file, and check access permissions with ACCESS rpc 
        
    FLAGS: nfsv3 access all
    DEPEND:
    CODE: ACCESS1
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
    check(res, msg="CREATE - file %s" % test_file)
    test_file_fh = res.resok.obj.handle.data
    
    ### Execution Phase ###
    res = env.c1.access(test_file_fh, ACCESS3_READ)
    
    ### Verification Phase ###
    check(res, msg="ACCESS - file %s" % test_file)
    if res.resok.access != ACCESS3_READ:
        t.fail_support(" ".join([
            "ACCESS - response: access bit mask [%s]" % res.resok.access,
            "is not the correct value [%s]" % ACCESS3_READ]))

### Add test cases for:
# ACCESS3_LOOKUP = 0x0002
# ACCESS3_MODIFY = 0x0004
# ACCESS3_EXTEND = 0x0008
# ACCESS3_DELETE = 0x0010
# ACCESS3_EXECUTE = 0x0020
### ToDo: Add basic negative cases.  Beef up coverage
