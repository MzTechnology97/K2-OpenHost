# Chamber camera (Creality CAM)

Updated: **2026-10-14**. [Italiano](../it/CAMERA.md)

The K2 Pro chamber camera works on the external host with plain crowsnest and the stock `uvcvideo` driver. It needs two settings, without which the image turns black.

## Setup

In `~/printer_data/config/crowsnest.conf`, in the `[cam]` section of the camera:

```ini
[cam 1]
mode: ustreamer
port: 8080
device: /dev/v4l/by-id/usb-Creality_3D_Technology_CREALITY_CAM_<serial>-video-index0
resolution: 1920x1080
max_fps: 25
v4l2ctl: brightness=128,contrast=128,sharpness=128,saturation=128,power_line_frequency=1,auto_exposure=3
```

- `max_fps: 25` is required. At 30 fps the camera's auto exposure settles on a black image.
- `v4l2ctl` holds the controls of the stock firmware. Crowsnest sends them to the camera before it starts the stream, which is the order this camera needs.
- Then **reboot the host**. The camera only picks up the controls correctly after a power cycle, and rebooting the CM5 is what power-cycles it.

The [installer helper](https://github.com/MzTechnology97/k2-openhost-installer-helper) does this when it installs crowsnest with the camera connected. `./helper.sh install creality-cam` runs only this step. It changes the section whose `device` is this camera and keeps a backup of `crowsnest.conf`.

Use the `/dev/v4l/by-id/...` path rather than `/dev/video0`, so the section still points at this camera when other cameras are connected.

![Chamber camera on the CM5: crowsnest at 25 fps with the stock controls](../images/creality-cam-cm5-25fps.jpg)

*The chamber camera on the reference printer with these settings, 2026-10-14, during a PETG-CF print: stock `uvcvideo` driver, crowsnest/ustreamer at 1920x1080 and 25 fps, the controls above.*

## The camera

| | |
|---|---|
| USB | `1d6c:0103` "CREALITY CAM", Fullhan FH8636, firmware `STD-9613V2` |
| Class | UVC 1.00, video on a **bulk** endpoint (`0x83`) |
| Formats | MJPEG, YUYV, H.264; 640x360 to 1920x1080; 5 to 30 fps |
| Controls | brightness, contrast, saturation, sharpness (0-255, default 128), gain (0-100, no visible effect), power_line_frequency, white balance, auto_exposure, exposure_time_absolute |

## Firmware behaviour

These are behaviours of the camera's firmware. The stock T113 shows them too: its `ustreamer` runs at 25 fps and its start-up script sets the controls before the first stream.

| Behaviour | Effect | What to do |
|---|---|---|
| Auto exposure at **30 fps** with the controls set | The exposure settles on a black image (mean 19/255) within a second | `max_fps: 25` |
| Controls sent **before** the first stream after power-on, at 25 fps | Bright image, like the stock firmware (mean 189/255 with the chamber LED at 100 %) | `v4l2ctl` in crowsnest, then reboot |
| No controls sent | Normal, darker image (mean ~72) | — |
| First control change **while streaming** after power-on | The image goes black; a second change brings it back, in the darker mode | Change `v4l2ctl` and reboot instead of changing controls live |
| `auto_exposure` 1 (manual) or 2 (shutter priority) | The image freezes black until the camera is power cycled | Use 3 (aperture priority, as stock) or 0 |
| `gain` | No visible effect | — |

With the chamber LED at 100 %, about 45 % of the pixels are clipped in the bright mode, as on the stock firmware. If that is too much, lower `brightness` in `v4l2ctl` and reboot.

## What was checked (2026-10-12 to 2026-10-14)

The camera turned black on the CM5 whenever its controls were set at start-up. The causes below were tested one at a time on the reference printer. A CM5 reboot is the only way to power-cycle the camera, so every test needed one.

- **USB hub and power management:** the same hub works on the T113. USB autosuspend set to `on` changed nothing.
- **Timing of the controls:** at 30 fps, sending the controls 3 s, 15 s or 18 s after power-on, all before the first stream, still gave black. At 25 fps, 3 s and 15 s both gave the bright image.
- **Kernel driver** (`uvcvideo` 6.12 on the CM5, 5.4 on the T113): two real differences, confirmed with `usbmon` and a patched module built for the test.
  - At probe time, kernel 6.8+ writes `power_line_frequency` twice (off, then back) to find out which values the camera supports. 5.4 does not do this.
  - Kernel 6.12 sends `CLEAR_FEATURE(ENDPOINT_HALT)` to the bulk endpoint only when a stream stops. Without it, the first stream after power-on returns only 12-byte error headers. ustreamer recovers by itself: it times out after 2 s, restarts, and the second stream works.
  - With both fixed, the image was still black at 30 fps. With the stock driver it is bright at 25 fps. So the driver is **not** the cause, and no patched module is needed.
- **ustreamer:** `strace` shows it sends no image controls. Its only differences from the stock firmware's stream were the frame rate and the buffer count.

## H.264

The camera can also send H.264 directly. For now K2-OpenHost stays on MJPEG:

- ustreamer, the crowsnest default, streams only MJPEG. Showing H.264 in Mainsail needs a WebRTC server such as go2rtc, set up as a separate webcam service.
- The CM5 (Raspberry Pi 5 family) has no hardware H.264 encoder or decoder. Snapshots for timelapse, Mobileraker or OctoEverywhere would have to decode H.264 frames on the CPU, whereas MJPEG frames are already JPEG snapshots.
- The camera has a single video interface, so it cannot send H.264 and MJPEG at the same time.
- The firmware behaviour above has not been tested in H.264 mode.

H.264 mainly saves bandwidth: about 4 MB/s of MJPEG at 1080p and 25 fps, against a few Mbit/s of H.264. That matters for remote viewing over a slow link, not on the local network.
