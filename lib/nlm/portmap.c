#include <Python.h>
#include <rpc/rpc.h>
#include <rpc/pmap_clnt.h>

static PyObject * portmap_set(PyObject *self, PyObject *args)
{
	unsigned long program, version;
	int protocol;
	unsigned short port;
	
	if (!PyArg_ParseTuple(args, "kkiH:set", 
			      &program, &version, &protocol, &port))
		return NULL;
	// Tai: removed the unset here so we can bind both TCP and UDP
	pmap_set(program, version, protocol, port);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * portmap_unset(PyObject *self, PyObject *args)
{
	unsigned long program, version;
	struct netconfig *nconf;
	
	if (!PyArg_ParseTuple(args, "kk:unset",
			      &program, &version))
		return NULL;

	pmap_unset(program, version);
	nconf = getnetconfigent("udp6");
	if (nconf != NULL) {
		rpcb_unset((rpcprog_t)program, (rpcvers_t)version, nconf);
		freenetconfigent(nconf);
	}
	nconf = getnetconfigent("tcp6");
	if (nconf != NULL) {
		rpcb_unset((rpcprog_t)program, (rpcvers_t)version, nconf);
		freenetconfigent(nconf);
	}
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef PortmapMethods[] = {
	{"set", portmap_set, METH_VARARGS, 
	 "Set an entry in the portmapper."},
	{"unset", portmap_unset, METH_VARARGS,
	 "Unset an entry in the portmapper."},
	{NULL, NULL, 0, NULL}
};

void initportmap(void)
{
	(void) Py_InitModule("portmap", PortmapMethods);
}

