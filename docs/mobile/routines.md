# Routines

A routine is a phrase that runs a group of commands. Say "good morning" and Jarvis runs each step (the weather, your calendar, the news) and answers with one spoken summary. A routine can also run on a schedule.

## The routine list

Each card shows:

- an icon for when it runs: a microphone for a routine you start by voice, an hourglass for one that repeats every few minutes or hours, a calendar for one that runs at a set time;
- the routine's name and its first three trigger phrases;
- the number of steps, and the schedule if it has one (for example "Weekdays · 7:00 AM" or "Every 30m").

On a card:

- Tap the card to edit the routine.
- Tap the **play** button to run it now. With more than one node, pick which node runs it; the answer appears in an alert ("Done." if the routine returns no message). "No response" means the node did not answer: check that it is online.
- Tap the three-dot menu for **Edit** and **Delete**, or swipe the card left to delete it.

Pull down to refresh the list.

## Creating a routine

Tap **+** to open **New Routine**:

1. **Routine Name**.
2. **Trigger Phrases**: type a phrase in **Add phrase** and add it. At least one is required.
3. **Steps**: tap **Add Step**, then choose a **Command**. **Commands from** picks which node's commands the list shows; each node offers the commands installed on it. Give the step a **Label** if you like, and fill in its parameters: required ones are listed, **+ Parameter** adds an optional one and **+ Custom** adds any key and value. Hold the handle on a step to drag it into a new order.
4. **Response Instruction**: how Jarvis should sum up the results, for example "Give a cheerful morning briefing."
5. **Response Length**: **Short**, **Medium** or **Long**.
6. **Schedule** (optional): turn it on to run the routine without being asked.
    - **At a time**: a **Time** and the days (**Daily**, **Weekdays**, **Weekends** or **Custom**).
    - **Repeating**: **Every** 15 or 30 minutes, or 1, 2, 4, 6 or 12 hours.
    - **Run on**: the node that runs it.
7. Tap **Create Routine** (or **Save Changes** when editing).

The button stays disabled until the routine is complete, and the line above it says what is missing, for example "Add at least one trigger phrase", "Step 2: choose a command" or "Schedule: choose a node to run on". Step labels must be unique.

If a node's commands cannot be listed because the app has no encryption key for it, the Steps section offers **Set up encryption key**, or pick another node in **Commands from**.

## Scheduled errands

The calendar button at the top of the Routines tab opens **Scheduled errands**: the one-time and recurring errands you asked Jarvis to schedule by voice (for example "every morning at 8, check the weather"). Each row shows what it does, how often and when it runs next. Tap the cancel button on a row to stop it; a recurring errand stops repeating.
