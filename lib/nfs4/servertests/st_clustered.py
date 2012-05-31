from nfs4.nfs4_const import *
from environment import check, checklist, checkdict, get_invalid_utf8strings
from nfs4.nfs4lib import get_bitnumattr_dict
import os
import time

# Any test that uses the "--secondserver" parameter should depend on this test
def testSecondServer(t, env):
    """ SECONDSERVER1 - Tests the "--secondserver" parameter

    FLAGS: clustered
    DEPEND:
    CODE: SECONDSERV1
    """

    if not env.opts.secondserver:
        t.fail("SECONDSERV1 test being skipped: Second server not defined!")

    c1 = env.c1
    c1.init_connection()

    # XXX Using c1node2 here can cause problems when passing in the same server
    # for secondserver as the first server.
    c3node2 = env.c3node2
    c3node2.init_connection()

    # Use the second server: create, close and remove the file.
    print "creating/removing on second server"
    fh1, stateid1 = c3node2.create_confirm(t.code, c3node2.homedir + [t.code])
    res = c3node2.close_file(t.code, fh1, stateid1)
    check(res)
    res = c3node2.remove_obj(c3node2.homedir, t.code)
    check(res)

    # Create/close a file from connection 1
    print "creating on first server"
    fh1, stateid1 = c1.create_confirm(t.code, c1.homedir + [t.code])
    res = c1.close_file(t.code, fh1, stateid1)
    check(res)

    # Remove the file from connection 2
    print "removing on second server"
    res = c3node2.remove_obj(c3node2.homedir, t.code)
    check(res)

# Test MULTICONN
def testMulticonn(t, env):
    """Test MULTICONN support

    FLAGS: multiconn
    DEPEND: MKFILE
    CODE: MULTICONN
    """
    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)
    file_obj = c.homedir + [t.code]

    # Create and close the file on first connection
    fh, stateid = c.create_confirm(t.code, file_obj,
                                   access=OPEN4_SHARE_ACCESS_BOTH,
                                   deny=OPEN4_SHARE_DENY_NONE)
    res = c.close_file(t.code, fh, stateid)
    check(res)

    # Remove file on second connection
    res = c2.remove_obj(c2.homedir, t.code)
    check(res)

def testDisconnect1(t, env):
    """DISCONNECT - setclientid, disconnect and then try to confirm the
    setclientid

    FLAGS: disconnect timed all
    DEPEND: INIT
    CODE: DISCONN1 
    """
    cid1 = 'pynfs%i_%s_1' % (os.getpid(), t.code)

    # Setclientid
    c = env.c1
    res = c.compound([c.setclientid(cid1)])
    check(res)
    clientid = res.resarray[0].switch.switch.clientid
    confirm = res.resarray[0].switch.switch.setclientid_confirm

    # Disconnect
    c.reconnect()
    sleeptime = c.getLeaseTime() * 3 / 2
    env.sleep(sleeptime)

    # Try to confirm the first setclientid
    res = c.compound([c.setclientid_confirm_op(clientid, confirm)])
    check(res, NFS4ERR_STALE_CLIENTID, msg="Reconnect did not invalidate setclientid")

def testDisconnect2(t, env):
    """DISCONNECT - Open a file with share mode, then disconnect. Should be
    able to open the file again, if disconnect causes lease expiration.

    FLAGS: multiconn disconnect timed all
    DEPEND: INIT OPEN25 MULTICONN
    CODE: DISCONN2
    """
    cid1 = 'pynfs%i_%s_1' % (os.getpid(), t.code)
    cid2 = 'pynfs%i_%s_2' % (os.getpid(), t.code)

    c = env.c1
    c.init_connection(id=cid1)
    c2 = env.get_and_init_secondconn(c)

    # Open file once, make sure it can't be opened twice
    fh, stateid = c.create_confirm(t.code, deny=OPEN4_SHARE_DENY_BOTH)
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, NFS4ERR_SHARE_DENIED,
          "Second OPEN should be denied")

    # Disconnect from connection 1
    c.reconnect()
    sleeptime = c.getLeaseTime() * 3 / 2
    env.sleep(sleeptime)

    # Open file again - should work
    c2.init_connection(id=cid2)
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, msg="Reconnect did not expire leased data.")

def testDisconnect3(t, env):
    """DISCONNECT - Very similar to testDisconnect2, but with multiple
                    confirmed clientids. Register several clientids and open a
                    file with the middle one. Then disconnect and be able to
                    open the file again, if disconnect causes lease expiration.

    FLAGS: multiconn disconnect timed all
    DEPEND: INIT DISCONN2 MULTICONN
    CODE: DISCONN3
    """
    cid1 = 'pynfs%i_%s_1' % (os.getpid(), t.code)
    cid2 = 'pynfs%i_%s_2' % (os.getpid(), t.code)
    cid3 = 'pynfs%i_%s_3' % (os.getpid(), t.code)
    cid4 = 'pynfs%i_%s_4' % (os.getpid(), t.code)
    cid5 = 'pynfs%i_%s_5' % (os.getpid(), t.code)
    cid6 = 'pynfs%i_%s_6' % (os.getpid(), t.code)

    c = env.c1
    c2 = env.get_and_init_secondconn(c)

    c.init_connection(id=cid1)
    c.init_connection(id=cid2)
    c.init_connection(id=cid3)

    # Open file once, make sure it can't be opened twice
    fh, stateid = c.create_confirm(t.code, deny=OPEN4_SHARE_DENY_BOTH)
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, NFS4ERR_SHARE_DENIED,
          "Second OPEN should be denied")

    # Register a few more clientids
    c.init_connection(id=cid4)
    c.init_connection(id=cid5)

    # Check that the open is still denied
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, NFS4ERR_SHARE_DENIED,
          "Second OPEN should be denied")

    # Disconnect from connection 1
    c.reconnect()
    sleeptime = c.getLeaseTime() * 3 / 2
    env.sleep(sleeptime)

    # Open file again - should work
    c2.init_connection(id=cid6)
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, msg="Reconnect did not expire leased data.")
