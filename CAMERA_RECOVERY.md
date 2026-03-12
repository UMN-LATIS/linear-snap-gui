# EDSDK Camera Connection Recovery Guide

## Problem: `EdsOpenSession: EDSDK error 0x000000C0 (SESSION_CONNECTION_ERROR)`

This error means the camera enumeration succeeded, but the SDK cannot open a session (exclusive lock on the camera).

**Root causes:**
1. Camera in manual focus mode with some modes incompatible with live view
2. Camera's USB mode setting 
3. Another application holding the session  
4. Camera firmware in a locked state
5. USB connection timing/state issue

---

## Recovery Steps (in order):

### Step 1: Check Camera Physical State
- [ ] Camera powered on
- [ ] LCD screen responsive
- [ ] No error message displayed on camera
- [ ] Not in video recording mode
- [ ] Not in a lens error state

### Step 2: Check USB Connection
- [ ] USB cable connected
- [ ] Try different USB port on computer
- [ ] Unplug USB, wait 2 seconds, replug
- [ ] Check System Report → USB for camera presence

### Step 3: Camera Settings Reset
**On the camera:**
1. Open Menu → Setup → Clear Settings
2. Select "Clear All Camera Settings" → OK
3. Power cycle: Turn off → wait 3 sec → turn on

### Step 4: USB Transfer Mode
**On the camera:**
1. Menu → Setup → USB
2. Change to "PTP (Picture Transfer Protocol)" if available
3. Or select "Auto" for detection

### Step 5: Force Release Old Sessions
**On macOS:**
```bash
# Kill any lingering processes
killall -9 ptpcamerad 2>/dev/null; true
killall -9 PTPCamera 2>/dev/null; true

# Kill any Python processes holding EDSDK
killall -9 python3 2>/dev/null; true
```

**Then restart the app.**

### Step 6: Reset EDSDK State
Run this test script from Terminal:
```bash
cd /Users/colin/Documents/Development/embedded\ tools/miniMacro-Gui
python test_session_only.py
```

This will:
- Try fresh SDK initialization
- Enumerate camera
- Attempt session open
- Report exact error with context

---

## Detailed Error Information

**Error Code:** `0x000000C0`  
**Name:** `SESSION_CONNECTION_ERROR`  
**Hex:** `0xC0` (192 decimal)

**This is NOT a normal documented EDSDK error.** It indicates the camera is rejecting session attempts for an unusual reason.

---

## If Recovery Steps Don't Work:

### Camera Firmware Check
1. Power off camera
2. Check current firmware version in camera menu
3. If available, update to latest firmware from Canon website

### USB Driver Reset (macOS)
```bash
# Remove USB device from system
cd /System/Library/Extensions
sudo rm -rf IOUSBMassStorageClass.kext 2>/dev/null; true

# Then reboot
```

### Last Resort: Hard Reset Camera
1. Remove battery
2. Wait 30 seconds  
3. Reinsert battery
4. Power on
5. Format SD card in camera if available

---

## Testing Live View After Recovery

Once `test_session_only.py` shows `OK` for EdsOpenSession:

```bash
python test_minimal_liveview.py
```

Should show frames captured with ✓ status.

---

## Notes

- The retry logic in CameraControl.py will attempt 3 times with 2-sec delays
- Each retry reinitializes the SDK
- After 3 failed attempts, it reports the error
- Live view requires an active, responsive session

If you get past this error, live view should stream ~15 FPS at 704x1056 resolution.
