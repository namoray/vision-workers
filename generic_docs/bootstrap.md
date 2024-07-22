# Ensuring your hardware is ready

To ensure that your machine is ready, run `sudo -E ./bootstrap.sh`. This bootstrapping script will do the following:
- Ensure some base packages and utilities are installed.
- Ensure that the Nvidia GPU drivers are installed.
- Ensure Docker and the nvidia-container-toolkit are installed and configured.
- Ensure Python 3.11 and pip are installed and available via `python` and `pip`.
- Install the vision-autoupdater as a systemd unit if the user opted in (default).
- Install the orchestrator as a cronjob if the user opted out of auto-updates.
- Reboot if necessary (this is only in the case your system didn't come with nvidia drivers).

To opt out of auto-updates run this command instead `WITH_AUTOUPDATES=0 sudo -E ./bootstrap.sh`.

# Checking the status of the vision auto-updater

The vision auto-updater is installed as a systemd unit, to check if it is running/healthy, run:
```bash
sudo systemctl status vision-autoupdater
```

To stop and disable the auto-updater from restarting, run:
```bash
sudo systemctl disable --now vision-autoupdater
```

To start and enable the auto-updater, run:
```bash
sudo systemctl enable --now vision-autoupdater
```

To watch the logs of the auto-updater, run:
```bash
sudo journalctl -fu vision-autoupdater
```

# Issues with dpkg

Some hosting providers run post-boot initialisation scripts that can block
`bootstrap.sh` from running. You will see this if the script complains that it
couldn't acquire a lock for dpkg because another process has it.

If this is the case, allow the machine to continue it's initialization (10-15 minutes) 
and then reattempt to run `bootstrap.sh`.