# Migrating from the old Docker install

Before Jarvis Automation, Jarvis ran as a set of Docker containers, each service on its own port. That install is retired for new users, and it no longer installs out of the box: MinIO, which it depends on, is gone. An existing install keeps running, and its pages are kept, frozen, under [Legacy](../legacy/index.md). This page moves you to Jarvis Automation, a single program called `jarvisd`, on the same machine.

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**. The commands below use `v0.1.0-rc18` as the example tag: replace it with the newest tag there.

## Choose a path

| | Start fresh | Keep your data |
|---|---|---|
| **What you get** | An empty server: you make a new account and set up voice nodes and phones again. | Your accounts and passwords, households, voice nodes, rooms, devices, settings, memories, routines, contacts, inbox and recipes. |
| **The old install** | Deleted, with all of its data. | Stopped, not deleted, so you can [go back](#roll-back) to it. |
| **Time** | About 10 minutes, plus the model download. | About 30 minutes, plus the model download. |

Either way, the new server takes the old one's ports, so phones and voice nodes find it at the same address.

## Start fresh

!!! warning "This deletes everything the old install knew"
    Accounts, households, routines, memories, recipes and the Docker images all go. To keep any of it, follow [Keep your data](#keep-your-data) instead.

### Remove the old install

=== "Linux"

    ```sh
    cd ~/.jarvis/compose && docker compose down -v --rmi all
    systemctl --user disable --now jarvis-admin.service
    rm ~/.config/systemd/user/jarvis-admin.service && systemctl --user daemon-reload
    cd ~ && rm -rf ~/.jarvis
    ```

=== "macOS"

    ```sh
    cd ~/.jarvis/compose && docker compose down -v --rmi all
    launchctl bootout gui/$(id -u)/com.jarvis.admin
    launchctl bootout gui/$(id -u)/com.jarvis.llm-proxy
    launchctl bootout gui/$(id -u)/com.jarvis.whisper-api
    launchctl bootout gui/$(id -u)/com.jarvis.tts
    launchctl bootout gui/$(id -u)/com.jarvis.ocr.service
    launchctl bootout gui/$(id -u)/com.jarvis.ocr.worker
    rm -f ~/Library/LaunchAgents/com.jarvis.admin.plist \
          ~/Library/LaunchAgents/com.jarvis.llm-proxy.plist \
          ~/Library/LaunchAgents/com.jarvis.whisper-api.plist \
          ~/Library/LaunchAgents/com.jarvis.tts.plist \
          ~/Library/LaunchAgents/com.jarvis.ocr.service.plist \
          ~/Library/LaunchAgents/com.jarvis.ocr.worker.plist
    cd ~ && rm -rf ~/.jarvis
    ```

    These background services ran the speech, language-model and OCR parts outside Docker. A `bootout` for one that isn't loaded says so and does nothing.

=== "Windows"

    Close the `jarvis-admin` console window, then in PowerShell:

    ```powershell
    cd $env:USERPROFILE\.jarvis\compose
    docker compose down -v --rmi all
    cd ~
    Remove-Item -Recurse -Force $env:USERPROFILE\.jarvis
    ```

`-v` removes the database volumes, where the old data lives; `--rmi all` removes the images. `~/.jarvis` is the old install's folder. The new server keeps its data elsewhere (`~/.jarvisd`, `/var/lib/jarvisd` or `%ProgramData%\jarvisd`), so this doesn't touch it.

### Install Jarvis Automation

Install as for a new machine: [macOS](macos.md), [Windows](windows.md), [Linux](linux.md) or the [one-liners](one-liners.md). Then finish in the [setup wizard](setup-wizard.md) at `http://<host>:7710/setup`.

Voice nodes and phones still hold the old server's keys and sessions. Set each voice node up again ([Voice node](voice-node.md)), and in the [mobile app](mobile-app.md) sign in with the account you made in the wizard.

## Keep your data

The import copies the old install's data into the new server and keeps every id, so voice nodes and phones carry on with the keys and passwords they already have. It reads the old database read-only and never changes it.

The order matters: install, import, **then** the setup wizard. The wizard's account step makes the new database non-empty, and the import only writes into an empty one.

### 1. Before you start

Write down how each container restarts, so that a [roll back](#roll-back) can put it back exactly. In a terminal (PowerShell on Windows):

```sh
docker inspect --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}} {{.State.Status}}' $(docker ps -aq) > ~/jarvis-legacy-containers.txt
```

A copy of the old database is cheap insurance. The import never writes to it, but nothing else protects it:

```sh
docker exec jarvis-postgres pg_dumpall -U jarvis | gzip > ~/jarvis-legacy-$(date +%F).sql.gz
```

(If your install used another database role, the role is `DB_USER` in `~/.jarvis/compose/.env`.)

### 2. Install with the old install stopped

Install with the script, and give it the option that stops the old install first. Don't open the setup link it prints yet.

=== "Linux and macOS"

    ```sh
    curl -fsSLO https://github.com/alexberardi/jarvis-server/releases/download/v0.1.0-rc18/install.sh
    less install.sh                         # read it first
    sh install.sh --stop-legacy             # asks for sudo
    ```

    `--stop-legacy` stops every container of the old install and turns its restart policy off, stops the old admin and keeps it from starting at login. On macOS it also stops the background services (`com.jarvis.*`) and prints the lines that bring them back, after **To bring them back later**: keep them for a roll back. Nothing is deleted. See [Advanced one-liners](one-liners.md#options).

=== "Windows"

    In PowerShell, from the folder you downloaded `install.ps1` from the release into:

    ```powershell
    powershell -ExecutionPolicy Bypass -File install.ps1 -StopLegacy
    ```

    `-StopLegacy` stops the old containers and turns their restart policy off. Nothing is deleted. Close the `jarvis-admin` console window yourself.

The server starts once, which is fine: it has made its keys but no account yet.

### 3. Import your data

Stop the new server, start only the old database, run the import as a dry run, then for real. The dry run checks every row and writes nothing, not even to the new server's database.

=== "Linux"

    The server's own account, `jarvisd`, can't read your home folder, so hand it the old install's `.env` file (the database password) in a private folder, and remove it afterwards:

    ```sh
    sudo jarvisd service stop
    docker start jarvis-postgres
    until docker exec jarvis-postgres pg_isready -q; do sleep 1; done
    L=/var/lib/jarvisd/legacy-compose
    sudo install -d -m 0700 -o jarvisd -g jarvisd $L
    sudo install -m 0400 -o jarvisd -g jarvisd ~/.jarvis/compose/.env $L/.env
    sudo -u jarvisd jarvisd import-legacy --home /var/lib/jarvisd --compose $L   # dry run
    sudo -u jarvisd jarvisd import-legacy --home /var/lib/jarvisd --compose $L --apply
    sudo rm -rf $L
    ```

    With a user service (`install.sh --user`), run everything as yourself: `jarvisd service stop --user`, then `jarvisd import-legacy --compose ~/.jarvis/compose`, and the same with `--apply`.

=== "macOS"

    The server runs as your account, so run the import as yourself:

    ```sh
    sudo jarvisd service stop
    docker start jarvis-postgres
    until docker exec jarvis-postgres pg_isready -q; do sleep 1; done
    jarvisd import-legacy --compose ~/.jarvis/compose   # dry run
    jarvisd import-legacy --compose ~/.jarvis/compose --apply
    ```

=== "Windows"

    In an Administrator PowerShell:

    ```powershell
    jarvisd service stop
    docker start jarvis-postgres
    docker exec jarvis-postgres pg_isready     # repeat until it says "accepting connections"
    jarvisd import-legacy --compose $env:USERPROFILE\.jarvis\compose   # dry run
    jarvisd import-legacy --compose $env:USERPROFILE\.jarvis\compose --apply
    ```

Read the dry run's report before you add `--apply`:

- It should end with **dry run passed**, and every table should show **FAILED 0**.
- **REFUSED** on a database's schema version means your old install is at a version the import doesn't know. Stop there and [ask for help](../troubleshooting/index.md#getting-help) with the report; don't force it with `--accept-head`.
- **household not imported** skips are leftovers with no household, such as test nodes; nothing is lost that worked before.
- **inactive nodes** are listed by id. They come over inactive, as they were.
- A refusal because the server is running, or because the database is not empty, names what to do. If you already opened the setup link, see [Opened the setup link too early](#opened-the-setup-link-too-early).

`--apply` writes everything in one go or nothing at all. It reports the imported admin accounts (email masked) and writes a log, `import-legacy-<time>.log`, into the server's data folder. The log names people by email; it is readable by the server's account only.

Options and other ways to point at the old database: [`jarvisd import-legacy`](../operate/cli.md#import-legacy).

### 4. Export your recipes and start the server

Recipes, meal plans and staples come over separately. While the old database is still running, export them with the script from the same release:

```sh
curl -fsSLO https://raw.githubusercontent.com/alexberardi/jarvis-server/v0.1.0-rc18/scripts/legacy/recipes-export.sh
less recipes-export.sh                  # read it first
bash recipes-export.sh --out ~/recipes-export.tar.gz
```

It only reads the old install. The file holds email addresses and household names: keep it private and delete it after the import. Then stop the old database and start the new server:

=== "Linux"

    ```sh
    docker stop jarvis-postgres
    sudo jarvisd service start && sudo jarvisd service status --wait 60s
    sudo jarvisd setup-link
    ```

=== "macOS"

    ```sh
    docker stop jarvis-postgres
    sudo jarvisd service start
    jarvisd setup-link
    ```

=== "Windows"

    ```powershell
    docker stop jarvis-postgres
    jarvisd service start
    jarvisd setup-link
    ```

`setup-link` now says to sign in rather than printing a token: the imported admin account closed the account step.

## Finish in the setup wizard

Open `http://<host>:7710/` and sign in with your **old admin account and its old password**. The wizard skips the Check and Account steps and resumes at **Hardware**, then Models and Privacy; see [Setup wizard](setup-wizard.md). If the old account was set to change its password at next sign-in, you set a new one first.

### Import your recipes

With the server running, import the export as a dry run, then with `--apply`. Recipes go to the account with the same email address as on the old install.

=== "Linux"

    The command refuses to run as root; the server's account must be able to read the file:

    ```sh
    sudo install -m 0600 -o jarvisd -g jarvisd ~/recipes-export.tar.gz /var/lib/jarvisd/recipes-export.tar.gz
    B=/var/lib/jarvisd/recipes-export.tar.gz
    sudo -u jarvisd jarvisd import-recipes --home /var/lib/jarvisd $B   # dry run
    sudo -u jarvisd jarvisd import-recipes --home /var/lib/jarvisd $B --apply
    ```

=== "macOS"

    ```sh
    jarvisd import-recipes ~/recipes-export.tar.gz   # dry run
    jarvisd import-recipes ~/recipes-export.tar.gz --apply
    ```

=== "Windows"

    In an Administrator PowerShell:

    ```powershell
    jarvisd import-recipes $env:USERPROFILE\recipes-export.tar.gz   # dry run
    jarvisd import-recipes $env:USERPROFILE\recipes-export.tar.gz --apply
    ```

In the dry run's report:

- **Users not matched**: nobody on the new server has that email yet. Their recipes wait for a later run.
- **Households not mapped, ambiguous**: pick the new household by hand with `--household <old id>=<new id>`, using the ids in the report.
- **REFUSED**: two old accounts match one new account (emails differing only in case), or two old households map to one new one. Nothing was written; fix the accounts and run it again.

Run the same `--apply` again whenever more people have signed in; it adds only what is new. Options: [`jarvisd import-recipes`](../operate/cli.md#import-recipes).

### Voice nodes

There is nothing to do for most nodes. The import kept each node's registration and key, and the new server answers on the old ports, so a node reconnects by itself within a minute or two and shows in the app's node list. Inactive nodes stay inactive.

Every version connects and shows in the app, and a node on 0.3.4 or later needs nothing more. For older ones, what the app can do depends on the version:

| Node version | From the app | What to do |
|---|---|---|
| 0.1.0–0.1.3 | Neither update nor reset. | Set it up again from a fresh SD card ([Voice node](voice-node.md)). |
| 0.1.4–0.1.130 | Update, but not reset. | Update it from the app to 0.3.4 or later; that also lets it receive commands again. |
| 0.1.131–0.1.149 | Update once you allow it; reset from 0.1.135, in some cases. | On the node's screen in the app, tap **Enable updates**, then update it. Before 0.1.137 the button is missing; see [Update policy](../clients/node-setup.md#update-policy). |
| 0.2.0 (Docker node) | Reset, but not update. | Pull the newer node image and recreate its container. |
| 0.3.1 | Update once you allow it, and reset. | Tap **Enable updates**, then update it to 0.3.4 or later; jokes and briefings don't work until then. |

A node that can't reach the server's message broker still gets updates, because they come back with its regular check-in. More: [Voice node](voice-node.md).

### Phones

Each person signs in again in the app, with their old email and password: accounts came over, sign-in sessions didn't. The server address stays the same (`http://<server>:7700`). Allow notifications when the app asks, so it can send them again, and pick the voice node to chat with. See [Mobile app](mobile-app.md).

### What doesn't come over

- **Voice profiles**: each person enrolls again. Speaker recognition stays on in households that had it on.
- **Sign-in sessions and push registrations**: the apps register again when people sign in.
- **Language-model and engine settings**: the wizard's Models step chooses the models.
- **Transcripts, request logs and pending invites.**

### Opened the setup link too early

If an account was made in the wizard before the import, the import refuses a database that isn't empty. Move the new database aside, start the server once so it makes an empty one, and run [step 3](#3-import-your-data) again from the top:

=== "Linux"

    ```sh
    sudo jarvisd service stop
    sudo sh -c 'for f in /var/lib/jarvisd/jarvis.db*; do mv "$f" "$f.aside"; done'
    sudo jarvisd service start
    ```

=== "macOS"

    ```sh
    sudo jarvisd service stop
    for f in ~/.jarvisd/jarvis.db*; do mv "$f" "$f.aside"; done
    sudo jarvisd service start
    ```

=== "Windows"

    ```powershell
    jarvisd service stop
    Get-ChildItem "$env:ProgramData\jarvisd\jarvis.db*" | Rename-Item -NewName { $_.Name + ".aside" }
    jarvisd service start
    ```

## Roll back

The old install was stopped, never changed, so you can go back to it at any point. Turn the new server off, and off at boot, then start the old one as it was:

=== "Linux"

    ```sh
    sudo jarvisd service stop && sudo systemctl disable jarvisd
    while read -r name policy state; do name=${name#/}; docker update --restart="$policy" "$name" >/dev/null; done < ~/jarvis-legacy-containers.txt
    docker start $(awk '$3 == "running" {sub("^/", "", $1); print $1}' ~/jarvis-legacy-containers.txt)
    systemctl --user enable --now jarvis-admin.service
    ```

=== "macOS"

    ```sh
    sudo jarvisd service uninstall           # keeps ~/.jarvisd
    while read -r name policy state; do name=${name#/}; docker update --restart="$policy" "$name" >/dev/null; done < ~/jarvis-legacy-containers.txt
    docker start $(awk '$3 == "running" {sub("^/", "", $1); print $1}' ~/jarvis-legacy-containers.txt)
    ```

    Then run the lines `--stop-legacy` printed after **To bring them back later**, one per background service, such as:

    ```sh
    launchctl enable gui/$(id -u)/com.jarvis.llm-proxy && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jarvis.llm-proxy.plist
    ```

=== "Windows"

    In an Administrator PowerShell:

    ```powershell
    jarvisd service uninstall                # keeps %ProgramData%\jarvisd
    Get-Content ~\jarvis-legacy-containers.txt | ForEach-Object {
        $name, $policy, $state = $_.TrimStart('/') -split ' '
        docker update --restart=$policy $name | Out-Null
        if ($state -eq 'running') { docker start $name | Out-Null }
    }
    ```

    Then start `jarvis-admin` again.

Phones sign in again with the same accounts. Voice nodes reconnect to the old install with their keys, unless you updated one past what the old install supports. The new server's data stays where it is until you remove it ([Uninstall](uninstall.md)).

## When you're done with the old install

Once the new server has run for a while and you're happy with it, the old install is only taking space: its Docker images and database volumes. Remove it with the steps in [Remove the old install](#remove-the-old-install) under Start fresh. That deletes the old data for good, so keep the database copy from [step 1](#1-before-you-start) if you want one.
