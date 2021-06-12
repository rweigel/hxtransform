import os
import ctypes
from datetime import datetime
import numpy as np

libcxform_path = os.path.join(os.path.dirname(__file__), '../hxform/cxformv.so')
libcxform = ctypes.cdll.LoadLibrary(libcxform_path)

time = [1997,1,1,0,0,0]
v_in = np.array([1,0,0],dtype=np.double)
v_out = np.full(3, np.nan, dtype=np.double)

# Call native cxform function directly
es = libcxform.date2es(
		ctypes.c_int(int(time[0])),
		ctypes.c_int(int(time[1])),
		ctypes.c_int(int(time[2])),
	    ctypes.c_int(int(time[3])),
	    ctypes.c_int(int(time[4])),
	    ctypes.c_int(int(time[5]))
	)

ret = libcxform.cxform(
	    str.encode('GSM'),
	    str.encode('GSE'),
	    ctypes.c_double(es),
	    v_in.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
	    v_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
	) 
print(ret)
print(time)
print(v_in)
print(v_out)

# Call vectorized wrapper function cxformv
time = np.array([time,time], dtype=np.int32)
indata = np.array([v_in,v_in], dtype=np.double)
outdata = np.array([v_out,v_out], dtype=np.double)

libcxform = ctypes.cdll.LoadLibrary(libcxform_path)

ret = libcxform.cxformv(
		ctypes.c_void_p(indata.ctypes.data),
		ctypes.c_void_p(time.ctypes.data),
    	ctypes.c_char_p(b'GSM'),
    	ctypes.c_char_p(b'GSE'),
    	ctypes.c_void_p(outdata.ctypes.data),
		ctypes.c_int(indata.shape[0]),
		ctypes.c_int(time.shape[0])
	)
print(ret)
print(time)
print(indata)
print(outdata)