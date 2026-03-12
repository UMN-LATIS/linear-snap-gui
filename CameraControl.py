import threading
import ctypes
import numpy as np
import cv2
import os
import platform
import time
import atexit
import pathlib
import shutil
from pubsub import pub
from multiprocessing.connection import Client

import edsdk as eds


class CameraControl:
    image = None
    t = None
    photoCount = 0
    stopWaiting = False
    stopLiveView = True
    laplacian = 0
    likelyBlank = False
    camera = None           # EdsCameraRef (ctypes c_void_p)
    new_folder_path = ""
    requiresRefocus = False
    stackCenter = None

    # ctypes callback objects must stay alive as long as the SDK holds a
    # pointer to them — store them as instance attributes.
    _obj_cb   = None
    _prop_cb  = None
    _state_cb = None

    def __init__(self, config):
        self.config = config
        self._transfer_event  = threading.Event()
        self._pending_dir_item = None   # EdsDirectoryItemRef awaiting download
        self._sdk_initialized  = False
        self._event_thread     = None
        self._stop_event_thread = False

        try:
            eds.check(eds.EdsInitializeSDK(), "EdsInitializeSDK")
            self._sdk_initialized = True
            
            # Retry logic: sometimes the camera needs time to enumerate after SDK init
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self._connect()
                    break  # Success!
                except RuntimeError as e:
                    if "No Canon camera detected" in str(e) and attempt < max_retries - 1:
                        print(f"Camera not found on attempt {attempt+1}, retrying...")
                        time.sleep(1.5)
                    else:
                        raise
        except Exception as exc:
            print(f"Camera init failed: {exc}")
            self.camera = None

        atexit.register(self.cleanup)

    def _reset_macos_camera_daemons(self):
        if platform.system() != "Darwin":
            return
        # Optional manual override only. Automatic daemon killing caused
        # regressions where the camera disappeared during initialization.
        if os.environ.get("LINEARSNAP_KILL_PTP", "0") != "1":
            return
        os.system("killall -9 ptpcamerad 2>/dev/null; true")
        os.system("killall -9 PTPCamera 2>/dev/null; true")
        time.sleep(0.25)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self):
        camera_list = eds.EdsCameraListRef()
        
        eds.check(eds.EdsGetCameraList(ctypes.byref(camera_list)), "EdsGetCameraList")

        count = eds.EdsUInt32(0)
        eds.check(eds.EdsGetChildCount(camera_list, ctypes.byref(count)), "EdsGetChildCount")

        if count.value == 0:
            eds.EdsRelease(camera_list)
            raise RuntimeError("No Canon camera detected")

        camera_ref = eds.EdsCameraRef()
        try:
            eds.check(
                eds.EdsGetChildAtIndex(camera_list, 0, ctypes.byref(camera_ref)),
                "EdsGetChildAtIndex",
            )
        except Exception as e:
            eds.EdsRelease(camera_list)
            raise
        
        eds.EdsRelease(camera_list)

        try:
            eds.check(eds.EdsOpenSession(camera_ref), "EdsOpenSession")
        except Exception as e:
            eds.EdsRelease(camera_ref)
            raise
            
        self.camera = camera_ref

        self._obj_cb   = eds.ObjectEventHandler(self._on_object_event)
        self._prop_cb  = eds.PropertyEventHandler(self._on_property_event)
        self._state_cb = eds.StateEventHandler(self._on_state_event)

        err = eds.EdsSetObjectEventHandler(
            self.camera, eds.kEdsObjectEvent_All,
            self._obj_cb, None,
        )
        eds.check(err, "EdsSetObjectEventHandler")
        
        err = eds.EdsSetPropertyEventHandler(
            self.camera, eds.kEdsPropertyEvent_All,
            self._prop_cb, None,
        )
        eds.check(err, "EdsSetPropertyEventHandler")
        
        err = eds.EdsSetCameraStateEventHandler(
            self.camera, eds.kEdsStateEvent_All,
            self._state_cb, None,
        )
        eds.check(err, "EdsSetCameraStateEventHandler")

        self._stop_event_thread = False
        self._event_thread = threading.Thread(
            target=self._poll_events, name="edsdk-events", daemon=True
        )
        self._event_thread.start()

    def _get_product_name(self) -> str:
        buf = ctypes.create_string_buffer(256)
        try:
            eds.EdsGetPropertyData(
                self.camera, eds.kEdsPropID_ProductName, 0, 256, buf,
            )
            return buf.value.decode("utf-8", errors="replace")
        except Exception:
            return "Unknown"

    # ------------------------------------------------------------------
    # EdsGetEvent polling thread
    # ------------------------------------------------------------------

    def _poll_events(self):
        while not self._stop_event_thread:
            try:
                eds.EdsGetEvent()
            except Exception:
                pass
            time.sleep(0.05)

    # ------------------------------------------------------------------
    # EDSDK event callbacks
    # ------------------------------------------------------------------

    def _on_object_event(self, event, obj_ref, context):
        if event == eds.kEdsObjectEvent_DirItemRequestTransfer:
            eds.EdsRetain(obj_ref)
            self._pending_dir_item = obj_ref
            self._transfer_event.set()
        return 0

    def _on_property_event(self, event, prop_id, param, context):
        return 0

    def _on_state_event(self, event, event_data, context):
        if event == eds.kEdsStateEvent_Shutdown:
            print("Camera disconnected")
            self.camera = None
        elif event == eds.kEdsStateEvent_WillSoonShutDown:
            if self.camera is not None:
                try:
                    eds.EdsSendCommand(
                        self.camera, eds.kEdsCameraCommand_ExtendShutDownTimer, 0,
                    )
                except Exception:
                    pass
        return 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self):
        self.photoCount = 0
        self.laplacian = 0
        self.likelyBlank = False
        self.requiresRefocus = False

    def setCoreId(self, coreId):
        self.coreId = coreId

    def cleanup(self):
        self.stopLiveView = True
        self._stop_event_thread = True
        time.sleep(0.15)
        if self.camera is not None:
            try:
                eds.EdsCloseSession(self.camera)
                eds.EdsRelease(self.camera)
            except Exception:
                pass
            self.camera = None
        if self._sdk_initialized:
            try:
                eds.EdsTerminateSDK()
            except Exception:
                pass
            self._sdk_initialized = False

    def setLiveView(self, liveView):
        if liveView:
            if not self.stopLiveView:
                return
            self.stopLiveView = False
            
            # Enable EVF on main thread BEFORE spawning daemon
            try:
                self._enable_evf()
            except Exception as e:
                print(f"Failed to enable EVF: {e}")
                self.stopLiveView = True
                return
            
            self.t = threading.Thread(
                target=self.runLiveView, name="liveViewWorker", daemon=True
            )
            self.t.start()
        else:
            self.stopLiveView = True
            time.sleep(0.2)  # Let thread exit
            try:
                self._disable_evf()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Camera settings
    # ------------------------------------------------------------------

    def setupCamera(self, iso_value: str):
        if self.camera is None:
            return

        iso_enum = eds.ISO_MAP.get(str(iso_value))
        if iso_enum is not None:
            val = eds.EdsUInt32(iso_enum)
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_ISOSpeed, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            )
        else:
            print(f"setupCamera: unknown ISO value '{iso_value}'")

        tv_key = self.config.configValues.get("previewShutter", "1/15")
        tv_enum = eds.TV_MAP.get(tv_key)
        if tv_enum is not None:
            val = eds.EdsUInt32(tv_enum)
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_Tv, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            )
        else:
            print(f"setupCamera: unknown Tv value '{tv_key}'")

        wb_val = eds.EdsUInt32(eds.WB_MAP["Color Temperature"])
        eds.EdsSetPropertyData(
            self.camera, eds.kEdsPropID_WhiteBalance, 0,
            ctypes.sizeof(eds.EdsUInt32), ctypes.byref(wb_val),
        )

        try:
            ct = int(self.config.configValues.get("colorTemperature", "5600"))
            ct_val = eds.EdsUInt32(ct)
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_ColorTemperature, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(ct_val),
            )
        except (ValueError, TypeError) as exc:
            print(f"setupCamera: bad colorTemperature: {exc}")

    def _set_u32_property(self, prop_id, enum_value, label: str):
        if self.camera is None:
            raise RuntimeError("Camera not initialized")

        # If the camera reports a property description, only write supported values.
        try:
            desc = eds.EdsPropertyDesc()
            err = eds.EdsGetPropertyDesc(self.camera, prop_id, ctypes.byref(desc))
            if err == 0 and desc.numElements > 0:
                supported = {int(desc.propDesc[i]) for i in range(desc.numElements)}
                if int(enum_value) not in supported:
                    raise ValueError(f"{label}: value not supported by current camera mode")
        except ValueError:
            raise
        except Exception:
            # Some bodies/modes do not expose property desc reliably; fall back to direct write.
            pass

        val = eds.EdsUInt32(enum_value)
        eds.check(
            eds.EdsSetPropertyData(
                self.camera, prop_id, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            ),
            label,
        )

    def set_iso(self, iso_value: str):
        iso_enum = eds.ISO_MAP.get(str(iso_value))
        if iso_enum is None:
            raise ValueError(f"Unsupported ISO value: {iso_value}")
        self._set_u32_property(eds.kEdsPropID_ISOSpeed, iso_enum, "set ISO")

    def set_shutter(self, shutter_value: str):
        tv_enum = eds.TV_MAP.get(str(shutter_value))
        if tv_enum is None:
            raise ValueError(f"Unsupported shutter value: {shutter_value}")
        self._set_u32_property(eds.kEdsPropID_Tv, tv_enum, "set shutter")

    def set_aperture(self, fstop_value: str):
        av_enum = eds.AV_MAP.get(str(fstop_value))
        if av_enum is None:
            raise ValueError(f"Unsupported F-stop value: {fstop_value}")
        self._set_u32_property(eds.kEdsPropID_Av, av_enum, "set aperture")

    def set_white_balance(self, wb_value: str):
        wb_enum = eds.WB_MAP.get(str(wb_value))
        if wb_enum is None:
            raise ValueError(f"Unsupported white balance value: {wb_value}")
        self._set_u32_property(eds.kEdsPropID_WhiteBalance, wb_enum, "set white balance")

    def _get_supported_prop_labels(self, prop_id: int, value_map: dict):
        if self.camera is None:
            return []

        reverse = {int(v): str(k) for k, v in value_map.items()}
        desc = eds.EdsPropertyDesc()
        err = eds.EdsGetPropertyDesc(self.camera, prop_id, ctypes.byref(desc))
        if err != 0 or desc.numElements <= 0:
            return []

        labels = []
        for i in range(desc.numElements):
            raw = int(desc.propDesc[i])
            label = reverse.get(raw)
            if label is not None:
                labels.append(label)
        return labels

    def get_supported_setting_labels(self):
        return {
            "iso": self._get_supported_prop_labels(eds.kEdsPropID_ISOSpeed, eds.ISO_MAP),
            "shutter": self._get_supported_prop_labels(eds.kEdsPropID_Tv, eds.TV_MAP),
            "aperture": self._get_supported_prop_labels(eds.kEdsPropID_Av, eds.AV_MAP),
            "white_balance": self._get_supported_prop_labels(eds.kEdsPropID_WhiteBalance, eds.WB_MAP),
        }

    def apply_exposure_settings(self, iso_value: str, shutter_value: str, fstop_value: str, wb_value: str = None):
        was_liveview_on = not self.stopLiveView
        if was_liveview_on:
            self.setLiveView(False)
            time.sleep(0.25)

        try:
            self.set_iso(iso_value)
            self.set_shutter(shutter_value)
            self.set_aperture(fstop_value)
            if wb_value is not None:
                self.set_white_balance(wb_value)
        finally:
            if was_liveview_on:
                # Resume liveview after applying properties.
                self.setLiveView(True)

    def prepare_host_download(self):
        if self.camera is None:
            raise RuntimeError("Camera not initialized")
        self._set_u32_property(eds.kEdsPropID_SaveTo, eds.kEdsSaveTo_Host, "set SaveTo Host")

        capacity = eds.EdsCapacity()
        capacity.numberOfFreeClusters = 0x7FFFFFFF
        capacity.bytesPerSector = 512
        capacity.reset = True
        eds.check(eds.EdsSetCapacity(self.camera, capacity), "EdsSetCapacity")

    def _download_dir_item_to(self, dir_item, output_dir: str):
        item_info = eds.EdsDirectoryItemInfo()
        eds.check(
            eds.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(item_info)),
            "EdsGetDirectoryItemInfo",
        )

        filename = item_info.szFileName.decode("utf-8", errors="replace")
        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, filename)

        stream_ref = eds.EdsStreamRef()
        try:
            eds.check(
                eds.EdsCreateFileStream(
                    target_path.encode("utf-8"),
                    eds.kEdsFileCreateDisposition_CreateAlways,
                    eds.kEdsAccess_ReadWrite,
                    ctypes.byref(stream_ref),
                ),
                "EdsCreateFileStream",
            )
            eds.check(eds.EdsDownload(dir_item, item_info.size, stream_ref), "EdsDownload")
            eds.check(eds.EdsDownloadComplete(dir_item), "EdsDownloadComplete")
        finally:
            if stream_ref.value:
                eds.EdsRelease(stream_ref)

        return target_path

    def download_next_photo(self, output_dir: str, timeout_s: float = 0.5):
        if self.camera is None:
            raise RuntimeError("Camera not initialized")

        signalled = self._transfer_event.wait(timeout=timeout_s)
        if not signalled:
            return None

        self._transfer_event.clear()
        dir_item = self._pending_dir_item
        self._pending_dir_item = None
        if dir_item is None:
            return None

        try:
            return self._download_dir_item_to(dir_item, output_dir)
        finally:
            eds.EdsRelease(dir_item)

    def _setupCaptureSettings(self):
        if self.camera is None:
            return
        iso_key  = self.config.configValues.get("captureISO", "100")
        iso_enum = eds.ISO_MAP.get(str(iso_key))
        if iso_enum is not None:
            val = eds.EdsUInt32(iso_enum)
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_ISOSpeed, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            )
        tv_key  = self.config.configValues.get("captureShutter", "1/500")
        tv_enum = eds.TV_MAP.get(tv_key)
        if tv_enum is not None:
            val = eds.EdsUInt32(tv_enum)
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_Tv, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            )

    # ------------------------------------------------------------------
    # Live view
    # ------------------------------------------------------------------

    def _enable_evf(self):
        val = eds.EdsUInt32(eds.kEdsEvfOutputDevice_PC)
        eds.check(
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_Evf_OutputDevice, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            ),
            "enable EVF",
        )

    def _disable_evf(self):
        val = eds.EdsUInt32(eds.kEdsEvfOutputDevice_OFF)
        try:
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_Evf_OutputDevice, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(val),
            )
        except Exception as exc:
            print(f"_disable_evf: {exc}")

    def runLiveView(self):
        if self.camera is None:
            return

        print("Init LiveView")
        time.sleep(1.0)  # Let EVF stabilize after enable
        
        frame_count = 0

        while True:
            if self.stopLiveView:
                break
                
            stream_ref = eds.EdsStreamRef()
            evf_ref    = eds.EdsEvfImageRef()
            try:
                eds.check(
                    eds.EdsCreateMemoryStream(0, ctypes.byref(stream_ref)),
                    "EdsCreateMemoryStream",
                )
                eds.check(
                    eds.EdsCreateEvfImageRef(stream_ref, ctypes.byref(evf_ref)),
                    "EdsCreateEvfImageRef",
                )
                err = eds.EdsDownloadEvfImage(self.camera, evf_ref)
                # Transient startup/not-ready states are expected while EVF warms up.
                if err in (0x00002C00, 0x0000A102):
                    time.sleep(0.03)
                    continue
                eds.check(err, "EdsDownloadEvfImage")

                ptr    = ctypes.c_void_p()
                length = eds.EdsUInt64()
                eds.check(eds.EdsGetPointer(stream_ref, ctypes.byref(ptr)), "EdsGetPointer")
                eds.check(eds.EdsGetLength(stream_ref, ctypes.byref(length)),  "EdsGetLength")

                if length.value > 0 and ptr.value:
                    raw   = (ctypes.c_uint8 * length.value).from_address(ptr.value)
                    array = np.frombuffer(raw, dtype=np.uint8)
                    img   = cv2.imdecode(array, cv2.IMREAD_COLOR)

                    if img is not None:
                        h, w = img.shape[:2]
                        left = (w - 500) // 2
                        top  = (h - 500) // 2
                        middle = img[top:top+500, left:left+500]
                        gray   = cv2.cvtColor(middle, cv2.COLOR_BGR2GRAY)

                        if frame_count > 5:
                            lap = cv2.Laplacian(gray, cv2.CV_64F)
                            self.laplacian = lap.var()

                            b, g, r, _ = cv2.mean(middle)
                            if (b + g + r) / 3 < 40:
                                self.likelyBlank = True

                        self.image = img

            except Exception as exc:
                print(f"runLiveView frame error: {exc}")
            finally:
                if evf_ref.value:
                    eds.EdsRelease(evf_ref)
                if stream_ref.value:
                    eds.EdsRelease(stream_ref)

            if self.stopLiveView:
                self.image = None
                break

            frame_count += 1

    # ------------------------------------------------------------------
    # Core imaging session
    # ------------------------------------------------------------------

    def prepForCore(self, coreId):
        self.coreId = coreId
        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.new_folder_path = os.path.join(
            self.config.configValues["BasePath"],
            coreId + "-" + timestr,
        )
        if not os.path.exists(self.new_folder_path):
            os.makedirs(self.new_folder_path)

        if platform.system() == "Darwin":
            os.system("killall -9 ptpcamerad 2>/dev/null; true")

        save_to = eds.EdsUInt32(eds.kEdsSaveTo_Host)
        eds.check(
            eds.EdsSetPropertyData(
                self.camera, eds.kEdsPropID_SaveTo, 0,
                ctypes.sizeof(eds.EdsUInt32), ctypes.byref(save_to),
            ),
            "set SaveTo Host",
        )

        capacity = eds.EdsCapacity()
        capacity.numberOfFreeClusters = 0x7FFFFFFF
        capacity.bytesPerSector       = 512
        capacity.reset                = True
        eds.check(eds.EdsSetCapacity(self.camera, capacity), "EdsSetCapacity")

        self.setupCamera(self.config.configValues.get("captureISO", "100"))

    def waitForPhoto(self, coreId):
        print("Starting waitForPhoto thread")

        temp_folder_path = os.path.join(self.new_folder_path, "scratch")
        if not os.path.exists(temp_folder_path):
            os.makedirs(temp_folder_path)

        self.photoCount   = 0
        self.newPosition  = True
        self.stopWaiting  = False

        print("Waiting for Photos")

        while True:
            signalled = self._transfer_event.wait(timeout=5.0)
            self._transfer_event.clear()

            if not signalled:
                if self.stopWaiting:
                    break
                continue

            dir_item = self._pending_dir_item
            self._pending_dir_item = None

            if dir_item is None:
                if self.stopWaiting:
                    break
                continue

            item_info = eds.EdsDirectoryItemInfo()
            try:
                eds.check(
                    eds.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(item_info)),
                    "EdsGetDirectoryItemInfo",
                )
            except Exception as exc:
                print(f"EdsGetDirectoryItemInfo failed: {exc}")
                eds.EdsDownloadCancel(dir_item)
                eds.EdsRelease(dir_item)
                continue

            filename    = item_info.szFileName.decode("utf-8", errors="replace")
            target_path = os.path.join(temp_folder_path, filename)

            stream_ref = eds.EdsStreamRef()
            try:
                eds.check(
                    eds.EdsCreateFileStream(
                        target_path.encode("utf-8"),
                        eds.kEdsFileCreateDisposition_CreateAlways,
                        eds.kEdsAccess_ReadWrite,
                        ctypes.byref(stream_ref),
                    ),
                    "EdsCreateFileStream",
                )
                eds.check(
                    eds.EdsDownload(dir_item, item_info.size, stream_ref),
                    "EdsDownload",
                )
                eds.check(
                    eds.EdsDownloadComplete(dir_item),
                    "EdsDownloadComplete",
                )
                print(f"Image saved to {target_path}")
            except Exception as exc:
                print(f"Download failed: {exc}")
                try:
                    eds.EdsDownloadCancel(dir_item)
                except Exception:
                    pass
            finally:
                if stream_ref.value:
                    eds.EdsRelease(stream_ref)
                eds.EdsRelease(dir_item)

            if self.newPosition:
                self.newPosition = False
                print("new position")
                blank_t = threading.Thread(
                    target=self.testForBlank,
                    args=(target_path,),
                    name="test-for-blank",
                    daemon=True,
                )
                blank_t.start()

            self.photoCount += 1

            if self.photoCount == int(self.config.configValues.get("StackDepth", "20")):
                print("end of position")
                self.photoCount = 0
                sort_t = threading.Thread(
                    target=self.sortPhotos,
                    args=(temp_folder_path, self.new_folder_path),
                    name="photo-sort",
                    daemon=True,
                )
                sort_t.start()
                self.newPosition = True

            if self.stopWaiting:
                break

        print("Breaking")
        print("Cleaning up scratch")
        shutil.rmtree(pathlib.Path(temp_folder_path), ignore_errors=True)
        print("waitForPhoto thread done")

    # ------------------------------------------------------------------
    # Image analysis helpers
    # ------------------------------------------------------------------

    def sortPhotos(self, temp_folder_path, new_folder_path):
        print("Sorting photos")

        files = sorted(os.listdir(temp_folder_path))
        jpeg_files = [f for f in files if f.lower().endswith(".jpg")]

        i = 1
        while True:
            created_folder_path = os.path.join(new_folder_path, f"{i:03d}")
            if not os.path.exists(created_folder_path):
                os.makedirs(created_folder_path)
                break
            i += 1

        stack_depth = int(self.config.configValues.get("StackDepth", "20"))
        for jpeg in jpeg_files[:stack_depth]:
            os.rename(
                os.path.join(temp_folder_path, jpeg),
                os.path.join(created_folder_path, jpeg),
            )
        print("done sorting")

        self.image = cv2.imread(
            os.path.join(created_folder_path, jpeg_files[round(stack_depth / 2)])
        )

        file_sizes = [
            os.path.getsize(os.path.join(created_folder_path, j))
            for j in jpeg_files[:stack_depth]
        ]

        biggest_size = max(file_sizes)
        biggest_idx  = file_sizes.index(biggest_size)
        self.stackCenter = biggest_idx

        if biggest_idx < 3 or biggest_idx > len(file_sizes) - 3:
            print("Biggest size is within 3 positions of the start or the end")
            self.requiresRefocus = True

        smallest_size = min(file_sizes)
        if biggest_size < smallest_size * 1.1:
            self.requiresRefocus = True

    def testForBlank(self, photo):
        image = cv2.imread(photo)
        if image is None:
            return
        h, w = image.shape[:2]
        x, y = w // 2, h // 2
        cropped = image[y-250:y+250, x-250:x+250]
        b, g, r, _ = cv2.mean(cropped)
        if (b + g + r) / 3 < 20:
            print("End of core")
            self.stopWaiting = True
            pub.sendMessage("coreStatus", message="end")

    def notifyCoreComplete(self):
        address = ("localhost", 6234)
        try:
            conn = Client(address, authkey=b"dendroFun")
            print("Broadcasting Core Complete Message")
            conn.send(self.new_folder_path)
            conn.close()
        except Exception:
            print("Error sending message to LinearStitch")
