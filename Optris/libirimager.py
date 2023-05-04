"""
This module wraps libirmanager
Windows only png functions not included
TCP server related functions not included
Only tested on windows, expected to work on linux
For unknown reasons the first frame tends to be corrupt?
"""

from ctypes import *
import ctypes.util
import numpy as np
import atexit
from enum import Enum
import pathlib
import os

__all__ = ['libirimagerException', 'evo_irimager_terminate', 'evo_irimager_get_thermal_image',
           'evo_irimager_get_palette_image_size', 'evo_irimager_get_palette_image',
           'evo_irimager_get_focusmotor_pos', 'evo_irimager_get_thermal_image_size',
           'evo_irimager_get_thermal_image_size', 'evo_irimager_get_thermal_palette_image',
           'evo_irimager_set_palette_scale', 'evo_irimager_set_radiation_parameters',
           'evo_irimager_set_shutter_mode', 'evo_irimager_set_temperature_range',
           'evo_irimager_trigger_shutter_flag', 'evo_irimager_usb_init', 'raw_to_C',
           'evo_irimager_set_focusmotor_pos']

basepath = pathlib.Path(__file__).absolute().parent

# load library
if os.name == 'nt':
         #windows:
    irdll = CDLL(str(basepath / 'libirimager.dll'))
else:
    #linux:
        irdll = cdll.LoadLibrary(ctypes.util.find_library("irdirectsdk"))



# Generate default path to generic.xml, based on this modules directory
default_config_xml = str(basepath / 'generic.xml')
default_formats_def = str(basepath)

def raw_to_C(d: np.ndarray) -> np.ndarray:
    """
    Convert a given ndarray from raw values to degrees
    """
    return (d.astype(float) - 1000.0) / 10.0

class libirimagerException(Exception):
    pass

def checkerror(i: int):
    if i != 0:
        raise libirimagerException()
    return

irdll.evo_irimager_terminate.argtypes = ()
def evo_irimager_terminate():
    checkerror(irdll.evo_irimager_terminate())
    return

irdll.evo_irimager_usb_init.argtypes = (c_char_p, c_char_p, c_char_p)
def evo_irimager_usb_init(xml_config=None, formats_def=None, logfile=None):
    if xml_config is None:
        xml_config = default_config_xml
    xml_config = xml_config.encode('utf-8')

    if formats_def is None:
        formats_def = default_formats_def
    formats_def = formats_def.encode('utf-8')

    if logfile:
        logfile = logfile.encode('utf-8')

    print(xml_config, formats_def, logfile)

    checkerror(irdll.evo_irimager_usb_init(c_char_p(xml_config), c_char_p(formats_def), c_char_p(logfile)))
    atexit.register(evo_irimager_terminate)
    return

irdll.evo_irimager_get_thermal_image_size.argtypes = (POINTER(c_int), POINTER(c_int))
def evo_irimager_get_thermal_image_size() -> (int, int):
    w = c_int()
    h = c_int()
    checkerror(irdll.evo_irimager_get_thermal_image_size(byref(w), byref(h)))
    return w.value, h.value

irdll.evo_irimager_get_palette_image_size.argtypes = (POINTER(c_int), POINTER(c_int))
def evo_irimager_get_palette_image_size() -> (int, int):
    w = c_int()
    h = c_int()

    checkerror(irdll.evo_irimager_get_palette_image_size(byref(w), byref(h)))
    return w.value, h.value

irdll.evo_irimager_get_thermal_image.argtype = (POINTER(c_int), POINTER(c_int), POINTER(c_ushort))
def evo_irimager_get_thermal_image(w: int, h: int) -> np.ndarray:
    data = (c_ushort*(w*h))()
    checkerror(irdll.evo_irimager_get_thermal_image(byref(c_int(w)), byref(c_int(h)), byref(data)))
    return np.ctypeslib.as_array(data).reshape(h, w)

irdll.evo_irimager_get_palette_image.argtype = (POINTER(c_int), POINTER(c_int), POINTER(c_ushort))
def evo_irimager_get_palette_image(w: int, h: int) -> np.ndarray:
    # TODO not sure on the pallette shape
    data = (c_ushort*(w*h*3))()
    checkerror(irdll.evo_irimager_get_palette_image(byref(c_int(w)), byref(c_int(h)), byref(data)))
    return np.ctypeslib.as_array(data).reshape(h, w, 3).T

irdll.evo_irimager_get_palette_image.argtype = (POINTER(c_int), POINTER(c_int), POINTER(c_ushort),
                                                POINTER(c_int), POINTER(c_int), POINTER(c_ushort))
def evo_irimager_get_thermal_palette_image(w_t: int, h_t: int, w_p: int, h_p: int) -> (np.ndarray, np.ndarray):
    # TODO not sure on the pallette shape
    t_data = c_ushort*(w_t*h_t)
    p_data = c_ushort*(w_p*h_p*3)

    checkerror(irdll.evo_irimager_get_thermal_palette_image(byref(c_int(w_t)), byref(c_int(h_t)), byref(t_data),
                                                            byref(c_int(w_p)), byref(c_int(h_p)), byref(p_data)))
    return np.ctypeslib.as_array(t_data).reshape(h_t, w_t).T, \
           np.ctypeslib.as_array(p_data).reshape(h_p, w_p, 3).T

class EnumOptrisColoringPalette(Enum):
    AlarmBlue = 1
    AlarmBlueHi = 2
    GrayBW = 3
    GrayWB = 4
    AlarmGreen = 5
    Iron = 6
    IronHi = 7
    Medical = 8
    Rainbow = 9
    RainbowHi = 10
    AlarmRed = 11

irdll.evo_irimager_set_palette.argtype = (c_int)
def evo_irimager_set_palette(palette: EnumOptrisColoringPalette):
    checkerror(irdll.evo_irimager_set_palette(c_int(palette.value)))
    return

class EnumOptrisPaletteScalingMethod(Enum):
    Manual = 1
    MinMax = 2
    Sigma1 = 3
    Sigma3 = 4

irdll.evo_irimager_set_palette_scale.argtype = (c_int)
def evo_irimager_set_palette_scale(palette_scale: EnumOptrisPaletteScalingMethod):
    checkerror(irdll.evo_irimager_set_palette(c_int(palette_scale.value)))
    return

class OptrisShutterMode(Enum):
    Manual = 0
    Auto = 1

irdll.evo_irimager_set_shutter_mode.argtype = (c_int)
def evo_irimager_set_shutter_mode(mode: OptrisShutterMode):
    checkerror(irdll.evo_irimager_set_palette(c_int(mode.value)))
    return

irdll.evo_irimager_trigger_shutter_flag.argtype = ()
def evo_irimager_trigger_shutter_flag():
    checkerror(irdll.evo_irimager_set_palette())
    return

irdll.evo_irimager_set_temperature_range.argtype = (c_int, c_int)
def evo_irimager_set_temperature_range(t_min: int, t_max: int):
    checkerror(irdll.evo_irimager_set_temperature_range(c_int(t_min), c_int(t_max)))
    return

irdll.evo_irimager_set_radiation_parameters.argtype = (c_float, c_float, c_float)
def evo_irimager_set_radiation_parameters(emissivity, transmissivity, tAmbient):
    checkerror(irdll.evo_irimager_set_radiation_parameters(c_float(emissivity), c_float(transmissivity), c_float(tAmbient)))
    return

irdll.evo_irimager_set_focusmotor_pos.argtype = (c_float)
def evo_irimager_set_focusmotor_pos(pos: float):
    checkerror(irdll.evo_irimager_set_focusmotor_pos(c_float(pos)))
    return

irdll.evo_irimager_get_focusmotor_pos.argtype = ()
def evo_irimager_get_focusmotor_pos() -> float:
    posOut = c_float()
    checkerror(irdll.evo_irimager_get_focusmotor_pos(byref(posOut)))
    return posOut.value
