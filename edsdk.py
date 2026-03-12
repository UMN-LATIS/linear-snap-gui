"""
Canon EDSDK ctypes wrapper for Python.

Loads EDSDK.framework from the local canonSDK directory (or the PyInstaller
bundle when frozen) and exposes the C API together with the constants and
value-lookup tables needed by CameraControl.py.
"""

import ctypes
import ctypes.util
import os
import sys

# ---------------------------------------------------------------------------
# Framework path resolution
# ---------------------------------------------------------------------------

def _find_framework() -> str:
    """Return the absolute path to the EDSDK dylib."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundle: framework binary is copied next to the executable
        base = sys._MEIPASS
        return os.path.join(base, "EDSDK.framework", "Versions", "A", "EDSDK")

    # Development: relative to this file
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(
        here,
        "canonSDK", "EDSDK", "Framework", "EDSDK.framework", "EDSDK",
    )


_lib = ctypes.CDLL(_find_framework())

# ---------------------------------------------------------------------------
# Primitive types
# ---------------------------------------------------------------------------

EdsError   = ctypes.c_uint32
EdsUInt32  = ctypes.c_uint32
EdsInt32   = ctypes.c_int32
EdsUInt64  = ctypes.c_uint64
EdsInt64   = ctypes.c_int64
EdsBool    = ctypes.c_uint32
EdsChar    = ctypes.c_char

# All reference types are opaque pointers
EdsBaseRef          = ctypes.c_void_p
EdsCameraListRef    = ctypes.c_void_p
EdsCameraRef        = ctypes.c_void_p
EdsStreamRef        = ctypes.c_void_p
EdsEvfImageRef      = ctypes.c_void_p
EdsDirectoryItemRef = ctypes.c_void_p

EDS_MAX_NAME = 256

# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

class EdsPoint(ctypes.Structure):
    _fields_ = [("x", EdsInt32), ("y", EdsInt32)]


class EdsSize(ctypes.Structure):
    _fields_ = [("width", EdsInt32), ("height", EdsInt32)]


class EdsRect(ctypes.Structure):
    _fields_ = [("point", EdsPoint), ("size", EdsSize)]


class EdsDeviceInfo(ctypes.Structure):
    _fields_ = [
        ("szPortName",          EdsChar * EDS_MAX_NAME),
        ("szDeviceDescription", EdsChar * EDS_MAX_NAME),
        ("deviceSubType",       EdsUInt32),
        ("reserved",            EdsUInt32),
    ]


class EdsDirectoryItemInfo(ctypes.Structure):
    _fields_ = [
        ("size",       EdsUInt64),
        ("isFolder",   EdsBool),
        ("groupID",    EdsUInt32),
        ("option",     EdsUInt32),
        ("szFileName", EdsChar * EDS_MAX_NAME),
        ("format",     EdsUInt32),
        ("dateTime",   EdsUInt32),
    ]


class EdsCapacity(ctypes.Structure):
    _fields_ = [
        ("numberOfFreeClusters", EdsInt32),
        ("bytesPerSector",       EdsInt32),
        ("reset",                EdsBool),
    ]


class EdsPropertyDesc(ctypes.Structure):
    _fields_ = [
        ("form",        EdsInt32),
        ("access",      EdsInt32),
        ("numElements", EdsInt32),
        ("propDesc",    EdsInt32 * 128),
    ]

# ---------------------------------------------------------------------------
# Callback function types  (EdsError EDSCALLBACK *Handler(...))
# Under macOS / clang the calling convention is the default (cdecl-equivalent)
# ---------------------------------------------------------------------------

ObjectEventHandler   = ctypes.CFUNCTYPE(EdsError, EdsUInt32, EdsBaseRef, ctypes.c_void_p)
PropertyEventHandler = ctypes.CFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, EdsUInt32, ctypes.c_void_p)
StateEventHandler    = ctypes.CFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, ctypes.c_void_p)
CameraAddedHandler   = ctypes.CFUNCTYPE(EdsError, ctypes.c_void_p)

# ---------------------------------------------------------------------------
# SDK constants — property IDs
# ---------------------------------------------------------------------------

kEdsPropID_ProductName       = 0x00000002
kEdsPropID_SaveTo            = 0x0000000B
kEdsPropID_WhiteBalance      = 0x00000106
kEdsPropID_ColorTemperature  = 0x00000107
kEdsPropID_ImageQuality      = 0x00000100
kEdsPropID_ISOSpeed          = 0x00000402
kEdsPropID_Tv                = 0x00000406
kEdsPropID_Av                = 0x00000405
kEdsPropID_Evf_OutputDevice  = 0x00000500
kEdsPropID_Evf_Mode          = 0x00000501
kEdsPropID_Evf_AFMode        = 0x0000050E

# ---------------------------------------------------------------------------
# SDK constants — save-to destinations
# ---------------------------------------------------------------------------

kEdsSaveTo_Camera = 1
kEdsSaveTo_Host   = 2
kEdsSaveTo_Both   = 3

# ---------------------------------------------------------------------------
# SDK constants — EVF output device
# ---------------------------------------------------------------------------

kEdsEvfOutputDevice_TFT      = 1
kEdsEvfOutputDevice_PC       = 2
kEdsEvfOutputDevice_PC_Small = 8
kEdsEvfOutputDevice_OFF      = 0   # disable live view

# ---------------------------------------------------------------------------
# SDK constants — camera commands
# ---------------------------------------------------------------------------

kEdsCameraCommand_TakePicture            = 0x00000000
kEdsCameraCommand_ExtendShutDownTimer    = 0x00000001
kEdsCameraCommand_PressShutterButton     = 0x00000004
kEdsCameraCommand_DoEvfAf                = 0x00000102
kEdsCameraCommand_DriveLensEvf           = 0x00000103

kEdsCameraCommand_ShutterButton_OFF              = 0x00000000
kEdsCameraCommand_ShutterButton_Halfway          = 0x00000001
kEdsCameraCommand_ShutterButton_Completely       = 0x00000003
kEdsCameraCommand_ShutterButton_Halfway_NonAF    = 0x00010001
kEdsCameraCommand_ShutterButton_Completely_NonAF = 0x00010003

# ---------------------------------------------------------------------------
# SDK constants — object/property/state events
# ---------------------------------------------------------------------------

kEdsObjectEvent_DirItemRequestTransfer = 0x00000208
kEdsObjectEvent_DirItemCreated         = 0x00000204
kEdsObjectEvent_All                    = 0x00000200

kEdsPropertyEvent_PropertyChanged      = 0x00000101
kEdsPropertyEvent_All                  = 0x00000100

kEdsStateEvent_Shutdown                = 0x00000301
kEdsStateEvent_WillSoonShutDown        = 0x00000303
kEdsStateEvent_CaptureError            = 0x00000305
kEdsStateEvent_All                     = 0x00000300

# ---------------------------------------------------------------------------
# SDK constants — file access / creation
# ---------------------------------------------------------------------------

kEdsFileCreateDisposition_CreateAlways = 1
kEdsAccess_ReadWrite                   = 2

# ---------------------------------------------------------------------------
# White balance enum → EDSDK integer
# ---------------------------------------------------------------------------

WB_MAP = {
    "Auto":             0,
    "Daylight":         1,
    "Cloudy":           2,
    "Tungsten":         3,
    "Fluorescent":      4,
    "Flash":            5,
    "Color Temperature": 9,   # same label used internally
}

# ---------------------------------------------------------------------------
# ISO speed string → EDSDK enum value
# (values from Canon EDSDK documentation; Canon R8 compatible)
# ---------------------------------------------------------------------------

ISO_MAP = {
    "Auto":  0x00000000,
    "100":   0x00000048,
    "125":   0x0000004b,
    "160":   0x0000004d,
    "200":   0x00000050,
    "250":   0x00000053,
    "320":   0x00000055,
    "400":   0x00000058,
    "500":   0x0000005b,
    "640":   0x0000005d,
    "800":   0x00000060,
    "1000":  0x00000063,
    "1250":  0x00000065,
    "1600":  0x00000068,
    "2000":  0x0000006b,
    "2500":  0x0000006d,
    "3200":  0x00000070,
    "4000":  0x00000073,
    "5000":  0x00000075,
    "6400":  0x00000078,
    "8000":  0x0000007b,
    "10000": 0x0000007d,
    "12800": 0x00000080,
    "25600": 0x00000088,
    "51200": 0x00000090,
    "102400": 0x00000098,
}

# ---------------------------------------------------------------------------
# Shutter speed (Tv) string → EDSDK enum value
# ---------------------------------------------------------------------------

TV_MAP = {
    "30":    0x10,
    "25":    0x13,
    "20":    0x15,
    "15":    0x18,
    "13":    0x1b,
    "10":    0x1d,
    "8":     0x20,
    "6":     0x23,
    "5":     0x25,
    "4":     0x28,
    "3.2":   0x2b,
    "2.5":   0x2d,
    "2":     0x30,
    "1.6":   0x33,
    "1.3":   0x35,
    "1":     0x38,
    "0.8":   0x3b,
    "0.6":   0x3d,
    "1/2":   0x40,
    "1/2.5": 0x43,
    "1/3":   0x45,
    "1/4":   0x48,
    "1/5":   0x4b,
    "1/6":   0x4d,
    "1/8":   0x50,
    "1/10":  0x53,
    "1/13":  0x55,
    "1/15":  0x58,
    "1/20":  0x5b,
    "1/25":  0x5d,
    "1/30":  0x60,
    "1/40":  0x63,
    "1/50":  0x65,
    "1/60":  0x68,
    "1/80":  0x6b,
    "1/100": 0x6d,
    "1/125": 0x70,
    "1/160": 0x73,
    "1/200": 0x75,
    "1/250": 0x78,
    "1/320": 0x7b,
    "1/400": 0x7d,
    "1/500": 0x80,
    "1/640": 0x83,
    "1/800": 0x85,
    "1/1000": 0x88,
    "1/1250": 0x8b,
    "1/1600": 0x8d,
    "1/2000": 0x90,
    "1/2500": 0x93,
    "1/3200": 0x95,
    "1/4000": 0x98,
    "1/5000": 0x9b,
    "1/6400": 0x9d,
    "1/8000": 0xa0,
}

# ---------------------------------------------------------------------------
# Bind C functions
# ---------------------------------------------------------------------------

def _fn(name, restype, *argtypes):
    fn = getattr(_lib, name)
    fn.restype  = restype
    fn.argtypes = list(argtypes)
    return fn


EdsInitializeSDK   = _fn("EdsInitializeSDK",  EdsError)
EdsTerminateSDK    = _fn("EdsTerminateSDK",   EdsError)
EdsGetEvent        = _fn("EdsGetEvent",        EdsError)

EdsRetain          = _fn("EdsRetain",  EdsUInt32, EdsBaseRef)
EdsRelease         = _fn("EdsRelease", EdsUInt32, EdsBaseRef)

EdsGetCameraList   = _fn("EdsGetCameraList",
                         EdsError,
                         ctypes.POINTER(EdsCameraListRef))

EdsGetChildCount   = _fn("EdsGetChildCount",
                         EdsError,
                         EdsBaseRef,
                         ctypes.POINTER(EdsUInt32))

EdsGetChildAtIndex = _fn("EdsGetChildAtIndex",
                         EdsError,
                         EdsBaseRef,
                         EdsInt32,
                         ctypes.POINTER(EdsBaseRef))

EdsGetDeviceInfo   = _fn("EdsGetDeviceInfo",
                         EdsError,
                         EdsCameraRef,
                         ctypes.POINTER(EdsDeviceInfo))

EdsOpenSession     = _fn("EdsOpenSession",  EdsError, EdsCameraRef)
EdsCloseSession    = _fn("EdsCloseSession", EdsError, EdsCameraRef)

EdsGetPropertySize = _fn("EdsGetPropertySize",
                         EdsError,
                         EdsBaseRef, EdsUInt32, EdsInt32,
                         ctypes.POINTER(EdsUInt32),
                         ctypes.POINTER(EdsUInt32))

EdsGetPropertyData = _fn("EdsGetPropertyData",
                         EdsError,
                         EdsBaseRef, EdsUInt32, EdsInt32,
                         EdsUInt32, ctypes.c_void_p)

EdsSetPropertyData = _fn("EdsSetPropertyData",
                         EdsError,
                         EdsBaseRef, EdsUInt32, EdsInt32,
                         EdsUInt32, ctypes.c_void_p)

EdsGetPropertyDesc = _fn("EdsGetPropertyDesc",
                         EdsError,
                         EdsBaseRef, EdsUInt32,
                         ctypes.POINTER(EdsPropertyDesc))

EdsSendCommand     = _fn("EdsSendCommand",
                         EdsError,
                         EdsCameraRef, EdsUInt32, EdsInt32)

EdsSetCapacity     = _fn("EdsSetCapacity",
                         EdsError,
                         EdsCameraRef, EdsCapacity)

# Directory item / file download
EdsGetDirectoryItemInfo = _fn("EdsGetDirectoryItemInfo",
                              EdsError,
                              EdsDirectoryItemRef,
                              ctypes.POINTER(EdsDirectoryItemInfo))

EdsCreateFileStream = _fn("EdsCreateFileStream",
                          EdsError,
                          ctypes.c_char_p,
                          EdsUInt32,    # EdsFileCreateDisposition
                          EdsUInt32,    # EdsAccess
                          ctypes.POINTER(EdsStreamRef))

EdsDownload         = _fn("EdsDownload",
                          EdsError,
                          EdsDirectoryItemRef,
                          EdsUInt64,
                          EdsStreamRef)

EdsDownloadComplete = _fn("EdsDownloadComplete",
                          EdsError,
                          EdsDirectoryItemRef)

EdsDownloadCancel   = _fn("EdsDownloadCancel",
                          EdsError,
                          EdsDirectoryItemRef)

# Memory stream / EVF
EdsCreateMemoryStream = _fn("EdsCreateMemoryStream",
                            EdsError,
                            EdsUInt64,
                            ctypes.POINTER(EdsStreamRef))

EdsCreateEvfImageRef  = _fn("EdsCreateEvfImageRef",
                            EdsError,
                            EdsStreamRef,
                            ctypes.POINTER(EdsEvfImageRef))

EdsDownloadEvfImage   = _fn("EdsDownloadEvfImage",
                            EdsError,
                            EdsCameraRef,
                            EdsEvfImageRef)

EdsGetPointer = _fn("EdsGetPointer",
                    EdsError,
                    EdsStreamRef,
                    ctypes.POINTER(ctypes.c_void_p))

EdsGetLength  = _fn("EdsGetLength",
                    EdsError,
                    EdsStreamRef,
                    ctypes.POINTER(EdsUInt64))

# Event handlers
EdsSetObjectEventHandler = _fn("EdsSetObjectEventHandler",
                               EdsError,
                               EdsCameraRef,
                               EdsUInt32,             # event
                               ObjectEventHandler,
                               ctypes.c_void_p)

EdsSetPropertyEventHandler = _fn("EdsSetPropertyEventHandler",
                                 EdsError,
                                 EdsCameraRef,
                                 EdsUInt32,           # event
                                 PropertyEventHandler,
                                 ctypes.c_void_p)

EdsSetCameraStateEventHandler = _fn("EdsSetCameraStateEventHandler",
                                    EdsError,
                                    EdsCameraRef,
                                    EdsUInt32,        # event
                                    StateEventHandler,
                                    ctypes.c_void_p)

EdsSetCameraAddedHandler = _fn("EdsSetCameraAddedHandler",
                               EdsError,
                               CameraAddedHandler,
                               ctypes.c_void_p)

# ---------------------------------------------------------------------------
# Helper: raise Python exception on SDK error
# ---------------------------------------------------------------------------

_EDS_ERR_NAMES = {
    0x00000000: "OK",
    0x00000001: "UNIMPLEMENTED",
    0x00000002: "INTERNAL_ERROR",
    0x00000003: "MEM_ALLOC_FAILED",
    0x00000004: "MEM_FREE_FAILED",
    0x00000005: "OPERATION_CANCELLED",
    0x00000006: "INCOMPATIBLE_VERSION",
    0x00000007: "NOT_SUPPORTED",
    0x00000008: "UNEXPECTED_EXCEPTION",
    0x00000009: "PROTECTION_VIOLATION",
    0x0000000A: "MISSING_CALLBACKFUNC",
    0x0000000B: "HANDLE_NOT_FOUND",
    0x0000000C: "INVALID_ID",
    0x0000000D: "WAIT_TIMEOUT_ERROR",
    0x00000021: "INVALID_FNPOINTER",
    0x00000022: "INVALID_SECTOR_SIZE",
    0x00000023: "INVALID_BUFFER",
    0x00000024: "INVALID_BUFFER_SIZE",
    0x00000025: "INVALID_FNPOINTER",
    0x00000026: "INVALID_SORT_FN",
    0x000000C0: "SESSION_CONNECTION_ERROR",  # Undocumented: likely camera locked/unavailable
    0x00002001: "FILE_IO_ERROR",
    0x00002002: "FILE_TOO_MANY_OPEN",
    0x00002003: "FILE_NOT_FOUND",
    0x00002004: "FILE_OPEN_ERROR",
    0x00002005: "FILE_CLOSE_ERROR",
    0x00002006: "FILE_SEEK_ERROR",
    0x00002007: "FILE_TELL_ERROR",
    0x00002008: "FILE_READ_ERROR",
    0x00002009: "FILE_WRITE_ERROR",
    0x0000200A: "FILE_EOF_REACHED",
    0x0000200B: "FILE_DISK_FULL_ERROR",
    0x0000200C: "FILE_ALREADY_EXISTS",
    0x0000200D: "FILE_FORMAT_UNRECOGNIZED",
    0x0000200E: "FILE_DATA_CORRUPT",
    0x0000200F: "FILE_NAMING_NA",
    0x00002011: "DIR_NOT_FOUND",
    0x00002012: "DIR_IO_ERROR",
    0x00002013: "DIR_ENTRY_NOT_FOUND",
    0x00002014: "DIR_ENTRY_EXISTS",
    0x00002015: "DIR_NOT_EMPTY",
    0x00002BFF: "DEVICE_NOT_FOUND",
    0x00002C00: "DEVICE_BUSY",
    0x00002C01: "DEVICE_INVALID",
    0x00002C02: "DEVICE_EMERGENCY",
    0x00002C03: "DEVICE_MEMORY_FULL",
    0x00002C04: "DEVICE_INTERNAL_ERROR",
    0x00002C05: "DEVICE_INVALID_PARAMETER",
    0x00002C06: "DEVICE_NO_DISK",
    0x00002C07: "DEVICE_DISK_ERROR",
    0x00002C08: "DEVICE_CF_GATE_CHANGED",
    0x00002C09: "DEVICE_DIAL_CHANGED",
    0x00002C0A: "DEVICE_NOT_INSTALLED",
    0x00002C0B: "DEVICE_STAY_AWAKE",
    0x00002C0C: "DEVICE_NOT_RELEASED",
    0x00002D01: "STREAM_IO_ERROR",
    0x00002D02: "STREAM_NOT_OPEN",
    0x00002D03: "STREAM_ALREADY_OPEN",
    0x00002D04: "STREAM_OPEN_ERROR",
    0x00002D05: "STREAM_CLOSE_ERROR",
    0x00002D06: "STREAM_SEEK_ERROR",
    0x00002D07: "STREAM_TELL_ERROR",
    0x00002D08: "STREAM_READ_ERROR",
    0x00002D09: "STREAM_WRITE_ERROR",
    0x00002D0A: "STREAM_PERMISSION_ERROR",
    0x00002D0B: "STREAM_COULDNT_BEGIN_THREAD",
    0x00002D0C: "STREAM_BAD_OPTIONS",
    0x00002D0D: "STREAM_END_OF_STREAM",
    0x00002E01: "COMM_PORT_IS_IN_USE",
    0x00002E02: "COMM_DISCONNECTED",
    0x00002E03: "COMM_DEVICE_INCOMPATIBLE",
    0x00002E04: "COMM_BUFFER_FULL",
    0x00002E05: "COMM_USB_BUS_ERR",
    0x00002F04: "USB_DEVICE_LOCK_ERROR",
    0x00002F06: "USB_DEVICE_UNLOCK_ERROR",
    0x00003000: "STI_UNKNOWN_ERROR",
    0x00003001: "STI_INTERNAL_ERROR",
    0x00003002: "STI_DEVICE_CREATE_ERROR",
    0x00003003: "STI_DEVICE_RELEASE_ERROR",
    0x00003004: "DEVICE_NOT_LAUNCHED",
    0x00003101: "ENUM_NA",
    0x00003102: "INVALID_FN_CALL",
    0x00003103: "HANDLE_UNAVAILABLE",
    0x00003104: "INVALID_STATUS",
    0x00003105: "INVALID_PARAMETER",
    0x00004000: "TAKE_PICTURE_AF_NG",
    0x00004001: "TAKE_PICTURE_RESERVED",
    0x00004002: "TAKE_PICTURE_MIRROR_UP_NG",
    0x00004003: "TAKE_PICTURE_SENSOR_CLEANING_NG",
    0x00004004: "TAKE_PICTURE_SILENCE_NG",
    0x00004005: "TAKE_PICTURE_NO_CARD_NG",
    0x00004006: "TAKE_PICTURE_WRITE_ERROR_NG",
    0x00004007: "TAKE_PICTURE_CARD_NG",
    0x00004008: "TAKE_PICTURE_CARD_PROTECT_NG",
    0x00004009: "TAKE_PICTURE_MOVIE_CROP_NG",
    0x0000400A: "TAKE_PICTURE_STROBO_CHARGE_NG",
    0x0000400B: "TAKE_PICTURE_NO_LENS_NG",
    0x0000400C: "TAKE_PICTURE_SPECIAL_MOVIE_MODE_NG",
    0x0000400D: "TAKE_PICTURE_LV_REL_PROHIBIT_MODE_NG",
}


class EDSError(Exception):
    def __init__(self, code: int, context: str = ""):
        self.code = code
        name = _EDS_ERR_NAMES.get(code, f"0x{code:08X}")
        msg = f"EDSDK error {name}"
        if context:
            msg = f"{context}: {msg}"
        super().__init__(msg)


def check(err: int, context: str = "") -> None:
    """Raise EDSError if *err* is not EDS_ERR_OK."""
    if err != 0:
        raise EDSError(err, context)
