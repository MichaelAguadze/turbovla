# TurboPi VLA Formalized

TurboPi VLA Formalized is a beginner-friendly recording stack for the TurboPi Advanced Kit.

It is split into two simple parts:

- The robot runs a lightweight HTTP server for camera, motor, servo, and health endpoints.
- The laptop runs the keyboard teleop client, records episodes, and saves data locally under `data/`.

The most important setup idea is this: use the robot hotspot only for first access, then move both the robot and the laptop onto the same Wi-Fi network. That gives you normal SSH, internet on the laptop, and a much smoother data-collection workflow.

## What This Repo Includes

- `robot_server/`: Flask server that runs on the TurboPi
- `client/`: keyboard teleop and recording client that runs on the laptop
- `storage/`: raw backup writer, accepted-episode writer, and LeRobot exporter
- `scripts/deploy_server.sh`: helper script to copy the server to the robot and start it
- `scripts/export_lerobot.py`: converter from this repo's episode format to a LeRobot-compatible dataset

This repo does not currently ship a dashboard app or a training script. It focuses on data collection and clean export into a format that LeRobot tooling can consume.

## Quick Start

### 1. Set up the laptop

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-laptop.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-laptop.txt
```

### 2. Connect to the robot hotspot for first access

1. Power on the TurboPi and wait for it to boot.
2. On your laptop, join the Wi-Fi network that starts with `HW`.
3. The default hotspot password is usually `hiwonder`.
4. SSH into the robot:

```bash
ssh pi@192.168.149.1
```

The default username is usually `pi`. Many stock images use `raspberrypi` as the password.

### 3. Move the robot onto your shared Wi-Fi

Once you are inside the robot:

```bash
nmcli dev wifi list
sudo nmcli device wifi connect "<SSID>" password "<PASSWORD>"
```

Your SSH session will usually disconnect right away. That is normal because the robot is leaving hotspot mode and joining the shared network.

### 4. Find the new robot IP and reconnect

Reconnect your laptop to the same Wi-Fi and find the robot IP with one of these methods:

- router connected-device list
- WonderPi or vendor tooling
- local display and keyboard on the robot, then `hostname -I`

Then SSH back in:

```bash
ssh pi@<ROBOT_IP>
```

### 5. Install robot-side Python packages

If you are using the TurboPi vendor image, `ros_robot_controller_sdk` and `cv2` usually already exist on the robot.

Install the lightweight Python deps either directly:

```bash
python3 -m pip install -r requirements-robot.txt
```

or from your laptop through the helper script:

```bash
bash scripts/deploy_server.sh deps
```

### 6. Start the robot server

If the repo is already on the robot:

```bash
python3 robot_server/server.py --port 8080
```

If the repo only exists on your laptop, use the helper script from Git Bash, WSL, or another Bash shell:

```bash
bash scripts/deploy_server.sh start
```

### 7. Start the laptop client

If you want to test driving before recording, use teleop-only mode:

```bash
python -m client.teleop --robot-ip <ROBOT_IP>
```

Then, when you are ready to collect data, start the recording client:

Shared-Wi-Fi mode:

```bash
python -m client.cli --robot-ip <ROBOT_IP>
```

Hotspot-only quick test:

```bash
python -m client
```

### 8. Export to LeRobot format

After you record accepted episodes, install the export extras:

```bash
pip install -r requirements-export.txt
```

Then convert your saved episodes:

```bash
python scripts/export_lerobot.py \
  --episodes-dir data/turbopi_nav/episodes \
  --output-dir data/turbopi_nav/lerobot \
  --repo-id <HF_DATASET_REPO>
```

By default the exporter uses `--state-source shifted_action`, which repairs older sessions where `observation.state` was incorrectly saved as the same-step action label.

Important export behavior:

- `--episodes-dir` can point at the full `episodes/` root or at one specific `session_YYYYMMDD_HHMMSS/` folder.
- The exporter converts every accepted `episode_*` folder under that path.
- If you want to leave out a bad episode, delete that episode folder before exporting.
- LeRobot may pack all exported frames into one chunked dataset video. That is normal.
- The visible video duration is `total_frames / fps`, not the wall-clock time you spent driving between episodes.

Example: export one cleaned session only

```bash
python scripts/export_lerobot.py \
  --episodes-dir data/turbopi_nav/episodes/session_20260402_114217 \
  --output-dir data/turbopi_nav/lerobot_session_20260402_114217 \
  --state-source shifted_action \
  --overwrite
```

### 9. Inspect what was recorded

If you want to manually verify that left/right motion and rotation were actually captured:

```bash
python scripts/inspect_episode.py --episodes-dir data/turbopi_nav/episodes
```

That prints a per-frame table with:

- `action_vx`, `action_vy`, `action_omega`
- `state_vx`, `state_vy`, `state_omega`
- counts for forward, backward, left, right, rotate-left, rotate-right, and stop frames
- a check that saved `state` is shifted relative to `action`

## Why Same Wi-Fi Matters

- Your laptop keeps internet access for installs, updates, and uploads.
- SSH becomes a normal LAN workflow instead of constantly switching back to the robot hotspot.
- The recording client can talk to the robot server directly while saving data on the laptop.
- It is much easier for a classroom setup where multiple students need a repeatable workflow.

After your first successful `nmcli` connection, you can make the setup persistent with `~/hiwonder-toolbox/wifi_conf.py`. The full steps are in the Wi-Fi guide.

## Docs

- [Getting Started](docs/getting-started.md)
- [Wi-Fi and SSH Guide](docs/wifi-and-ssh.md)
- [Data Collection Guide](docs/data-collection.md)
- [Troubleshooting](docs/troubleshooting.md)

## Repo Layout

```text
.
|-- client/
|-- robot_server/
|-- scripts/
|-- storage/
|-- data/                    # created automatically when you record or export
|-- requirements-laptop.txt
|-- requirements-robot.txt
|-- requirements-export.txt
`-- docs/
```

## Official Commands

Laptop:

```bash
python -m client
python -m client.cli --robot-ip <ROBOT_IP>
python -m client.teleop --robot-ip <ROBOT_IP>
python scripts/inspect_episode.py --episodes-dir data/turbopi_nav/episodes
python scripts/export_lerobot.py --episodes-dir data/turbopi_nav/episodes --output-dir data/turbopi_nav/lerobot --repo-id <HF_DATASET_REPO>
```

Robot, when the repo is already on the robot:

```bash
python3 robot_server/server.py --port 8080
```

Laptop helper for deploying the server:

```bash
bash scripts/deploy_server.sh deps
bash scripts/deploy_server.sh start
```

## Notes for Open-Source Users

- Runtime data is not tracked in this repo. Recording runs create timestamped folders under `data/<dataset_name>/`.
- Accepted episodes are stored as one folder per episode with `video.mp4` plus `data.parquet`.
- Temporary validation outputs such as `data/workflow_validation/` are safe to delete after you finish checking the pipeline.
- The recorder now saves `observation.state` as the previous normalized action, not the current action, to avoid target leakage during training.
- `ros_robot_controller_sdk` is TurboPi-specific and comes from the robot image, not from `pip`.
- If your robot image differs from the common Hiwonder defaults, check the vendor network guide first and then come back to this repo.

## References

- [Hiwonder TurboPi network setup](https://docs.hiwonder.com/projects/TurboPi/en/advanced/docs/7.network_configuration.html)
- [Hiwonder TurboPi getting ready](https://docs.hiwonder.com/projects/TurboPi/en/latest/docs/1.getting_ready.html)
- [Hugging Face LeRobot datasets docs](https://huggingface.co/docs/lerobot/main/en/lerobot-dataset-v3)
