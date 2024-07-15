# wip-cli

![wip-cli-logo](/img/wip-cli-logo.svg)

`wip-cli` is a command-line tool for managing your Work In Progress (WIP) items. It allows you to create, navigate, and manage a tree-like structure of tasks or projects, helping you keep track of multiple branching work streams without losing your place or your notes.

Your thought process isn't linear, so your notes shouldn't be either. `wip-cli` adapts to your natural workflow, allowing you to branch off, dive deep, and resurface with ease.

## What is WIP?

> [!NOTE]
> This entire project (including this readme and logo) are AI-generated, just to see if I could do it. However, I do use this tool myself, so read on if it sounds interesting!

WIP stands for "Work In Progress". In the context of this tool, a WIP is any task, project, or piece of work that you're currently focusing on. The `wip` command allows you to manage these items in a hierarchical structure, much like a tree of tasks and subtasks.

## How `wip` Works

`wip` treats your work items as a tree structure, where each node represents a task or project. This structure allows for:

1. **Hierarchical Organization**: Tasks can have subtasks, projects can have subprojects, etc.
2. **Stack-like Navigation**: You can "push" new tasks onto your stack of work, and "pop" them off when complete.
3. **Branching Work Streams**: You can have multiple ongoing branches of work, and easily switch between them.
4. **Persistent State**: Your place in each branch is saved, along with any notes you've made.

This approach allows you to:
- Start a new task without losing context of your current work.
- Easily return to previous tasks exactly where you left off.
- Maintain separate streams of work for different projects or contexts.
- Keep notes associated with each task for future reference.

## Suggested Setup

Follow these steps to set up `wip-cli`:

1. Clone the repository into your `~/.wip-cli` directory:

   ```bash
   git clone https://github.com/brendanv/wip-cli.git ~/.wip-cli
   ```

   If the `~/.wip-cli` directory doesn't exist, create it first:

   ```bash
   mkdir ~/.wip-cli
   ```

2. Navigate to the cloned directory:

   ```bash
   cd ~/.wip-cli
   ```

3. Run the setup script to create a virtual environment and install dependencies:

   ```bash
   ./setup.sh
   ```

4. Add the `~/.wip-cli` directory to your PATH. Open your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`) in a text editor and add the following line:

   ```bash
   export PATH="$HOME/.wip-cli:$PATH"
   ```

5. Reload your shell configuration or restart your terminal:

   ```bash
   source ~/.bashrc  # or ~/.zshrc, ~/.bash_profile, etc.
   ```

## Usage

After setting up, you can use `wip` with the following commands:

- Create a new WIP item and push it onto your stack:
  ```
  wip push "New Task"
  ```

- Display the current WIP:
  ```
  wip current
  ```

- Move up to the parent WIP:
  ```
  wip up
  ```

- List child WIPs and move down to a selected one:
  ```
  wip down
  ```

- Interactively switch to a different WIP anywhere in the tree:
  ```
  wip switch
  ```

- Remove the current WIP and all its children:
  ```
  wip pop
  ```

- Edit notes for the current WIP:
  ```
  wip note
  ```

- Show the full path of the current WIP:
  ```
  wip path
  ```

## Example Workflow

Here's an example of how you might use `wip` in your daily work:

1. Start a new project:
   ```
   $ wip push "New Project A"
   Created new WIP: New Project A
   ```

2. Add a task to the project:
   ```
   $ wip push "Task 1"
   Created new WIP: Task 1
   ```

3. Add notes to the task:
   ```
   $ wip note
   Note updated successfully
   ```

4. Check your current WIP:
   ```
   $ wip current
   Current WIP: Task 1
   Path: /New Project A/Task 1
   Notes: This is a note for Task 1
   ```

5. Complete the task and return to the project level:
   ```
   $ wip pop
   Deleted node and moved to parent: Current WIP: New Project A
   Path: /New Project A
   Notes: None
   ```

6. Start a new branch of work without losing your place in Project A:
   ```
   $ wip up
   Current WIP: Root
   Path: /
   Notes: None

   $ wip push "New Project B"
   Created new WIP: New Project B
   ```

7. Switch back to Project A at any time:
   ```
   $ wip switch
   Switch to: /New Project A
   Switched to: Current WIP: New Project A
   Path: /New Project A
   Notes: None
   ```

This workflow allows you to maintain multiple streams of work, easily switch between them, and keep detailed notes at each level.

## Notes

- Your WIP data is stored in `~/.wip-cli/state.json`. Consider backing up this file periodically.
- Archived WIPs are stored in `~/.wip-cli/archive.json`.


For more detailed information about each command, you can check the source code or consider adding a `--help` option to each command in the future.