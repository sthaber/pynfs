from nfs4.nfs4_const import *
from environment import check, checklist, checkdict, get_invalid_utf8strings
from nfs4.nfs4lib import get_bitnumattr_dict

# Test sending an invalid callback to the server.
# ISILON: This is for bug 66347, to make sure opens don't take 5 seconds
#         because they are waiting on the callback server!
def testInvalidCallback1(t, env):
    """ Invalid callback test 1

    FLAGS: all
    DEPEND:
    CODE: CALLBACK1
    """

    # Initialize an invalid callback server
    c1 = env.c1
    c1.init_connection(cb_ident=0, cb_raddr="1.1.1.1.0.0")

    # Create a file
    c1.create_confirm(t.code, c1.homedir + [t.code])
