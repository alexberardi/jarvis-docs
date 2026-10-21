# Pantry (Package Store)

The Pantry tab is where you browse and install packages: commands, background tasks and services for your nodes. Tap the **?** next to the title to see the welcome card again.

## Browsing

- **Search packages...** searches the Pantry.
- The category chips filter the list: **All**, or a category with its package count.
- The sort chips order it: **Popular**, **Newest** or **A-Z**.

Each card shows the package's name, author, description, version and install count, plus:

- a check-mark count such as **2/3** when it is installed on some of your nodes;
- a verified badge when a Jarvis maintainer has reviewed it (unverified packages still work, but have not been audited);
- **Risk** and a number, for packages rated 4 or higher: higher risk means broader system access (network, root, files);
- **Bundle**, for a package that installs several related pieces (commands and tasks) together.

## Package details

Tap a package to open its page: what it contains (**Components**), its **Security Report**, **License** and **Platforms**. Read the security report before you install a package with a high risk rating.

## Installing

Only household **admins** and **power users** see the install button.

1. Tap **Install** (or **Install / Update to v…** when some of your nodes have an older version).
2. With one node, the install starts at once. With several, pick the nodes in **Select nodes**.
3. A package that installs system software asks first (**Root-privileged install**, with the list of packages). Continue only if you trust the author.
4. The progress screen follows each node until the install finishes.

The node downloads the package, checks it, installs its dependencies and enables its commands. When every node already has the latest version, the app says **Up to date**.

Some packages are not for every node:

- A package made for Raspberry Pi nodes is not offered to a computer running the desktop agent ("Not for computers").
- A prompt provider runs on your server, not a node, and installs with **Install to Command Center**. It changes how Jarvis writes its responses.

If an update goes wrong, the package page offers **Revert to v…**, which rolls the nodes back to the previous version; each node restarts.

## Test Install

**Test** at the top of the Pantry tab opens **Test Install**, for trying a package that is not in the Pantry yet: enter the 6-character **Share Code** from the Forge, choose the **Target Node** and install it there.
