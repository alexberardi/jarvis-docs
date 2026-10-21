# Pairing

Pairing adds the computer without typing a password into it. Anyone in your household can approve it. The other way to add it is to sign in on the setup page with your Jarvis Automation email and password.

## Pair this computer

1. On the setup page, choose **Show a pairing code**. The computer shows a code such as `ABCD-EFGH` and its own name.
2. Approve the code in Jarvis Automation, either in the [web app](#approve-it-in-the-web-app) or in the [mobile app](#approve-it-in-the-mobile-app).
3. Back on the computer, the page names the household and who approved it. Click **Yes, add it**. **No, cancel** adds nothing.

A code works once and only for 10 minutes; if it runs out, show a new one. From a terminal, `jarvis-agent enroll --server <host>` shows a code the same way.

### Approve it in the web app

In Jarvis Automation (the web app, `http://<host>:7710`), open **Add-ons** (admins also find it on **Nodes**). Under **Pending pairings**, type the code, choose the household and the room, and click **Approve**. **Deny** refuses it.

### Approve it in the mobile app

1. In the mobile app, open **Nodes** and tap **Add a computer**.
2. **Get the agent on the computer:** the screen shows the agent's download link, with **Copy link**, **Share** and **Open**, so you can send it to the computer.
3. **Approve its code:** each computer waiting to be paired shows up with its name and code. Approve only if the computer shows this same code. Choose the household and the room, then tap **Approve** (or **Deny**).

The computer finishes pairing a few seconds later and shows up in your nodes.
