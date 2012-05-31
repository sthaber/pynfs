from nfs4.nfs4_const import *
from environment import check, checklist, checkvalid, get_invalid_utf8strings
from nfs4.nfs4lib import bitmap2list, dict2fattr, get_attrbitnum_dict
from nfs4.nfs4_type import nfstime4, settime4, nfsace4
import re

def compare_acl(acl1, acl2):
    """ compare_acl(acl1(list), acl2(list)): 
        Compares two sets of access control lists (lists of nfsace4 objects) 
        to determine if they are equal. Returns True if equal, False if not. 
    """

    if len(acl1) != len(acl2):
        # ACL's don't match in length, return False
        return False

    # iterate over aces and run comparison
    for ace1, ace2 in zip(acl1, acl2):
        # compare arguments of the two aces
        if ((cmp(ace1.type, ace2.type) | cmp(ace1.flag, ace2.flag) | cmp(ace1.access_mask, ace2.access_mask) | 
               cmp(ace1.who, ace2.who)) != 0):

            # found an two ACEs that don't match, return False
            return False

    return True

def validate_op(t, env, file_obj, verbose=0, **kwargs):
    """ validate_op(t, env, file_obj(list), verbose(boolean), **kwargs): 
        A flexible validation function, that can be passed several types of
        test arguments and expected values, for example:
            test_open_write=NFS4_OK
        this instructs the function to test opening a file for write and
        expect to get returned NFS4_OK, failing if otherwise. 
    """

    # parse key to determine if command has client indicator
    for key, expected in kwargs.iteritems():
        client = env.c1
        client_name = "c1"

        # attempt to pull a client name off the operation
        match = re.match('(c(?:1|2))_(.+)', key)

        # if we have a match, isolate out the client and op
        if match != None:
            if   match.groups()[0] == 'c1':
                client = env.c1
                client_name = "c1"
            elif match.groups()[0] == 'c2':
                client = env.c2
                client_name = "c2"

            op = match.groups()[1]
        else:
            # if we don't match, define op as the orig key
            op = key

        # test OPEN WRITE and assert status 
        if (op == "test_open_write"):
            # perform open with correct share mode
            res = client.open_file(file_obj[-1], 
                access=OPEN4_SHARE_ACCESS_WRITE, deny=OPEN4_SHARE_DENY_NONE)
            check(res, expected, "Validate_OP (%s) NFS4 OPEN ACCESS WRITE"  % (client_name))

            if verbose:
                print "Validate_OP (%s) NFS4 OPEN ACCESS WRITE received %s as expected" % (client_name, res.status)

            if (expected == NFS4_OK):
                (fh, stateid) = client.confirm(file_obj[-1], res)

                # attempt write
                res = client.write_file(file_obj, "1"*1000, stateid=stateid)
                check(res, expected, "Validate_OP (%s) NFS4 WRITE OP" % (client_name))

                if verbose:
                    print "Validate_OP (%s) NFS4 WRITE OP received %s as expected" % (client_name, res.status)

                client.close_file(file_obj[-1], fh, stateid)

        # test OPEN READ and assert status 
        if (op =="test_open_read"):
            # get our expected assert status (for example NFS4_OK)
            res = client.open_file(file_obj[-1], 
                access=OPEN4_SHARE_ACCESS_READ, deny=OPEN4_SHARE_DENY_NONE)
            check(res, expected, "Validate_OP (%s) NFS4 OPEN ACCESS READ" % (client_name))

            if verbose:
                print "Validate_OP (%s) NFS4 OPEN ACCESS READ received %s as expected" % (client_name, res.status)

            if (expected == NFS4_OK):
                (fh, stateid) = client.confirm(file_obj[-1], res)

                # attempt write
                res = client.read_file(file_obj, stateid=stateid)
                check(res, expected, "Validate_OP (%s) NFS4 READ OP" % (client_name))

                if verbose:
                    print "Validate_OP (%s) NFS4 READ OP received %s as expected" % (client_name, res.status)

                client.close_file(file_obj[-1], fh, stateid)

        # test DIRECT WRITE and assert status 
        if (op == "test_direct_write"):
            res = client.write_file(file_obj, "1"*1000)
            check(res, expected, "Validate_OP (%s) NFS4 DIRECT WRITE OP" % (client_name))

            if verbose:
                print "Validate_OP (%s) NFS4 DIRECT WRITE OP received %s as expected" % (client_name, res.status)

        # test DIRECT READ and assert status 
        if (op == "test_direct_read"):
            res = client.read_file(file_obj)
            check(res, expected, "Validate_OP (%s) NFS4 DIRECT READ OP" % (client_name))

            if verbose:
                print "Validate_OP (%s) NFS4 DIRECT READ OP received %s as expected" % (client_name, res.status)

def acl_test(t, env, testname, acl, file_type="file", **kwargs):
    """ acl_test(t, env, testname(string), acl(list), filetype=(string), 
            **kwargs): 
        A generic wrapper for running an acl test, allowing flexible
        definition of tests by a single function call. The test wrapper
        attempts to round-trip a specific acl and then calls validates
        the ACL by running tests dependent on the remaining **kwargs.
    """
    c1 = env.c1
    c1.init_connection()

    c2 = env.c2
    c2.init_connection()

    file_name = t.code + testname
    file_obj = c1.homedir + [file_name]

    if file_type == "file":
        fh, stateid = c1.create_confirm(file_name,
            access=OPEN4_SHARE_ACCESS_BOTH, deny=OPEN4_SHARE_DENY_NONE,
            mode=GUARDED4)
    else:
        dir_res = c1.create_obj(file_name, type=NF4DIR)
        check(dir_res, NFS4_OK, "Error creating file %s" % (t.code))

    # round trip the ACL
    set_acl_round_trip(file_obj, c1, acl)

    if file_type == "file":
        res = c1.close_file(file_name, fh, stateid)
        check(res, NFS4_OK, "Error closing file %s" % (t.code))

        # FIXME: validate_op only tests file ops currently
        validate_op(t, env, file_obj, **kwargs)

def set_acl_round_trip(file_obj, client, acl, set_acl_exp=NFS4_OK, get_acl_exp=NFS4_OK, compare=True):
    """ set_acl_round_trip(file_obj(list), client, acl, set_acl_exp=NFS4_OK, 
            get_acl_exp=NFS4_OK, compare=True):
        Sets a specific ACL on a file (can be directory as well) and then
        attempts to round trip it via SETATTR and GETATTR and then compares
        the original and final ACL to validate they are equal.
    """
    # if given an argument that is not a list, set it to be a list
    if type(acl) != type(list()):
        acl = [acl]
    
    baseops = client.use_obj(file_obj)
    acl_attr_bitnum = get_attrbitnum_dict()['acl']

    # set passed in ace on file
    setaclops = baseops + [client.setattr({acl_attr_bitnum: acl})] 
    set_res = client.compound(setaclops)
    
    # check result 
    check(set_res, set_acl_exp, "SETATTR: Could not set ACE: %s" % (acl))
    
    # get back set ace  
    getaclops = baseops + [client.getattr({acl_attr_bitnum: acl})]

    get_res = client.compound(getaclops)
    
    check(get_res, get_acl_exp, "GETATTR: Could not get ACE: %s" % (acl))
    
    # pull the ace from the server out of the response
    get_res_acl = get_res.resarray[-1].obj_attributes[acl_attr_bitnum]

    # compare the source ace and result ace
    if compare:
        checkvalid(compare_acl(acl, get_res_acl), 
            "SETATTR ACL: Source ACE (%s) and returned ACE (%s) do not match!" % (acl, get_res_acl))

def ace_type_to_str(ace_type):
    ace_type_map = {ACE4_ACCESS_ALLOWED_ACE_TYPE:"ACE4_ACCESS_ALLOWED_ACE_TYPE",
        ACE4_ACCESS_DENIED_ACE_TYPE:"ACE4_ACCESS_DENIED_ACE_TYPE", 
        ACE4_SYSTEM_AUDIT_ACE_TYPE:"ACE4_SYSTEM_AUDIT_ACE_TYPE",
        ACE4_SYSTEM_ALARM_ACE_TYPE:"ACE4_SYSTEM_ALARM_ACE_TYPE"}

    return ace_type_map[ace_type]

def ace_flag_to_str(ace_flag):
    ace_flag_map = {0:"NOFLAG", ACE4_FILE_INHERIT_ACE:"ACE4_FILE_INHERIT_ACE", 
        ACE4_DIRECTORY_INHERIT_ACE:"ACE4_DIRECTORY_INHERIT_ACE", 
        ACE4_NO_PROPAGATE_INHERIT_ACE:"ACE4_NO_PROPAGATE_INHERIT_ACE", 
        ACE4_INHERIT_ONLY_ACE:"ACE4_INHERIT_ONLY_ACE", 
        ACE4_SUCCESSFUL_ACCESS_ACE_FLAG:"ACE4_SUCCESSFUL_ACCESS_ACE_FLAG", 
        ACE4_FAILED_ACCESS_ACE_FLAG:"ACE4_FAILED_ACCESS_ACE_FLAG", 
        ACE4_IDENTIFIER_GROUP:"ACE4_IDENTIFIER_GROUP"}

    return ace_flag_map[ace_flag]

def ace_mode_to_str(file_type, access_mode):
    access_modes_file_map = { ACE4_READ_DATA:"ACE4_READ_DATA", 
        ACE4_WRITE_DATA:"ACE4_WRITE_DATA", ACE4_APPEND_DATA:"ACE4_APPEND_DATA"}

    access_modes_dir_map = { ACE4_LIST_DIRECTORY:"ACE4_LIST_DIRECTORY", 
        ACE4_ADD_FILE:"ACE4_ADD_FILE", ACE4_ADD_SUBDIRECTORY:"ACE4_ADD_SUBDIRECTORY"}

    access_modes_generic_map = { ACE4_READ_NAMED_ATTRS:"ACE4_READ_NAMED_ATTRS", 
        ACE4_WRITE_NAMED_ATTRS:"ACE4_WRITE_NAMED_ATTRS", ACE4_EXECUTE:"ACE4_EXECUTE", ACE4_DELETE_CHILD:"ACE4_DELETE_CHILD", 
        ACE4_READ_ATTRIBUTES:"ACE4_READ_ATTRIBUTES", ACE4_WRITE_ATTRIBUTES:"ACE4_WRITE_ATTRIBUTES", ACE4_DELETE:"ACE4_DELETE", 
        ACE4_READ_ACL:"ACE4_READ_ACL", ACE4_WRITE_ACL:"ACE4_WRITE_ACL", ACE4_WRITE_OWNER:"ACE4_WRITE_OWNER", 
        ACE4_SYNCHRONIZE:"ACE4_SYNCHRONIZE", ACE4_GENERIC_READ:"ACE4_GENERIC_READ", ACE4_GENERIC_WRITE:"ACE4_GENERIC_WRITE", 
        ACE4_GENERIC_EXECUTE:"ACE4_GENERIC_EXECUTE"}

    if file_type == "file":
        access_modes_file_map.update(access_modes_generic_map)
        return access_modes_file_map[access_mode]
    else:
        access_modes_dir_map.update(access_modes_generic_map)
        return access_modes_dir_map[access_mode]

def check_res(t, c, res, file, dict):
    modified = bitmap2list(res.resarray[-1].attrsset)
    for attr in modified:
        if attr not in dict:
            t.fail("attrsset contained %s, which was not requested" %
                   get_bitnumattr_dict()[attr])
    newdict = c.do_getattrdict(file, dict.keys())
    if newdict != dict:
        t.fail("Set attrs %s not equal to got attrs %s" % (dict, newdict))

########################################

### Special Identity tests
def testACLOwnerDenyRead(t, env):
    """SETACL OWNER@ deny read

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1odr
    """
    acl_test(t, env, "owner_deny_read", 
        nfsace4(ACE4_ACCESS_DENIED_ACE_TYPE, 0, ACE4_GENERIC_READ, "OWNER@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4ERR_ACCESS, 
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLOwnerAllowRead(t, env):
    """SETACL OWNER@ allow read

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1oar
    """
    acl_test(t, env, "owner_allow_read",
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_READ, "OWNER@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4_OK,
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLOwnerDenyWrite(t, env):
    """SETACL OWNER@ deny write

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1odw
    """
    acl_test(t, env, "owner_deny_write",
        nfsace4(ACE4_ACCESS_DENIED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "OWNER@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4ERR_ACCESS,
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLOwnerAllowWrite(t, env):
    """SETACL OWNER@ deny write

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1oaw
    """
    acl_test(t, env, "owner_allow_write",
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "OWNER@"),
        test_open_write=NFS4_OK, test_open_read=NFS4ERR_ACCESS,
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLEveryoneDenyRead(t, env):
    """SETACL EVERYONE@ deny read

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1edr
    """
    acl_test(t, env, "everyone_deny_read", 
        nfsace4(ACE4_ACCESS_DENIED_ACE_TYPE, 0, ACE4_GENERIC_READ, "EVERYONE@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4ERR_ACCESS, 
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLEveryoneAllowRead(t, env):
    """SETACL EVERYONE@ allow read

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1ear
    """
    acl_test(t, env, "everyone_allow_read",
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_READ, "EVERYONE@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4_OK,
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4_OK)

def testACLEveryoneDenyWrite(t, env):
    """SETACL EVERYONE@ deny write

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1edw
    """
    acl_test(t, env, "everyone_deny_write",
        nfsace4(ACE4_ACCESS_DENIED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@"),
        test_open_write=NFS4ERR_ACCESS, test_open_read=NFS4ERR_ACCESS,
        c2_test_open_write=NFS4ERR_ACCESS, c2_test_open_read=NFS4ERR_ACCESS)

def testACLEveryoneAllowWrite(t, env):
    """SETACL EVERYONE@ deny write

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1eaw
    """
    acl_test(t, env, "everyone_allow_write",
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@"),
        test_open_write=NFS4_OK, test_open_read=NFS4ERR_ACCESS,
        c2_test_open_write=NFS4_OK, c2_test_open_read=NFS4ERR_ACCESS)

def testACLMultipleACE(t, env):
    """SETACL EVERYONE@ deny write

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL1ma
    """
    acl_test(t, env, "",
        [nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@"),
         nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_READ, "OWNER@")],
        test_open_write=NFS4_OK, test_open_read=NFS4_OK,
        c2_test_open_write=NFS4_OK, c2_test_open_read=NFS4ERR_ACCESS)

def testACLDirectAccess(t, env):
    """SETATTR OWNER@ and verify prevention of direct write/read

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL2
    """

    c = env.c1
    c.init_connection()
    filename = c.homedir + ["acl_direct_access"]
    # we initially create the file 666 to make sure it's the ACL that is
    # restricting access
    fh1, stateid1 = c.create_confirm('owner1', filename, attrs={FATTR4_MODE: 0666},
        access=OPEN4_SHARE_ACCESS_BOTH, deny=OPEN4_SHARE_DENY_NONE, mode=GUARDED4)

    # create a new connection to do the access as someone else
    # to make sure we're not hitting the owner_override case
    c2 = env.c2
    c2.init_connection()

    res = c2.write_file(filename, "1"*1000)
    check(res, NFS4_OK, "NFS4 Direct Write Op without ACL")
    res = c2.read_file(filename)
    check(res, NFS4_OK, "NFS4 Direct Read Op without ACL")

    set_acl_round_trip(filename, c,
        nfsace4(ACE4_ACCESS_DENIED_ACE_TYPE, 0, ACE4_READ_DATA | ACE4_WRITE_DATA,
                "EVERYONE@"))

    res = c2.write_file(filename, "1"*1000)
    check(res, NFS4ERR_ACCESS, "NFS4 Direct Write Op with ACL")
    res = c2.read_file(filename)
    check(res, NFS4ERR_ACCESS, "NFS4 Direct Read Op with ACL")


### Variable tests

def testACLTypes(t, env):
    """SETATTR all supported and unsupported ACL Types and verify correct response

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL3
    """
    c = env.c1
    c.init_connection()
    file_obj = c.homedir + [t.code]

    # track ACL support types for comparison of aclsupport mask returned by server
    acl_support_types = [ACL4_SUPPORT_ALLOW_ACL, ACL4_SUPPORT_DENY_ACL, ACL4_SUPPORT_AUDIT_ACL,
        ACL4_SUPPORT_ALARM_ACL]

    # track all ACL types for test
    ace_types = [ACE4_ACCESS_ALLOWED_ACE_TYPE, ACE4_ACCESS_DENIED_ACE_TYPE, ACE4_SYSTEM_AUDIT_ACE_TYPE,
        ACE4_SYSTEM_ALARM_ACE_TYPE]

    # track ACL names for printing in test results
    ace_type_names = ["ACE4_ACCESS_ALLOWED_ACE_TYPE", "ACE4_ACCESS_DENIED_ACE_TYPE", "ACE4_SYSTEM_AUDIT_ACE_TYPE",
        "ACE4_SYSTEM_ALARM_ACE_TYPE"]

    # get supported acl type mask from server
    supported = c.supportedACLTypes()

    fh, stateid = c.create_confirm(t.code)

    for index in range(0, len(acl_support_types)):
        if supported & acl_support_types[index]:
            print "Testing supported ACL type: %s" % (ace_type_names[index])

            set_acl_round_trip(file_obj, c,
                [nfsace4(ace_types[index], 0, ACE4_READ_DATA, "OWNER@")],
                set_acl_exp=NFS4_OK)
        else:
            print "Testing unsupported ACL type: %s" % (ace_type_names[index])

            set_acl_round_trip(file_obj, c, 
                [nfsace4(ace_types[index], 0, ACE4_READ_DATA, "OWNER@")],
                set_acl_exp=NFS4ERR_ATTRNOTSUPP, compare=False)
 
def testACLEnumRountTrip(t, env):
    """SETATTR all supported ACL Types

    FLAGS: acls file all
    DEPEND: MKFILE
    CODE: SETACL4
    """
    c = env.c1
    c.init_connection()
    rtfail = 0

    # track ACL support types for comparison of aclsupport mask returned by server
    acl_support_types = [ACL4_SUPPORT_ALLOW_ACL, ACL4_SUPPORT_DENY_ACL, ACL4_SUPPORT_AUDIT_ACL,
        ACL4_SUPPORT_ALARM_ACL]

    # track all ACL types for test
    ace_types = [ACE4_ACCESS_ALLOWED_ACE_TYPE, ACE4_ACCESS_DENIED_ACE_TYPE, ACE4_SYSTEM_AUDIT_ACE_TYPE,
        ACE4_SYSTEM_ALARM_ACE_TYPE]

    # track all ACL flags for test
    ace_flags = { }
    # for ALLOWED and DENIED, SUCCESSFUL_ACCESS and FAILED_ACCESS mean nothing
    # for all types, IDENTIFIER_GROUP is omitted; we only test FOO@ whos
    ace_flags[ACE4_ACCESS_ALLOWED_ACE_TYPE] = [0, ACE4_FILE_INHERIT_ACE,
        ACE4_DIRECTORY_INHERIT_ACE, ACE4_NO_PROPAGATE_INHERIT_ACE,
        ACE4_INHERIT_ONLY_ACE]
    ace_flags[ACE4_ACCESS_DENIED_ACE_TYPE] = [0, ACE4_FILE_INHERIT_ACE,
        ACE4_DIRECTORY_INHERIT_ACE, ACE4_NO_PROPAGATE_INHERIT_ACE,
        ACE4_INHERIT_ONLY_ACE]

    # AUDIT and ALARM currently omit nothing because they're not even
    # supported and are therefore dead code; if we add support then
    # we'll need to review which values to include
    ace_flags[ACE4_SYSTEM_AUDIT_ACE_TYPE] = [0, ACE4_FILE_INHERIT_ACE,
        ACE4_DIRECTORY_INHERIT_ACE, ACE4_NO_PROPAGATE_INHERIT_ACE,
        ACE4_INHERIT_ONLY_ACE, ACE4_SUCCESSFUL_ACCESS_ACE_FLAG,
        ACE4_FAILED_ACCESS_ACE_FLAG]
    ace_flags[ACE4_SYSTEM_ALARM_ACE_TYPE] = [0, ACE4_FILE_INHERIT_ACE,
        ACE4_DIRECTORY_INHERIT_ACE, ACE4_NO_PROPAGATE_INHERIT_ACE,
        ACE4_INHERIT_ONLY_ACE, ACE4_SUCCESSFUL_ACCESS_ACE_FLAG,
        ACE4_FAILED_ACCESS_ACE_FLAG]

    # track all ACL access modes for test
    ace_access_modes = { }

    # for file we omit DELETE_CHILD since files can't have children
    ace_access_modes["file"] = [ACE4_READ_DATA, ACE4_WRITE_DATA, ACE4_APPEND_DATA,
        ACE4_READ_NAMED_ATTRS, ACE4_WRITE_NAMED_ATTRS, ACE4_EXECUTE,
        ACE4_READ_ATTRIBUTES, ACE4_WRITE_ATTRIBUTES, ACE4_DELETE, ACE4_READ_ACL,
        ACE4_WRITE_ACL, ACE4_WRITE_OWNER, ACE4_SYNCHRONIZE, ACE4_GENERIC_READ,
        ACE4_GENERIC_WRITE, ACE4_GENERIC_EXECUTE]

    # for dir we omit SYNCHRONIZE, GENERIC_READ, GENERIC_WRITE and
    # GENERIC_EXECUTE since these are inapplicable to directories
    ace_access_modes["dir"] = [ACE4_READ_DATA, ACE4_WRITE_DATA, ACE4_APPEND_DATA,
        ACE4_READ_NAMED_ATTRS, ACE4_WRITE_NAMED_ATTRS, ACE4_EXECUTE, ACE4_DELETE_CHILD, 
        ACE4_READ_ATTRIBUTES, ACE4_WRITE_ATTRIBUTES, ACE4_DELETE, ACE4_READ_ACL,
        ACE4_WRITE_ACL, ACE4_WRITE_OWNER]

    # track interesting who types for test
    ace_identities = ["OWNER@", "GROUP@", "EVERYONE@"]
#    ace_identities = ["OWNER@", "GROUP@", "EVERYONE@", "INTERACTIVE@", "NETWORK@", "DIALUP@", "BATCH@", "ANONYMOUS@",
#        "AUTHENTICATED@", "SERVICE@"]

    # get supported acl type mask from server
    supported = c.supportedACLTypes()

    for file_type in ("file", "dir"):
        # iterate over all acl support types
        for index in range(0, len(acl_support_types)):
            # only run tests on supported acl types (unsupported will surely fail)
            if supported & acl_support_types[index]:
                # iterate over all possible ace flags
                for ace_flag in ace_flags[ace_types[index]]:
                    # skip any flag tests for files since they don't apply
                    if ace_flag != 0 and file_type == "file":
                        continue

                    # iterate over all access modes
                    for access_mode in ace_access_modes[file_type]:
                        # iterate over all identities
                        for identity in ace_identities:

                            # generate a test name for presentation
                            testname = "%s_%s_%s_%s_%s" % (file_type, ace_type_to_str(ace_types[index]), 
                                ace_flag_to_str(ace_flag), ace_mode_to_str(file_type, access_mode), identity)
    
                            print "Round Tripping nfsace4(%s, %s, %s, %s) on a %s" % (ace_type_to_str(ace_types[index]), 
                                ace_flag_to_str(ace_flag), ace_mode_to_str(file_type, access_mode), identity, file_type)

                            try:
                                acl_test(t, env, testname, 
                                    [nfsace4(ace_types[index], ace_flag, access_mode, identity)],
                                    file_type=file_type, verbose=1)

                            except Exception, e:
                                rtfail += 1
                                print "--> ACLTest Exception: ", e

    # If there are any round trip failures force global test failure
    if rtfail:
        t.fail("There were %d failures in round-tripping ACEs" % (rtfail))


def testSyntheticAcl(t, env):
    """ GETATTR of an ACL on a file with no ACL
        This should return a synthetic ACL, see RFC 5661, section 6.4.2

    FLAGS: getattr file all
    DEPEND: LOOKFILE
    CODE: GATTACL
    """
    c = env.c1
    file_obj = c.homedir + [t.code]
    acl_attr_bitnum = get_attrbitnum_dict()['acl']

    # These expected values come from the Isilon synthetic ACL; if that changes
    # or ACL policy is being applied, this test may need to change.
    group_rights = every_rights = ACE4_READ_DATA + ACE4_READ_NAMED_ATTRS + \
        ACE4_READ_ATTRIBUTES + ACE4_READ_ACL + ACE4_SYNCHRONIZE
    owner_rights = group_rights + ACE4_WRITE_DATA + ACE4_APPEND_DATA + \
        ACE4_WRITE_NAMED_ATTRS + ACE4_WRITE_ATTRIBUTES + ACE4_WRITE_ACL
    acl_expected = [
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, owner_rights, "OWNER@"),
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, group_rights, "GROUP@"),
        nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, every_rights, "EVERYONE@")]

    c.create_confirm(t.code)
    ops = c.use_obj(file_obj) + [c.getattr({acl_attr_bitnum: 'acl'})]
    res = c.compound(ops)
    check(res, msg="Asking for ACL attribute")

    acl_retrieved = res.resarray[-1].opgetattr.resok4.obj_attributes[acl_attr_bitnum]
    if acl_retrieved == []:
        t.fail("ACL is empty!")
    if compare_acl(acl_retrieved, acl_expected) == False:
        t.fail("ACL does not match!")
