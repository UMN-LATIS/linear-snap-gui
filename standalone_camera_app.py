#!/usr/bin/env python3
"""Standalone camera utility app using CameraControl.

Features:
- Connect to camera
- Toggle live view
- Separate Shooting and LiveView setting profiles
- Auto-apply LiveView profile when starting EVF and Shooting profile when stopping EVF
- Display live Laplacian focus metric
- Auto-download photos triggered by physical shutter button
"""

import os
import threading
import queue
import time
import base64
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
import edsdk as eds
from config import LSConfig
from CameraControl import CameraControl


class StandaloneCameraApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Standalone Camera Control")
        self.root.geometry("980x760")

        self.config = LSConfig()
        self.camera = None

        self.download_running = False
        self.download_thread = None
        self.log_queue = queue.Queue()
        self.download_count = 0
        self.preview_photo = None
        self.live_window = None
        self.live_window_label = None
        self.live_window_photo = None
        self.live_window_user_closed = False
        self.capture_preview_window = None
        self.capture_preview_label = None
        self.capture_preview_photo = None

        self.iso_values = sorted(
            [k for k in eds.ISO_MAP.keys() if k != "Auto"],
            key=lambda x: int(x),
        )
        self.iso_values.insert(0, "Auto")

        def _tv_key(k: str):
            if "/" in k:
                num, den = k.split("/")
                try:
                    return float(num) / float(den)
                except Exception:
                    return 0.0
            try:
                return float(k)
            except Exception:
                return 0.0

        self.shutter_values = sorted(eds.TV_MAP.keys(), key=_tv_key, reverse=True)

        self.fstop_values = sorted(
            eds.AV_MAP.keys(),
            key=lambda x: float(x),
        )
        self.wb_values = list(eds.WB_MAP.keys())
        self.rotate_values = ["0", "90", "180", "270"]

        self._build_ui()
        self._pump_logs()
        self._refresh_metrics()
        self._refresh_preview()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        top = ttk.LabelFrame(container, text="Connection", padding=8)
        top.pack(fill=tk.X)

        self.connect_btn = ttk.Button(top, text="Connect Camera", command=self.connect_camera)
        self.connect_btn.pack(side=tk.LEFT)

        self.live_btn = ttk.Button(top, text="Start LiveView", command=self.toggle_liveview, state=tk.DISABLED)
        self.live_btn.pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        settings = ttk.LabelFrame(container, text="Exposure Settings", padding=8)
        settings.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(settings, text="Shooting Settings").grid(row=0, column=0, columnspan=5, sticky="w")

        ttk.Label(settings, text="ISO").grid(row=1, column=0, sticky="w")
        self.shoot_iso_var = tk.StringVar(value=self.config.configValues.get("captureISO", "100"))
        self.shoot_iso_cb = ttk.Combobox(settings, textvariable=self.shoot_iso_var, values=self.iso_values, width=12, state="readonly")
        self.shoot_iso_cb.grid(row=2, column=0, sticky="w", padx=(0, 12))

        ttk.Label(settings, text="Shutter").grid(row=1, column=1, sticky="w")
        self.shoot_shutter_var = tk.StringVar(value=self.config.configValues.get("captureShutter", "1/500"))
        self.shoot_shutter_cb = ttk.Combobox(settings, textvariable=self.shoot_shutter_var, values=self.shutter_values, width=12, state="readonly")
        self.shoot_shutter_cb.grid(row=2, column=1, sticky="w", padx=(0, 12))

        ttk.Label(settings, text="F-stop").grid(row=1, column=2, sticky="w")
        self.shoot_fstop_var = tk.StringVar(value=self.config.configValues.get("captureFStop", "5.6"))
        self.shoot_fstop_cb = ttk.Combobox(settings, textvariable=self.shoot_fstop_var, values=self.fstop_values, width=12, state="readonly")
        self.shoot_fstop_cb.grid(row=2, column=2, sticky="w", padx=(0, 12))

        ttk.Label(settings, text="White Balance").grid(row=1, column=3, sticky="w")
        self.shoot_wb_var = tk.StringVar(value=self.config.configValues.get("captureWhiteBalance", "Auto"))
        self.shoot_wb_cb = ttk.Combobox(settings, textvariable=self.shoot_wb_var, values=self.wb_values, width=16, state="readonly")
        self.shoot_wb_cb.grid(row=2, column=3, sticky="w", padx=(0, 12))

        self.apply_shoot_btn = ttk.Button(settings, text="Apply Shooting", command=self.apply_shooting_profile, state=tk.DISABLED)
        self.apply_shoot_btn.grid(row=2, column=4, sticky="w")

        ttk.Separator(settings, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew", pady=(10, 10))

        ttk.Label(settings, text="LiveView Settings").grid(row=4, column=0, columnspan=5, sticky="w")

        ttk.Label(settings, text="ISO").grid(row=5, column=0, sticky="w")
        self.live_iso_var = tk.StringVar(value=self.config.configValues.get("previewISO", "100"))
        self.live_iso_cb = ttk.Combobox(settings, textvariable=self.live_iso_var, values=self.iso_values, width=12, state="readonly")
        self.live_iso_cb.grid(row=6, column=0, sticky="w", padx=(0, 12))

        ttk.Label(settings, text="Shutter").grid(row=5, column=1, sticky="w")
        self.live_shutter_var = tk.StringVar(value=self.config.configValues.get("previewShutter", "1/15"))
        self.live_shutter_cb = ttk.Combobox(settings, textvariable=self.live_shutter_var, values=self.shutter_values, width=12, state="readonly")
        self.live_shutter_cb.grid(row=6, column=1, sticky="w", padx=(0, 12))

        ttk.Label(settings, text="F-stop").grid(row=5, column=2, sticky="w")
        self.live_fstop_var = tk.StringVar(value=self.config.configValues.get("previewFStop", "5.6"))
        self.live_fstop_cb = ttk.Combobox(settings, textvariable=self.live_fstop_var, values=self.fstop_values, width=12, state="readonly")
        self.live_fstop_cb.grid(row=6, column=2, sticky="w", padx=(0, 12))

        self.apply_live_btn = ttk.Button(settings, text="Apply LiveView", command=self.apply_live_profile, state=tk.DISABLED)
        self.apply_live_btn.grid(row=6, column=4, sticky="w")

        metrics = ttk.LabelFrame(container, text="Live Metrics", padding=8)
        metrics.pack(fill=tk.X, pady=(10, 0))

        self.lap_var = tk.StringVar(value="Laplacian: --")
        ttk.Label(metrics, textvariable=self.lap_var).pack(side=tk.LEFT)

        self.download_count_var = tk.StringVar(value="Downloaded: 0")
        ttk.Label(metrics, textvariable=self.download_count_var).pack(side=tk.LEFT, padx=20)

        preview = ttk.LabelFrame(container, text="LiveView Preview", padding=8)
        preview.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.preview_label = ttk.Label(preview, text="LiveView stream opens in a separate window.", anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        dl = ttk.LabelFrame(container, text="Physical Shutter Auto-Download", padding=8)
        dl.pack(fill=tk.X, pady=(10, 0))

        self.output_dir_var = tk.StringVar(value=self.config.configValues.get("BasePath", os.path.expanduser("~")))
        ttk.Entry(dl, textvariable=self.output_dir_var, width=72).grid(row=0, column=0, sticky="we")
        ttk.Button(dl, text="Browse", command=self.pick_output_dir).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(dl, text="Rotate").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.rotate_var = tk.StringVar(value=self.config.configValues.get("standaloneRotate", "0"))
        self.rotate_cb = ttk.Combobox(dl, textvariable=self.rotate_var, values=self.rotate_values, width=8, state="readonly")
        self.rotate_cb.grid(row=1, column=0, sticky="w", padx=(55, 0), pady=(8, 0))
        self.rotate_cb.bind("<<ComboboxSelected>>", lambda _evt: self.save_preferences())

        self.show_image_preview_var = tk.BooleanVar(
            value=self.config.configValues.get("standaloneShowImagePreview", "0") == "1"
        )
        self.show_image_preview_cb = ttk.Checkbutton(
            dl,
            text="Show image preview",
            variable=self.show_image_preview_var,
            command=self._on_toggle_capture_preview,
        )
        self.show_image_preview_cb.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        self.toggle_dl_btn = ttk.Button(dl, text="Start Auto-Download", command=self.toggle_download, state=tk.DISABLED)
        self.toggle_dl_btn.grid(row=2, column=0, sticky="w", pady=(8, 0))

        log_box = ttk.LabelFrame(container, text="Log", padding=8)
        log_box.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = tk.Text(log_box, height=12, wrap="word", state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {msg}")

    def _pump_logs(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, line + "\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self._pump_logs)

    def _refresh_metrics(self):
        if self.camera is not None:
            lap = self.camera.laplacian
            if lap is None or lap == 0:
                self.lap_var.set("Laplacian: --")
            else:
                self.lap_var.set(f"Laplacian: {lap:.2f}")
        self.root.after(200, self._refresh_metrics)

    def _refresh_preview(self):
        try:
            if self.camera is not None and not self.camera.stopLiveView and self.camera.image is not None and not self.live_window_user_closed:
                if self.live_window is None or not self.live_window.winfo_exists():
                    return

                frame = self.camera.image
                frame = self._rotate_image(frame, self._get_rotation_degrees())
                target_w = max(self.live_window_label.winfo_width(), 1)
                target_h = max(self.live_window_label.winfo_height(), 1)
                frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

                # Keep OpenCV frame in BGR for imencode; converting to RGB here
                # causes a channel swap when Tk decodes the PNG.
                ok, encoded = cv2.imencode(".png", frame)
                if ok and self.live_window_label is not None:
                    png_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
                    self.live_window_photo = tk.PhotoImage(data=png_b64)
                    self.live_window_label.configure(image=self.live_window_photo, text="")
            elif self.camera is None or self.camera.stopLiveView:
                self._close_live_window()
        except Exception:
            pass

        self.root.after(80, self._refresh_preview)

    def _get_rotation_degrees(self) -> int:
        try:
            deg = int((self.rotate_var.get() if hasattr(self, "rotate_var") else "0").strip())
            if deg in (0, 90, 180, 270):
                return deg
        except Exception:
            pass
        return 0

    def _rotate_image(self, image, degrees: int):
        if image is None or degrees == 0:
            return image
        if degrees == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        if degrees == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        if degrees == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return image

    def _rotate_saved_file(self, path: str, degrees: int):
        if degrees == 0:
            return
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self._log(f"Rotate skipped (unable to read image): {path}")
            return
        rotated = self._rotate_image(image, degrees)
        if rotated is None:
            return

        root, ext = os.path.splitext(path)
        if not ext:
            # Fallback should be rare, but ensure imwrite has a known extension.
            ext = ".jpg"
        tmp_path = f"{root}.rotating{ext}"
        ok = cv2.imwrite(tmp_path, rotated)
        if not ok:
            self._log(f"Rotate failed (write error): {path}")
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return
        os.replace(tmp_path, path)

    def connect_camera(self):
        if self.camera is not None:
            self._log("Camera already connected")
            return

        try:
            self.camera = CameraControl(self.config)
            if self.camera.camera is None:
                detail = self.camera.init_error or "unknown error"
                self.camera = None
                raise RuntimeError(f"Camera initialization failed: {detail}")

            model = self.camera._get_product_name()
            self.status_var.set(f"Connected: {model}")
            self._log(f"Connected to {model}")

            self.live_btn.configure(state=tk.NORMAL)
            self.apply_shoot_btn.configure(state=tk.NORMAL)
            self.apply_live_btn.configure(state=tk.NORMAL)
            self.toggle_dl_btn.configure(state=tk.NORMAL)
            self.connect_btn.configure(state=tk.DISABLED)

            self._apply_camera_supported_dropdowns()
        except Exception as exc:
            self._log(f"Connect failed: {exc}")
            messagebox.showerror("Camera Error", str(exc))

    def _sort_iso_values(self, values):
        non_auto = [v for v in values if v != "Auto"]
        non_auto.sort(key=lambda x: int(x))
        if "Auto" in values:
            return ["Auto"] + non_auto
        return non_auto

    def _sort_shutter_values(self, values):
        def _tv_key(k: str):
            if "/" in k:
                n, d = k.split("/")
                try:
                    return float(n) / float(d)
                except Exception:
                    return 0.0
            try:
                return float(k)
            except Exception:
                return 0.0

        return sorted(values, key=_tv_key, reverse=True)

    def _sort_aperture_values(self, values):
        return sorted(values, key=lambda x: float(x))

    def _set_combo_values(self, combo, var, values, preferred):
        combo["values"] = values
        if preferred in values:
            var.set(preferred)
        elif values:
            var.set(values[0])

    def _apply_camera_supported_dropdowns(self):
        if self.camera is None:
            return

        supported = self.camera.get_supported_setting_labels()

        iso_vals = supported.get("iso") or self.iso_values
        tv_vals = supported.get("shutter") or self.shutter_values
        av_vals = supported.get("aperture") or self.fstop_values
        wb_vals = supported.get("white_balance") or self.wb_values

        iso_vals = self._sort_iso_values(list(dict.fromkeys(iso_vals)))
        tv_vals = self._sort_shutter_values(list(dict.fromkeys(tv_vals)))
        av_vals = self._sort_aperture_values(list(dict.fromkeys(av_vals)))
        wb_vals = [w for w in self.wb_values if w in set(wb_vals)] or self.wb_values

        self._set_combo_values(self.shoot_iso_cb, self.shoot_iso_var, iso_vals, self.shoot_iso_var.get())
        self._set_combo_values(self.live_iso_cb, self.live_iso_var, iso_vals, self.live_iso_var.get())
        self._set_combo_values(self.shoot_shutter_cb, self.shoot_shutter_var, tv_vals, self.shoot_shutter_var.get())
        self._set_combo_values(self.live_shutter_cb, self.live_shutter_var, tv_vals, self.live_shutter_var.get())
        self._set_combo_values(self.shoot_fstop_cb, self.shoot_fstop_var, av_vals, self.shoot_fstop_var.get())
        self._set_combo_values(self.live_fstop_cb, self.live_fstop_var, av_vals, self.live_fstop_var.get())
        self._set_combo_values(self.shoot_wb_cb, self.shoot_wb_var, wb_vals, self.shoot_wb_var.get())

        self._log(
            f"Supported values loaded: ISO={len(iso_vals)}, Shutter={len(tv_vals)}, F-stop={len(av_vals)}, WB={len(wb_vals)}"
        )

    def save_preferences(self):
        self.config.configValues["captureISO"] = self.shoot_iso_var.get().strip()
        self.config.configValues["captureShutter"] = self.shoot_shutter_var.get().strip()
        self.config.configValues["captureFStop"] = self.shoot_fstop_var.get().strip()
        self.config.configValues["captureWhiteBalance"] = self.shoot_wb_var.get().strip()

        self.config.configValues["previewISO"] = self.live_iso_var.get().strip()
        self.config.configValues["previewShutter"] = self.live_shutter_var.get().strip()
        self.config.configValues["previewFStop"] = self.live_fstop_var.get().strip()
        self.config.configValues["standaloneRotate"] = str(self._get_rotation_degrees())
        self.config.configValues["standaloneShowImagePreview"] = "1" if self.show_image_preview_var.get() else "0"

        self.config.configValues["BasePath"] = self.output_dir_var.get().strip() or self.config.configValues.get("BasePath", "")
        self.config.save_config()
        self._log("Preferences saved")

    def apply_shooting_profile(self):
        if self.camera is None:
            return
        try:
            iso = self.shoot_iso_var.get().strip()
            shutter = self.shoot_shutter_var.get().strip()
            fstop = self.shoot_fstop_var.get().strip()
            wb = self.shoot_wb_var.get().strip()
            self.camera.apply_exposure_settings(iso, shutter, fstop, wb)
            self._log(f"Shooting profile applied: ISO {iso}, Shutter {shutter}, F/{fstop}, WB {wb}")
            self.save_preferences()
        except Exception as exc:
            self._log(f"Shooting profile apply failed: {exc}")
            messagebox.showerror("Exposure Error", str(exc))

    def apply_live_profile(self):
        if self.camera is None:
            return
        try:
            iso = self.live_iso_var.get().strip()
            shutter = self.live_shutter_var.get().strip()
            fstop = self.live_fstop_var.get().strip()
            self.camera.apply_exposure_settings(iso, shutter, fstop)
            self._log(f"LiveView profile applied: ISO {iso}, Shutter {shutter}, F/{fstop}")
            self.save_preferences()
        except Exception as exc:
            self._log(f"LiveView profile apply failed: {exc}")
            messagebox.showerror("Exposure Error", str(exc))

    def toggle_liveview(self):
        if self.camera is None:
            return

        if self.camera.stopLiveView:
            try:
                self.live_window_user_closed = False
                self.camera.set_iso(self.live_iso_var.get().strip())
                self.camera.set_shutter(self.live_shutter_var.get().strip())
                self.camera.set_aperture(self.live_fstop_var.get().strip())
                self.camera.setLiveView(True)
                self._ensure_live_window()
                self.live_btn.configure(text="Stop LiveView")
                self._log("LiveView started (LiveView profile applied)")
            except Exception as exc:
                self._log(f"LiveView start failed: {exc}")
                messagebox.showerror("LiveView Error", str(exc))
        else:
            try:
                self.live_window_user_closed = True
                self.camera.setLiveView(False)
                self.camera.set_iso(self.shoot_iso_var.get().strip())
                self.camera.set_shutter(self.shoot_shutter_var.get().strip())
                self.camera.set_aperture(self.shoot_fstop_var.get().strip())
                self.camera.set_white_balance(self.shoot_wb_var.get().strip())
                self._close_live_window()
                self.live_btn.configure(text="Start LiveView")
                self._log("LiveView stopped (Shooting profile restored)")
                self.save_preferences()
            except Exception as exc:
                self._log(f"LiveView stop/profile restore failed: {exc}")
                messagebox.showerror("LiveView Error", str(exc))

    def pick_output_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if chosen:
            self.output_dir_var.set(chosen)

    def toggle_download(self):
        if self.download_running:
            self.stop_download()
        else:
            self.start_download()

    def start_download(self):
        if self.camera is None:
            return
        if self.download_running:
            return

        out_dir = self.output_dir_var.get().strip()
        if not out_dir:
            messagebox.showwarning("Output Directory", "Please choose an output directory.")
            return

        try:
            os.makedirs(out_dir, exist_ok=True)
            self.camera.prepare_host_download()
        except Exception as exc:
            self._log(f"Prepare download failed: {exc}")
            messagebox.showerror("Download Error", str(exc))
            return

        self.download_running = True
        self.download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self.download_thread.start()

        self.toggle_dl_btn.configure(text="Stop Auto-Download", state=tk.NORMAL)
        self._log(f"Auto-download started: {out_dir}")

    def stop_download(self):
        self.download_running = False
        self.toggle_dl_btn.configure(text="Start Auto-Download", state=(tk.NORMAL if self.camera else tk.DISABLED))
        self._log("Auto-download stopping")

    def _download_worker(self):
        output_dir = self.output_dir_var.get().strip()
        while self.download_running and self.camera is not None:
            try:
                saved_path = self.camera.download_next_photo(output_dir=output_dir, timeout_s=0.5)
                if saved_path:
                    rotation = self._get_rotation_degrees()
                    if rotation:
                        self._rotate_saved_file(saved_path, rotation)
                    self.download_count += 1
                    self.root.after(0, lambda c=self.download_count: self.download_count_var.set(f"Downloaded: {c}"))
                    if self.show_image_preview_var.get():
                        self.root.after(0, lambda p=saved_path: self._show_captured_image_preview(p))
                    if rotation:
                        self._log(f"Downloaded: {saved_path} (rotated {rotation} deg)")
                    else:
                        self._log(f"Downloaded: {saved_path}")
            except Exception as exc:
                self._log(f"Download error: {exc}")
                time.sleep(0.3)

        self.root.after(0, lambda: self.toggle_dl_btn.configure(
            text="Start Auto-Download",
            state=(tk.NORMAL if self.camera else tk.DISABLED),
        ))

    def _on_toggle_capture_preview(self):
        self.save_preferences()
        if not self.show_image_preview_var.get():
            self._close_capture_preview_window()

    def _close_capture_preview_window(self):
        if self.capture_preview_window is not None and self.capture_preview_window.winfo_exists():
            self.capture_preview_window.destroy()
        self.capture_preview_window = None
        self.capture_preview_label = None
        self.capture_preview_photo = None

    def _ensure_live_window(self):
        if self.live_window is not None and self.live_window.winfo_exists():
            return

        self.live_window = tk.Toplevel(self.root)
        self.live_window.title("LiveView Stream")
        self.live_window.geometry("1000x700")
        self.live_window.minsize(400, 300)
        self.live_window_label = ttk.Label(self.live_window, text="Live view image will appear here", anchor="center")
        self.live_window_label.pack(fill=tk.BOTH, expand=True)

        def _close_live_window():
            if self.camera is not None and not self.camera.stopLiveView:
                self.live_window_user_closed = True
                self.toggle_liveview()
            else:
                self._close_live_window()

        self.live_window.protocol("WM_DELETE_WINDOW", _close_live_window)

    def _close_live_window(self):
        if self.live_window is not None and self.live_window.winfo_exists():
            self.live_window.destroy()
        self.live_window = None
        self.live_window_label = None
        self.live_window_photo = None

    def _show_captured_image_preview(self, image_path: str):
        if not self.show_image_preview_var.get():
            return

        if self.capture_preview_window is None or not self.capture_preview_window.winfo_exists():
            self.capture_preview_window = tk.Toplevel(self.root)
            self.capture_preview_window.title("Image Preview")
            self.capture_preview_window.geometry("1000x700")
            self.capture_preview_window.minsize(400, 300)
            self.capture_preview_label = ttk.Label(self.capture_preview_window, text="Waiting for image...", anchor="center")
            self.capture_preview_label.pack(fill=tk.BOTH, expand=True)
            self.capture_preview_window.protocol("WM_DELETE_WINDOW", self._close_capture_preview_window)

        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            self._log(f"Image preview skipped (unable to read file): {image_path}")
            return

        h, w = image.shape[:2]
        max_w = 1400
        max_h = 900
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        ok, encoded = cv2.imencode(".png", image)
        if not ok or self.capture_preview_label is None:
            return

        png_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
        self.capture_preview_photo = tk.PhotoImage(data=png_b64)
        self.capture_preview_label.configure(image=self.capture_preview_photo, text="")
        self.capture_preview_window.lift()

    def _on_close(self):
        self.download_running = False
        try:
            self.save_preferences()
            self._close_capture_preview_window()
            self._close_live_window()
            if self.camera is not None:
                try:
                    self.camera.setLiveView(False)
                except Exception:
                    pass
                self.camera.cleanup()
        finally:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StandaloneCameraApp(root)
    root.mainloop()
