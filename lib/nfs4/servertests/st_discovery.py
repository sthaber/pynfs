from nfs4.nfs4_const import *
from environment import check, checklist, checkdict, get_invalid_utf8strings
from nfs4.nfs4lib import get_bitnumattr_dict
import os
import time

# XXX The following tests are not normal tests that fail or succeed - they are
# meant to be run as helper functionality, for example, to create state on an
# nfsv4 server before checking that state locally on the server.

# XXX If I dont hide this test, it will run in Andrew's tests...
def testDiscoveryOpen(t, env):
    """ DISCOVERY - Open a file, sleep, test the open.
                    Example where this can be used: nfsrevoke
    FLAGS: discovery timed
    DEPEND: INIT OPEN25 MULTICONN
    CODE: DISCOVERY1
    """

    c = env.c1
    c.init_connection()
    c2 = env.get_and_init_secondconn(c)

    fh, stateid = c.create_confirm(t.code, deny=OPEN4_SHARE_DENY_BOTH)
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, NFS4ERR_SHARE_DENIED, msg="Second OPEN should be denied")

    # During this sleep, things like "nfsrevoke" can be tried.
    time.sleep(15)

    # If nothing happened during the sleep, second open should still be denied
    res = c2.open_file(t.code, access=OPEN4_SHARE_ACCESS_WRITE)
    check(res, NFS4ERR_SHARE_DENIED, msg="Second OPEN should be denied")

def testInvestigate(t, env):
    """A simple test to print out various server information

    FLAGS: all
    DEPEND:
    CODE: GETSERVERINFO
    """
    # track ACL support types for comparison of aclsupport mask returned by server
    acl_support_types = [ACL4_SUPPORT_ALLOW_ACL, ACL4_SUPPORT_DENY_ACL,
        ACL4_SUPPORT_AUDIT_ACL, ACL4_SUPPORT_ALARM_ACL]
    # track ACL names for printing in test results
    ace_type_names = ["ACE4_ACCESS_ALLOWED_ACE_TYPE",
        "ACE4_ACCESS_DENIED_ACE_TYPE", "ACE4_SYSTEM_AUDIT_ACE_TYPE",
        "ACE4_SYSTEM_ALARM_ACE_TYPE"]

    c = env.c1
    c.init_connection()

    # Get lease time
    lease = c.getLeaseTime()
    print "Lease time = ", lease

    # Get supported Attributes
    attrs = c.supportedAttrs()
    for attr in [attr for attr in env.attr_info if attr.readable]:
        if attrs & attr.mask:
            print "Attr supported: %s" % (attr.name)

            # Filehandle is causing problems vs Solaris
            if attr.name != "filehandle":
                attrval = c.do_getattr(attr.bitnum, c.homedir)
                print "\t", attrval
        else:
            print "Attr NOT supported: %s" % (attr.name)
