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

        self.preview_label = ttk.Label(preview, text="Live view image will appear here", anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        dl = ttk.LabelFrame(container, text="Physical Shutter Auto-Download", padding=8)
        dl.pack(fill=tk.X, pady=(10, 0))

        self.output_dir_var = tk.StringVar(value=self.config.configValues.get("BasePath", os.path.expanduser("~")))
        ttk.Entry(dl, textvariable=self.output_dir_var, width=72).grid(row=0, column=0, sticky="we")
        ttk.Button(dl, text="Browse", command=self.pick_output_dir).grid(row=0, column=1, padx=(8, 0))

        self.start_dl_btn = ttk.Button(dl, text="Start Auto-Download", command=self.start_download, state=tk.DISABLED)
        self.start_dl_btn.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.stop_dl_btn = ttk.Button(dl, text="Stop Auto-Download", command=self.stop_download, state=tk.DISABLED)
        self.stop_dl_btn.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

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
            if self.camera is not None and not self.camera.stopLiveView and self.camera.image is not None:
                frame = self.camera.image
                h, w = frame.shape[:2]

                max_w = 840
                max_h = 420
                scale = min(max_w / w, max_h / h, 1.0)
                if scale < 1.0:
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

                # Keep OpenCV frame in BGR for imencode; converting to RGB here
                # causes a channel swap when Tk decodes the PNG.
                ok, encoded = cv2.imencode(".png", frame)
                if ok:
                    png_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
                    self.preview_photo = tk.PhotoImage(data=png_b64)
                    self.preview_label.configure(image=self.preview_photo, text="")
            elif self.camera is None or self.camera.stopLiveView:
                self.preview_label.configure(image="", text="Live view image will appear here")
                self.preview_photo = None
        except Exception:
            pass

        self.root.after(80, self._refresh_preview)

    def connect_camera(self):
        if self.camera is not None:
            self._log("Camera already connected")
            return

        try:
            self.camera = CameraControl(self.config)
            if self.camera.camera is None:
                self.camera = None
                raise RuntimeError("Camera initialization failed")

            model = self.camera._get_product_name()
            self.status_var.set(f"Connected: {model}")
            self._log(f"Connected to {model}")

            self.live_btn.configure(state=tk.NORMAL)
            self.apply_shoot_btn.configure(state=tk.NORMAL)
            self.apply_live_btn.configure(state=tk.NORMAL)
            self.start_dl_btn.configure(state=tk.NORMAL)
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
                self.camera.set_iso(self.live_iso_var.get().strip())
                self.camera.set_shutter(self.live_shutter_var.get().strip())
                self.camera.set_aperture(self.live_fstop_var.get().strip())
                self.camera.setLiveView(True)
                self.live_btn.configure(text="Stop LiveView")
                self._log("LiveView started (LiveView profile applied)")
            except Exception as exc:
                self._log(f"LiveView start failed: {exc}")
                messagebox.showerror("LiveView Error", str(exc))
        else:
            try:
                self.camera.setLiveView(False)
                self.camera.set_iso(self.shoot_iso_var.get().strip())
                self.camera.set_shutter(self.shoot_shutter_var.get().strip())
                self.camera.set_aperture(self.shoot_fstop_var.get().strip())
                self.camera.set_white_balance(self.shoot_wb_var.get().strip())
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

        self.start_dl_btn.configure(state=tk.DISABLED)
        self.stop_dl_btn.configure(state=tk.NORMAL)
        self._log(f"Auto-download started: {out_dir}")

    def stop_download(self):
        self.download_running = False
        self.stop_dl_btn.configure(state=tk.DISABLED)
        self.start_dl_btn.configure(state=tk.NORMAL)
        self._log("Auto-download stopping")

    def _download_worker(self):
        output_dir = self.output_dir_var.get().strip()
        while self.download_running and self.camera is not None:
            try:
                saved_path = self.camera.download_next_photo(output_dir=output_dir, timeout_s=0.5)
                if saved_path:
                    self.download_count += 1
                    self.download_count_var.set(f"Downloaded: {self.download_count}")
                    self._log(f"Downloaded: {saved_path}")
            except Exception as exc:
                self._log(f"Download error: {exc}")
                time.sleep(0.3)

        self.root.after(0, lambda: self.stop_dl_btn.configure(state=tk.DISABLED))
        self.root.after(0, lambda: self.start_dl_btn.configure(state=tk.NORMAL if self.camera else tk.DISABLED))

    def _on_close(self):
        self.download_running = False
        try:
            self.save_preferences()
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
