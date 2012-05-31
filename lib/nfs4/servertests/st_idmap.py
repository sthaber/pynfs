from nfs4.nfs4_const import *
from environment import check, checklist, checkvalid, get_invalid_utf8strings
from nfs4.nfs4lib import bitmap2list, dict2fattr, get_attrbitnum_dict
from nfs4.nfs4_type import nfstime4, settime4, nfsace4

# TODO The SGID and SOWNID tests currently assume the server's NFSv4 domain is
# "localdomain", but this could be an option passed in when running the tests.

def _setacl(c, path, acl, set_acl_exp=NFS4_OK):
    ops = c.use_obj(path)
    acl_attr_bitnum = get_attrbitnum_dict()['acl']
    # set passed in ace on file
    setaclops = ops + [c.setattr({acl_attr_bitnum: acl})]
    set_res = c.compound(setaclops)
    # check result
    check(set_res, set_acl_exp, "SETATTR: Could not set ACE: %s" % (acl))

def _admin_chownerorgrp(env, path, attr, newval):
    c4 = env.c4
    c4.init_connection()
    baseops = c4.use_obj(path)
    attr_bitnum = get_attrbitnum_dict()[attr]
    ops = baseops + [c4.setattr({attr_bitnum: newval})]
    res = c4.compound(ops)
    check(res, NFS4_OK,
                  "SETATTR did not support changing %s attribute" % (attr))

def testInvalidName(t, env):
    """ Test setting an ACL with an invalid name

    FLAGS: idmap setattr file acl all
    CODE: SETID1
    """
    c = env.c1
    c.init_connection()
    c.create_confirm(t.code)
    path = c.homedir + [t.code]
    # First ace is for test, second for cleanup
    acl = [nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_WRITE_OWNER, "baduser@baddomain"),
           nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@")]
    _setacl(c, path, acl, NFS4ERR_BADOWNER)

def testChangeGrpWithGid(t, env):
    """SETGROUP using GID

    FLAGS: idmap setattr file all
    CODE: SGID
    """
    c = env.c1
    c.init_connection()
    c.create_confirm(t.code)
    path = c.homedir + [t.code]
    # First ace is for test, second for cleanup
    acl = [nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_WRITE_OWNER, "admin@localdomain"),
           nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@")]
    _setacl(c, path, acl)
    _admin_chownerorgrp(env, path, 'owner_group', '1111')

def testChangeOwnerWithUid(t, env):
    """SETOWN using UID

    FLAGS: idmap setattr file all
    CODE: SOWNID
    """
    c = env.c1
    c.init_connection()
    c.create_confirm(t.code)
    path = c.homedir + [t.code]
    # First ace is for test, second for cleanup
    acl = [nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_WRITE_OWNER, "admin@localdomain"),
           nfsace4(ACE4_ACCESS_ALLOWED_ACE_TYPE, 0, ACE4_GENERIC_WRITE, "EVERYONE@")]
    _setacl(c, path, acl)
    _admin_chownerorgrp(env, path, 'owner', '10')
