#!/usr/bin/env python
# nfs3lib.py - NFS3_PROTOCOL library for python

import rpc
from xdrlib import Error as XDRError
from nfs3_const import *
from nfs3_type import *
from nfs3_pack import *
import time
import struct
import socket
import sys

AuthSys = rpc.SecAuthSys(0,'jupiter',103558,100,[])

class NFS3Exception(rpc.RPCError):
    pass

#An NFS procedure returned an error
class BadNFS3Res(NFS3Exception):
    def __init__(self, errcode, msg=None):
        self.errcode = errcode
        if msg:
            self.msg = msg + ': '
        else:
            self.msg = ''
    def __str__(self):
        return self.msg + "should return NFS3_OK, instead got %s" % \
            (nfsstat3[self.errcode])

class NFS3Client(rpc.RPCClient):
    def __init__(self, id, host='localhost', port=300, homedir=['pynfs'],
            sec_list=[AuthSys], opts = None):
        self.ipv6 = getattr(opts, "ipv6", False)
        self.packer = NFS3Packer()
        self.unpacker = NFS3Unpacker('')
        self.homedir = homedir
        self.id = id
        self.opts = opts
        #uselowport = True
        uselowport = getattr(opts, "secure", False)
        rpc.RPCClient.__init__(self, host, port, program=NFS_PROGRAM,
            version=NFS_V3, sec_list=sec_list, uselowport=uselowport,ipv6=self.ipv6)
        self.server_address = (host, port)
        
    def nfs3_pack(self, procedure, data):
        p = self.packer

        ### ToDo: refactor to use a dict ... should give better perf
        if procedure == NFSPROC3_NULL:
            pass
        elif procedure == NFSPROC3_GETATTR:
            p.pack_nfs_fh3(data)
        elif procedure == NFSPROC3_SETATTR:
            p.pack_setattr3args(data)
        elif procedure == NFSPROC3_LOOKUP:
            p.pack_diropargs3(data)
        elif procedure == NFSPROC3_ACCESS:
            p.pack_access3args(data)
        elif procedure == NFSPROC3_READLINK:
            p.pack_nfs_fh3(data)
        elif procedure == NFSPROC3_READ:
            p.pack_read3args(data)
        elif procedure == NFSPROC3_WRITE:
            p.pack_write3args(data)
        elif procedure == NFSPROC3_CREATE:
            p.pack_create3args(data)
        elif procedure == NFSPROC3_MKDIR:
            p.pack_mkdir3args(data)
        elif procedure == NFSPROC3_SYMLINK:
            p.pack_symlink3args(data)
        elif procedure == NFSPROC3_MKNOD:
            p.pack_mknod3args(data)
        elif procedure == NFSPROC3_REMOVE:
            p.pack_diropargs3(data)
        elif procedure == NFSPROC3_RMDIR:
            p.pack_diropargs3(data)
        elif procedure == NFSPROC3_RENAME:
            p.pack_rename3args(data)
        elif procedure == NFSPROC3_LINK:
            p.pack_link3args(data)
        elif procedure == NFSPROC3_READDIR:
            p.pack_readdir3args(data)
        elif procedure == NFSPROC3_READDIRPLUS:
            p.pack_readdirplus3args(data)
        elif procedure == NFSPROC3_FSSTAT:
            p.pack_nfs_fh3(data)
        elif procedure == NFSPROC3_FSINFO:
            p.pack_nfs_fh3(data)
        elif procedure == NFSPROC3_PATHCONF:
            p.pack_nfs_fh3(data)
        elif procedure == NFSPROC3_COMMIT:
            p.pack_commit3args(data)
        else:
            raise XDRError, 'bad switch=%s' % procedure

    # XXX Fancy unpacking, into status, data, etc
    def nfs3_unpack(self, procedure):
        un_p = self.unpacker

        ### ToDo: refactor to use a dict ... should give better perf
        if procedure == NFSPROC3_NULL:
            return
        elif procedure == NFSPROC3_GETATTR:
            return un_p.unpack_getattr3res()
        elif procedure == NFSPROC3_SETATTR:
            return un_p.unpack_wccstat3()
        elif procedure == NFSPROC3_LOOKUP:
            return un_p.unpack_lookup3res()
        elif procedure == NFSPROC3_ACCESS:
            return un_p.unpack_access3res()
        elif procedure == NFSPROC3_READLINK:
            return un_p.unpack_readlink3res()
        elif procedure == NFSPROC3_READ:
            return un_p.unpack_read3res()
        elif procedure == NFSPROC3_WRITE:
            return un_p.unpack_write3res()
        elif procedure == NFSPROC3_CREATE:
            return un_p.unpack_diropres3()
        elif procedure == NFSPROC3_MKDIR:
            return un_p.unpack_diropres3()
        elif procedure == NFSPROC3_SYMLINK:
            return un_p.unpack_diropres3()
        elif procedure == NFSPROC3_MKNOD:
            return un_p.unpack_diropres3()
        elif procedure == NFSPROC3_REMOVE:
            return un_p.unpack_wccstat3()
        elif procedure == NFSPROC3_RMDIR:
            return un_p.unpack_wccstat3()
        elif procedure == NFSPROC3_RENAME:
            return un_p.unpack_rename3res()
        elif procedure == NFSPROC3_LINK:
            return un_p.unpack_link3res()
        elif procedure == NFSPROC3_READDIR:
            return un_p.unpack_readdir3res()
        elif procedure == NFSPROC3_READDIRPLUS:
            return un_p.unpack_readdirplus3res()
        elif procedure == NFSPROC3_FSSTAT:
            return un_p.unpack_fsstat3res()
        elif procedure == NFSPROC3_FSINFO:
            return un_p.unpack_fsinfo3res()
        elif procedure == NFSPROC3_PATHCONF:
            return un_p.unpack_pathconf3res()
        elif procedure == NFSPROC3_COMMIT:
            return un_p.unpack_commit3res()
        else:
            raise XDRError, 'bad switch=%s' % procedure

    def nfs3_call(self, procedure, data=''):
        # Pack Request
        p = self.packer
        un_p = self.unpacker
        p.reset()

        self.nfs3_pack(procedure, data)
        
        # Make Call
        res = self.call(procedure, p.get_buffer())

        # Unpack Reply
        un_p.reset(res)
        res = self.nfs3_unpack(procedure)
        un_p.done()

        # XXX Error checking?
        return res

    """
    BASIC NFS3 OPERATIONS
    """
    
    def null(self):
        return self.nfs3_call(NFSPROC3_NULL)
    
    def getattr(self, file_handle=None):
        arg_list = nfs_fh3(file_handle)
        return self.nfs3_call(NFSPROC3_GETATTR, arg_list)
    
    def setattr(self, file_handle=None, mode_set=0, mode_val=0777, 
                uid_set=0, uid_val=None, gid_set=0, gid_val=None, 
                size_set=0, size_val=0, atime_set=0, atime_val=None, 
                mtime_set=0, mtime_val=None, 
                guard_check=False, guard_time=None):
        if uid_val is None:
            uid_val = self.opts.uid
        if gid_val is None:
            gid_val = self.opts.gid
        curr_time=("%s" % time.time()).split('.')
        if atime_val is None:
            atime_val = nfstime3(curr_time[0], curr_time[1])
        if mtime_val is None:
            mtime_val = nfstime3(curr_time[0], curr_time[1])
        if guard_time is None:
            guard_time = nfstime3(curr_time[0], curr_time[1])
        arg_list = setattr3args(nfs_fh3(file_handle),
            sattr3(
                set_uint32(mode_set, mode_val),
                set_uint32(uid_set, uid_val),
                set_uint32(gid_set, gid_val), 
                set_uint64(size_set, size_val), 
                set_time(atime_set, atime_val), 
                set_time(mtime_set, mtime_val)
            ),
            sattrguard3(guard_check, guard_time))
        return self.nfs3_call(NFSPROC3_SETATTR, arg_list)
    
    def lookup(self, dir_fh=None, name=None):
        arg_list = diropargs3(nfs_fh3(dir_fh), name)
        return self.nfs3_call(NFSPROC3_LOOKUP, arg_list)
    
    def access(self, file_handle=None, access=None):
        arg_list = access3args(nfs_fh3(file_handle), access)
        return self.nfs3_call(NFSPROC3_ACCESS, arg_list)
    
    def readlink(self, link_fh=None):
        arg_list = nfs_fh3(link_fh)
        return self.nfs3_call(NFSPROC3_READLINK, arg_list)
    
    def read(self, file_handle=None, offset=0, count=0):
        arg_list = read3args(nfs_fh3(file_handle), offset, count)
        return self.nfs3_call(NFSPROC3_READ, arg_list)
    
    def write(self, file_handle=None, offset=0, count=0, stable=None, 
              data=None):
        arg_list = write3args(nfs_fh3(file_handle), offset, count, 
                              stable, data)
        return self.nfs3_call(NFSPROC3_WRITE, arg_list)
    
    def create(self, dir_fh=None, name=None, nfs3_mode=UNCHECKED, 
               file_mode_set=0, file_mode_val=0777, uid_set=0, uid_val=None, 
               gid_set=0, gid_val=None, size_set=0, size_val=0, 
               atime_set=0, atime_val=None, mtime_set=0, mtime_val=None,
               exclusive_verf=0):
        ### ToDo: add input validation?
        curr_time=("%s" % time.time()).split('.')
        if atime_val is None:
            atime_val = nfstime3(curr_time[0], curr_time[1])
        if mtime_val is None:
            mtime_val = nfstime3(curr_time[0], curr_time[1])
        if uid_val is None:
            uid_val = self.opts.uid
        if gid_val is None:
            gid_val = self.opts.gid

        arg_list=create3args(
            diropargs3(nfs_fh3(dir_fh), name),
            createhow3(nfs3_mode,
                sattr3(
                    set_uint32(file_mode_set, file_mode_val),
                    set_uint32(uid_set, uid_val),
                    set_uint32(gid_set, gid_val),
                    set_uint64(size_set, size_val),
                    set_time(atime_set, atime_val),
                    set_time(mtime_set, mtime_val)
                ),
                exclusive_verf
            ))
        return self.nfs3_call(NFSPROC3_CREATE, arg_list)
    
    def mkdir(self, parent_fh=None, name=None, 
               dir_mode_set=0, dir_mode_val=0777, uid_set=0, uid_val=None, 
               gid_set=0, gid_val=None, size_set=0, size_val=0, 
               atime_set=0, atime_val=None, mtime_set=0, mtime_val=None):
        ### ToDo: add input validation?
        curr_time=("%s" % time.time()).split('.')
        if atime_val is None:
            atime_val = nfstime3(curr_time[0], curr_time[1])
        if mtime_val is None:
            mtime_val = nfstime3(curr_time[0], curr_time[1])
        if uid_val is None:
            uid_val = self.opts.uid
        if gid_val is None:
            gid_val = self.opts.gid
        arg_list = mkdir3args(diropargs3(nfs_fh3(parent_fh), name),
            sattr3(
                set_uint32(dir_mode_set, dir_mode_val),
                set_uint32(uid_set, uid_val),
                set_uint32(gid_set, gid_val),
                set_uint64(size_set, size_val),
                set_time(atime_set, atime_val),
                set_time(mtime_set, mtime_val)
            ))
        return self.nfs3_call(NFSPROC3_MKDIR, arg_list)
    
    def symlink(self, dir_fh=None, link_name=None,
               mode_set=0, mode_val=0777, uid_set=0, uid_val=None, 
               gid_set=0, gid_val=None, size_set=0, size_val=0, 
               atime_set=0, atime_val=None, mtime_set=0, mtime_val=None,
               data=None):
        ### ToDo: add input validation?
        curr_time=("%s" % time.time()).split('.')
        if atime_val is None:
            atime_val = nfstime3(curr_time[0], curr_time[1])
        if mtime_val is None:
            mtime_val = nfstime3(curr_time[0], curr_time[1])
        if uid_val is None:
            uid_val = self.opts.uid
        if gid_val is None:
            gid_val = self.opts.gid
        arg_list = symlink3args(
            diropargs3(nfs_fh3(dir_fh), link_name), 
            symlinkdata3(
                sattr3(
                    set_uint32(mode_set, mode_val),
                    set_uint32(uid_set, uid_val),
                    set_uint32(gid_set, gid_val),
                    set_uint64(size_set, size_val),
                    set_time(atime_set, atime_val),
                    set_time(mtime_set, mtime_val)
                ),
                data
            ))
        return self.nfs3_call(NFSPROC3_SYMLINK, arg_list)
    
    def mknod(self, dir_fh=None, name=None, type=None, 
              mode_set=0, mode_val=0777, uid_set=0, uid_val=None, 
              gid_set=0, gid_val=None, size_set=0, size_val=0, 
              atime_set=0, atime_val=None, mtime_set=0, mtime_val=None):
        curr_time=("%s" % time.time()).split('.')
        if atime_val is None:
            atime_val = nfstime3(curr_time[0], curr_time[1])
        if mtime_val is None:
            mtime_val = nfstime3(curr_time[0], curr_time[1])
        if uid_val is None:
            uid_val = self.opts.uid
        if gid_val is None:
            gid_val = self.opts.gid
        attr = sattr3(
            set_uint32(mode_set, mode_val),
            set_uint32(uid_set, uid_val),
            set_uint32(gid_set, gid_val),
            set_uint64(size_set, size_val),
            set_time(atime_set, atime_val),
            set_time(mtime_set, mtime_val)
        )
        arg_list=mknod3args(diropargs3(nfs_fh3(dir_fh), name), 
            mknoddata3(type, devicedata3(attr, specdata3(1, 2)), attr))
        return self.nfs3_call(NFSPROC3_MKNOD, arg_list)
    
    def remove(self, dir_handle=None, file_name=None):
        arg_list=diropargs3(nfs_fh3(dir_handle), file_name)
        return self.nfs3_call(NFSPROC3_REMOVE, arg_list)
    
    def rmdir(self, parent_dir_handle=None, target_dir_name=None):
        arg_list=diropargs3(nfs_fh3(parent_dir_handle), target_dir_name)
        return self.nfs3_call(NFSPROC3_RMDIR, arg_list)
    
    def rename(self, old_parent_fh=None, old_file=None, new_parent_fh=None,
               new_file=None):
        arg_list=rename3args(diropargs3(nfs_fh3(old_parent_fh), old_file),
                         diropargs3(nfs_fh3(new_parent_fh), new_file))
        return self.nfs3_call(NFSPROC3_RENAME, arg_list)
    
    def link(self, target_file_fh=None, dir_fh=None, link_name=None):
        arg_list=link3args(nfs_fh3(target_file_fh), diropargs3(nfs_fh3(dir_fh), link_name))
        return self.nfs3_call(NFSPROC3_LINK, arg_list)
    
    def readdir(self, dir_fh=None, cookie=0, cookieverf='0', count=0):
        if type(cookieverf) is not str:
            cookieverf = cookieverf.__str__()
        arg_list = readdir3args(nfs_fh3(dir_fh), cookie, cookieverf, count)
        return self.nfs3_call(NFSPROC3_READDIR, arg_list)
    
    def readdirplus(self, dir_fh=None, cookie=0, cookieverf='0', dircount=0, maxcount=0):
        if type(cookieverf) is not str:
            cookieverf = cookieverf.__str__()
        arg_list = readdirplus3args(nfs_fh3(dir_fh), cookie, cookieverf, dircount, maxcount)
        return self.nfs3_call(NFSPROC3_READDIRPLUS, arg_list)
    
    def fsstat(self, file_fh=None):
        arg_list=nfs_fh3(file_fh)
        return self.nfs3_call(NFSPROC3_FSSTAT, arg_list)
    
    def fsinfo(self, file_fh=None):
        arg_list=nfs_fh3(file_fh)
        return self.nfs3_call(NFSPROC3_FSINFO, arg_list)
    
    def pathconf(self, file_fh=None):
        arg_list=nfs_fh3(file_fh)
        return self.nfs3_call(NFSPROC3_PATHCONF, arg_list)
    
    def commit(self, file_fh=None, offset=0, count=0):
        arg_list=commit3args(nfs_fh3(file_fh), offset, count)
        return self.nfs3_call(NFSPROC3_COMMIT, arg_list)
    
    """
    UTILITY FUNCTIONS
    """

    # Verify a NFS3 call was successful,
    # raise BadNFS3Res otherwise
    def nfs3_check_result(self, res, msg=None):
        if not res.status:
            return
        raise BadNFS3Res(res.status, msg)

    def do_readdir(self, dir_fh, cookie=0, cookieverf = '0', maxcount=4096):
        """ Since we may not get the whole directory listing in one readdir
        request, loop until we do.  For each request result, create a flat
        list with <entry3> objects.
        """
        entries = []
        count = 0
        while 1:
            count += 1
            res = self.readdir(dir_fh, cookie, cookieverf, maxcount)
            self.nfs3_check_result(res, msg="READDIR response #%i" % count)
            cookieverf = res.resok.cookieverf
            reply = res.resok.reply
            if not reply.entries:
                if not reply.eof:
                    raise BadNFS3Res("READDIR had no entries")
                else:
                    break
            entry = reply.entries[0]
            # Loop over all entries in result.
            while 1:
                entries.append(entry)
                if not entry.nextentry:
                    break
                entry = entry.nextentry[0]
            if reply.eof:
                break
            cookie = entry.cookie
        # Remove the entry lists so that the return value isn't
        #    exponentially large
        for entry in entries:
            entry.nextentry = None
        return entries

    def do_readdirplus(self, dir_fh, cookie=0, cookieverf='0', dircount=512, maxcount=4096):
        """ Since we may not get the whole directory listing in one readdirplus
        request, loop until we do.  For each request result, create a flat
        list with <entry3> objects.
        """
        entries = []
        count = 0
        while 1:
            count += 1
            res = self.readdirplus(dir_fh, cookie, cookieverf, dircount, maxcount)
            self.nfs3_check_result(res, msg="READDIR response #%i" % count)
            cookieverf = res.resok.cookieverf
            reply = res.resok.reply
            if not reply.entries:
                if not reply.eof:
                    raise BadNFS3Res("READDIR had no entries")
                else:
                    break
            entry = reply.entries[0]
            # Loop over all entries in result.
            while 1:
                entries.append(entry)
                if not entry.nextentry:
                    break
                entry = entry.nextentry[0]
            if reply.eof:
                break
            cookie = entry.cookie
        # Remove the entry lists so that the return value isn't
        #    exponentially large
        for entry in entries:
            entry.nextentry = None
        return entries

    def clean_dir(self, dir_fh):
        entries = self.do_readdir(dir_fh)
        for e in entries:
            # don't delete folders starting with '.'
            #    makes not only '.' and '..' safe, but hidden folders too
            if e.name[0] != '.':
                # add perms check to remove?  if not, add try/catch?
                res = self.rmdir(dir_fh, e.name)
                if res.status == NFS3ERR_NOTEMPTY:
                    lookup_res = self.lookup(dir_fh, e.name)
                    if lookup_res.status == NFS3_OK:
                        self.clean_dir(lookup_res.object.data)
                    res = self.rmdir(dir_fh, e.name)
                else:
                    if res.status == NFS3ERR_NOTDIR:
                        res = self.remove(dir_fh, e.name)
                self.nfs3_check_result(res, "Attempted to remove %s" % repr(e.name))
