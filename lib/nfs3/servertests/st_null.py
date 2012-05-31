from nfs3.nfs3_const import *
from environment import check, homedir_fh
from nfs3.nfs3lib import *

def testNfs3Null(t, env):
    """ NFSPROC3_NULL

    FLAGS: nfsv3 all
    DEPEND:
    CODE: NULL1
    """
    ### Setup Phase ###
    mnt_fh = homedir_fh(env.mc, env.c1)
    
    ### Execution Phase ###
    res = env.c1.null()
    
    ### Verification Phase ###
    # No check needed since res = None?
