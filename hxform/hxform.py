import numpy as np
from datetime import datetime

def tpad(time, length=7):
    """Pad list with 3 or more elements with zeros.

    Example:
    --------
    >>> from hxform import hxform as hx
    >>> print(hx.tpad([2000,1,1]))                 # [2000, 1, 1, 0, 0, 0, 0]
    >>> print(hx.tpad([2000,1,1], length=4))       # [2000, 1, 1, 0]
    >>> print(hx.tpad([2000,1,1,2,3,4], length=3)) # [2000, 1, 1]
    """

    in_type = type(time)

    # TODO: Check that time is valid
    time = list(time)

    assert(len(time) > 2)

    if len(time) > length:
        time = time[0:length]
    else:
        pad = length - len(time)
        time = time + pad*[0]


    if in_type == np.ndarray:
        return np.array(time)
    elif in_type == tuple:
        return tuple(time)
    else:
        return time


def to_doy(t):
    """Convert from [y, m, d, h, min, sec] to [y, doy, h, min, sec].

    Example
    -------
    >>> to_doy([2000,2,1,9,9,9]) # [2000,32,9,9,9]
    """
    t = tuple(np.array(tpad(t, length=6), dtype=np.int32))
    day_of_year = datetime(*t).timetuple().tm_yday
    return [t[0], day_of_year, t[3], t[4], t[5]]


def transform(v, time, csys_in, csys_out, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Transfrom between coordinates systems using Geopack or SpacePy.

    Parameters
    ----------
    v : array-like

        (Nv, 3) float np.array

        np.array of three floats

        list of three floats

        list containing lists of three floats

        list of 3-element np.arrays

    time : array-like
           list of 3+ ints
           list containing lists of 3+ ints
           np.array of 3+ ints
           (Nt, 3) float np.array, where Nt = 1 or Nt = Nv

           The 3+ ints are [year, month, day, [hours, [minutes, [seconds]]]]
           Zeros are used for any missing optional value.

    csys_in : str
              One of MAG, GEI, GEO, GSE, GSM, SM

    csys_out : str
               One of MAG, GEI, GEO, GSE, GSM, SM

    ctype_in : str
               'car' (default) or 'sph'
               For spherical coordinates, `v` should be in r, latitude, longitude,
               with angles in degrees.

    ctype_out : str
               'car' (default) or 'sph'

    lib : str
          'geopack_08_dp' (default) or 'spacepy'

    Returns
    -------
    array-like with dimensions matching either `time` (if `Nt` != 1 and `Nv` = 1) or
    `v` (if `Nv` =! 1 and `Nt` = 1). If `Nv` and `Nt` != 1, dimensions are same as `v`.

    Return type will match that of `v`. Note that if a list of 3-element np.arrays are
    passed, execution time will be larger. Use `np.ndarrays` for `v` and `time` for fastest
    execution time.

    Examples
    --------
    >>> from hxform import hxform as hx
    >>> t1 = [2000, 1, 1, 0, 0, 0] # or np.array([2000, 1, 1, 0, 0, 0])
    >>> v1 = [0, 0, 1]             # or np.array([0, 0, 1])
    >>> # All of the following are equivalent and return a list with three floats
    >>> from hxform import hxform as hx
    >>> hx.transform(v1, time1, 'GSM', 'GSE')
    >>> hx.transform(v1, time1, 'GSM', 'GSE', ctype_in='car')
    >>> hx.transform(v1, time1, 'GSM', 'GSE', ctype_in='car', ctype_out='car')

    The following 3 calls return a list with two lists of 3 elements

    1. Transform two vectors at same time t1

        >>> from hxform import hxform as hx
        >>> hx.transform([v1, v1], t1, 'GSM', 'GSE')

    2. Transform one vector at two different times

        >>> from hxform import hxform as hx
        >>> hx.transform(v1, [t1, t1], 'GSM', 'GSE')

    3. Transform two vectors, each at different times

        >>> from hxform import hxform as hx
        >>> hx.transform([v1, v1], [t1, t1], 'GSM', 'GSE')
    """

    in_type = type(v)

    list_of_arrays = False
    if isinstance(v[0], np.ndarray) and isinstance(v, list):
        list_of_arrays = True

    v = np.array(v)
    t = np.array(time)

    if len(t.shape) > 1 and len(v.shape) > 1:
        if t.shape[0] != v.shape[0]:
            raise ValueError("t and v cannot be different lengths")

    if lib == 'geopack_08_dp':
        import hxform.geopack_08_dp as geopack_08_dp
        trans = csys_in + 'to' + csys_out

        if len(v.shape) == 1:
            v = np.array([v])
        if len(t.shape) == 1:
            t = np.array([t])
            dtime = np.array([to_doy(t[0])], dtype=np.int32)# angel modification
        else:
            dtime = [] # angel modification
            for i in range(0, t.shape[0]):
                dtime.append(to_doy(tpad(t[i,0:5], length=5)))
            dtime = np.array(dtime, dtype=np.int32)

        # angel modification outsize is the size of the array returned by the fortran subroutine
        if v.shape[0] <= t.shape[0]:
            outsize = t.shape[0]
        else:
            outsize= v.shape[0]

        if ctype_in == 'sph':
            v[:,0], v[:,1], v[:,2] = StoC(v[:,0], v[:,1], v[:,2])
        # angel modification.
        vp = geopack_08_dp.transform(v, trans, dtime, outsize)

        if ctype_out == 'sph':
            vp[:,0], vp[:,1], vp[:,2] = CtoS(vp[:,0], vp[:,1], vp[:,2])# angel modification

    if lib == 'spacepy':
        try:
            # SpacePy is not installed when hxform is installed due to
            # frequent install failures and so the default is to not use it.
            import spacepy.coordinates as sc
            from spacepy.time import Ticktock
            import numpy.matlib
        except ImportError as error:
            print(error.__class__.__name__ + ": " + error.message)
        except Exception as exception:
            print(exception, False)
            print(exception.__class__.__name__ + ": " + exception.message)

        if len(t.shape) == 1 and len(v.shape) > 1:
            t = numpy.matlib.repmat(t, v.shape[0], 1)
        if len(v.shape) == 1 and len(t.shape) > 1:
            v = numpy.matlib.repmat(v, t.shape[0], 1)
        if len(v.shape) == 1:
            v = np.array([v])

        cvals = sc.Coords(v, csys_in, ctype_in)

        if len(t.shape) == 1:
            # SpacePy requires time values to be strings with second precision
            t_str = '%04d-%02d-%02dT%02d:%02d:%02d' % tuple(tpad(t, length=6))
        else:
            t_str = []
            for i in range(t.shape[0]):
                t_str.append('%04d-%02d-%02dT%02d:%02d:%02d' % tuple(tpad(t[i,:], length=6)))
            t_str = np.array(t_str)

        cvals.ticks = Ticktock(t_str, 'ISO')
        newcoord = cvals.convert(csys_out, ctype_out)

        vp = newcoord.data

    if len(t.shape) == 1 and len(v.shape) == 1:
        vp = vp[0, :]

    if in_type == np.ndarray:
        return vp
    else:
        if list_of_arrays is True:
            vp2 = []
            for i in range(vp.shape[0]):
                vp2.append(vp[i])
            return vp2
        else:
            return vp.tolist()


def MAGtoGEI(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'MAG', 'GEI', ...)"""
    return transform(v, time, 'MAG', 'GEI', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def MAGtoGEO(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'MAG', 'GEO', ...)"""
    return transform(v, time, 'MAG', 'GEO', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def MAGtoGSE(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'MAG', 'GSE', ...)"""
    return transform(v, time, 'MAG', 'GSE', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def MAGtoGSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'MAG', 'GSM', ...)"""
    return transform(v, time, 'MAG', 'GSM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def MAGtoSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'MAG', 'SM', ...)"""
    return transform(v, time, 'MAG', 'SM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)


def GEOtoMAG(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'MAG', ...)"""
    return transform(v, time, 'GEO', 'MAG', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GEOtoGEI(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'GEI', ...)"""
    return transform(v, time, 'GEO', 'GEI', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)
# angel modification
def GEItoGEO(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'GEI', ...)"""
    return transform(v, time, 'GEI', 'GEO', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GEOtoGSE(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'GSE', ...)"""
    return transform(v, time, 'GEO', 'GSE', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GEOtoGSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'GSM', ...)"""
    return transform(v, time, 'GEO', 'GSM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GEOtoSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GEO', 'SM', ...)"""
    return transform(v, time, 'GEO', 'SM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)


def GSEtoMAG(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSE', 'MAG', ...)"""
    return transform(v, time, 'GSE','MAG', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSEtoGEI(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSE', 'GEI', ...)"""
    return transform(v, time, 'GSE','GEI', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSEtoGEO(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSE', 'GEO', ...)"""
    return transform(v, time, 'GSE','GEO', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSEtoSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSE', 'SM', ...)"""
    return transform(v, time, 'GSE','SM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)


def GSMtoMAG(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSM', 'MAG', ...)"""
    return transform(v, time, 'GSM', 'MAG', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSMtoGEI(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSM', 'GEI', ...)"""
    return transform(v, time, 'GSM', 'GEI', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSMtoGEO(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSM', 'GEO', ...)"""
    return transform(v, time, 'GSM', 'GEO', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSMtoGSE(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSM', 'GSE', ...)"""
    return transform(v, time, 'GSM', 'GSE', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def GSMtoSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'GSM', 'SM', ...)"""
    return transform(v, time, 'GSM', 'SM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)


def SMtoMAG(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'SM', 'MAG', ...)"""
    return transform(v, time, 'SM', 'MAG', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def SMtoGEI(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'SM', 'GEI', ...)"""
    return transform(v, time, 'SM', 'GEI', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def SMtoGEO(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'SM', 'GEO', ...)"""
    return transform(v, time, 'SM', 'GEO', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def SMtoGSE(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'SM', 'GSE', ...)"""
    return transform(v, time, 'SM', 'GSE', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)

def SMtoGSM(v, time, ctype_in='car', ctype_out='car', lib='geopack_08_dp'):
    """Equivalent to transform(v, time, 'SM', 'GSM', ...)"""
    return transform(v, time, 'SM', 'GSM', ctype_in=ctype_in, ctype_out=ctype_out, lib=lib)


def CtoS(x, y, z):
    """Convert from cartesian to spherical coordinates."""
    r = np.sqrt(np.power(x, 2) + np.power(y, 2) + np.power(z, 2))
    theta = 90.0 - (180.0/np.pi)*np.acos(z/r)
    phi = (180.0/np.pi)*np.atan2(y, x)

    return r, theta, phi

def StoC(r, colat, long):
    """Convert from spherical to cartesian coordinates."""
    x = r*np.cos((np.pi/180.0)*long)*np.cos((np.pi/180.0)*colat)
    y = r*np.sin((np.pi/180.0)*long)*np.cos((np.pi/180.0)*colat)
    z = r*np.cos(np.pi/2.0 - (np.pi/180.0)*colat)
    return x, y, z


def UTtoHMS(UT, **kwargs):
    """Convert universal time in fractional hours into integer hour, minutes, seconds.

    Example
    -------
    >>> from hxform import hxform as hx
    >>> print(hx.UTtoHMS(12))              # [12, 0, 0]
    >>> print(hx.UTtoHMS(24))              # [0, 0, 0]
    >>> print(hx.UTtoHMS(24, keep24=True)) # [24, 0, 0]
    """

    keep24 = False
    if 'keep24' in kwargs:
        keep24 = kwargs['keep24']

    if UT > 24 or UT < 0:
        raise ValueError('Required: 0 <= UT <= 24.')

    hours = int(UT)
    minutes = int((UT-hours)*60.)
    seconds = int(round((UT-hours-minutes/60.)*3600.))
    if seconds == 60:
        seconds = 0
        minutes = minutes + 1
    if minutes == 60:
        minutes = 0
        hours = hours + 1

    if hours == 24 and keep24 == False:
        return [0, 0, 0]

    return [hours, minutes, seconds]


def MAGtoMLT(pos, time, csys='sph', lib='geopack_08_dp'):
    """Compute magnetic local time given a UT and MAG position or longitude.

    Uses equation 93 in Laundal and Richmond, 2016 (10.1007/s11214-016-0275-y)

    Usage:
    ------
    >>> from hxform import hxform as hx
    >>> mlt = hx.MAGtoMLT(MAGlong, time)
    >>> mlt = hx.MAGtoMLT([MAGlong1, Mlong2, ...], time)

    >>> mlt = hx.MAGtoMLT([MAGx, MAGy, MAGz], time, csys='car')
    >>> mlt = hx.MAGtoMLT([[MAGx1, MAGy1, MAGz1],...], time, csys='car')

    Returns:
    --------
    mlt: float or array-like

    Examples:
    --------
    >>> from hxform import hxform as hx
    >>> mlt = hx.MAGtoMLT(0., [2000, 1, 1, 0, 0, 0])
    >>> print(mlt) # 18.869936573301775

    >>> from hxform import hxform as hx
    >>> mlt = hx.MAGtoMLT([0., 0.], [2000, 1, 1, 0, 0, 0])
    >>> print(mlt) # [18.86993657 18.86993657]

    >>> from hxform import hxform as hx
    >>> mlt = hx.MAGtoMLT([-1., 0., 0.], [2000, 1, 1, 0, 0, 0], csys='car')
    >>> print(mlt) # 6.869936573301775

    >>> from hxform import hxform as hx
    >>> mlt = hx.MAGtoMLT([[-1., 0., 0.],[-1., 0., 0.]], [2000, 1, 1, 0, 0, 0], csys='car')
    >>> print(mlt) # [6.86993657 6.86993657]
"""

    assert(csys == 'car' or csys == 'sph')

    pos = np.array(pos)
    time = np.array(time)

    if not isinstance(pos, float):
        pos = np.array(pos)

    if csys == 'sph':
        phi = pos*np.pi/180.
    else:
        if pos.shape == (3, ):
            phi = np.arctan2(pos[1], pos[0])
        else:
            phi = np.arctan2(pos[:, 1], pos[:, 0])

    subsol_pt = transform(np.array([1, 0, 0]), time, 'GSM', 'MAG', lib=lib)

    if len(subsol_pt.shape) == 1:
        phi_cds = np.arctan2(subsol_pt[1], subsol_pt[0])
    else:
        phi_cds = np.arctan2(subsol_pt[:, 1], subsol_pt[:, 0])

    delta = phi - phi_cds # note np.array([a1, a2, ...])+b == np.array([a1+b, a2+b, ...])

    if isinstance(delta, float):
        delta = np.array([delta])

    idx = np.where(delta > np.pi)
    delta[idx] = delta[idx] - 2.*np.pi
    idx = np.where(delta <= -np.pi)
    delta[idx] = delta[idx] + 2.*np.pi

    if delta.size == 1:
        delta = delta[0]

    MLT = 12. + delta*24./(2.*np.pi)
    return MLT
