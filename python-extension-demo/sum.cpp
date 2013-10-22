#include <iostream>
using namespace std;

#include <python.h>

template<class T>
T sum(T v[], int nr)
{
	T result = 0;
	for(int i = 0; i != nr; i++){
		result += v[i];
	}
	return result;
}


static PyObject* wrap_sum(PyObject* self, PyObject* args)
{
	if(! PySequence_Check(args) ){
		PyErr_SetString(PyExc_TypeError, "expected a list or tuple");
		return NULL;
	}

	int array_size;
	int *data;
	PyObject *item;

	array_size = PySequence_Length(args);
	data = new int[array_size];

	for(int i = 0; i < array_size; i++){
		item = PySequence_GetItem(args, i);
		
		if(!item){
			continue;
		}

		data[i] = PyInt_AsLong(item);
	}

	int result = sum(data, array_size);
	delete []data;

	return PyInt_FromLong(result);
}

static PyMethodDef sum_module_funcs[] = {
	{"sum", wrap_sum, METH_VARARGS, "sum of a list or tuple"},
	{NULL, NULL, NULL, NULL}
};

PyMODINIT_FUNC
initsum(void)
{
	(void) Py_InitModule("sum", sum_module_funcs);
}

int main(int argc, char *argv[])
{
	Py_SetProgramName(argv[0]);

	Py_Initialize();

	initsum();
}