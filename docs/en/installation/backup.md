# Backup and restore

## Local backup with the helper

```bash
./helper.sh backup     # menu 20
./helper.sh restore    # menu 21
```

The backup saves into `~/k2-openhost-backups`:

- `~/printer_data/config` (the whole printer configuration);
- the CFS filament library `config/cfs_filaments.json`;
- the CFS state `~/printer_data/filament_box.json` (slot assignments, remaining estimates, settings);
- the Moonraker database (history, Mainsail settings).

![Backup](../../images/helper/cli-backup.png)

`restore` lists the archives, makes a backup of the current state first, then restores the chosen one. Restores are refused while printing.

## Automatic backup to GitHub (klipper-backup)

[Klipper-Backup](https://github.com/Staubgeborener/klipper-backup) commits `~/printer_data/config` to a **private** GitHub repository at every change, at boot, or on demand. The reference host uses it.

### 1. Create a private repository

On GitHub create an empty **private** repository, for example `K2-OpenHost-CM5`.

!!! danger "Keep it private"
    The configuration folder contains secrets: `moonraker.conf`, `telegram.conf`, the T113 token `k2oh_t113.token`, integration tokens. A public repository would publish them. If you ever make it public, add those files to `exclude` first.

### 2. Create a token

github.com → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**:

- **Repository access:** *Only select repositories* → your backup repository;
- **Repository permissions → Contents:** **Read and write**;
- copy the token at once: GitHub does not show it again.

The token goes only into `~/klipper-backup/.env` on the host, never into a repository or a chat.

### 3. Install

```bash
cd ~
git clone https://github.com/Staubgeborener/klipper-backup.git
./klipper-backup/install.sh
```

`install.sh` asks for the token, user, repository and branch, and can install the services `klipper-backup-filewatch` (backup at every change of the configuration) and `klipper-backup-on-boot`.

### Example `~/klipper-backup/.env`

```bash
github_token=PUT_YOUR_TOKEN_HERE
github_username=<your GitHub user>
github_repository=K2-OpenHost-CM5
branch_name="main"
commit_username="<name>"
commit_email="<name>@k2host"

backupPaths=( \
"printer_data/config/*" \
)

exclude=( \
"*.swp" \
"*.tmp" \
"printer-[0-9]*_[0-9]*.cfg" \
"*.bak" \
"*.bkp" \
"*.csv" \
"*.zip" \
)
```

### 4. Test

```bash
bash ~/klipper-backup/script.sh
systemctl status klipper-backup-filewatch.service
```

The script must end with the push to GitHub without authentication errors. Optional Mainsail macro (needs `gcode_shell_command`):

```ini
[gcode_shell_command backupgit]
command: bash /home/pi/klipper-backup/script.sh
timeout: 600
verbose: True

[gcode_macro BackupGit]
gcode:
    RUN_SHELL_COMMAND CMD=backupgit
```

### Good to know

- Klipper-Backup keeps its working copy in `~/config_backup`. At every run it empties that folder (keeping only `README.md`) and copies `backupPaths` again, so files added by hand to the repository root disappear: keep notes in `README.md`.
- When the token expires the backup stops: create a new one, update `github_token` in `.env`, then revoke the old one.
- Renamed the repository on GitHub? Update `github_repository` in `.env`: GitHub redirects the old name, but only until another repository takes it.

| Error | Fix |
| --- | --- |
| `403 Write access to repository not granted` | The token does not include the repository, or *Contents* is read-only. Edit the token on GitHub. |
| `Invalid username or token` when running `git push` by hand | The working copy reads the token from a variable set only by the script. Run `script.sh`, not `git push`. |
| `rejected (fetch first)` on a new repository | The local copy started its own history before the token worked. Move `~/config_backup` aside (`mv ~/config_backup ~/config_backup.old`) and run `script.sh` again. |
| `object file ... is empty` / `loose object ... is corrupt` | The local working copy is damaged (for example copied from another host). Move `~/config_backup` aside and run `script.sh` again: it recreates it from GitHub. |
| `remove the file manually to continue` | A leftover `index.lock` from an interrupted run: stop the filewatch service, then the fix above. |
