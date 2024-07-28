import argparse
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter


class WIPTracker:

    def __init__(self):
        self.db_file = Path(__file__).parent / "wip.db"
        self.conn = sqlite3.connect(str(self.db_file))
        self.cursor = self.conn.cursor()
        self.create_table()
        self.ensure_root_node()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wip (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent INTEGER,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archived_at TIMESTAMP,
                current BOOLEAN DEFAULT 0,
                FOREIGN KEY (parent) REFERENCES wip (id)
            )
        ''')
        self.conn.commit()

    def ensure_root_node(self):
        self.cursor.execute("SELECT id FROM wip WHERE parent IS NULL")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO wip (path, name, current) VALUES ('/', 'Root', 1)"
            )
            self.conn.commit()

    def get_current_node(self) -> Tuple[int, str, str, Optional[str]]:
        self.cursor.execute(
            "SELECT id, path, name, notes FROM wip WHERE current = 1")
        return self.cursor.fetchone()

    def set_current_node(self, node_id: int):
        self.cursor.execute("UPDATE wip SET current = 0")
        self.cursor.execute("UPDATE wip SET current = 1 WHERE id = ?",
                            (node_id, ))
        self.conn.commit()

    def push(self, name: str, notes: Optional[str] = None) -> None:
        current_id, current_path, _, _ = self.get_current_node()
        new_path = os.path.join(current_path, name).replace('\\', '/')
        self.cursor.execute(
            "INSERT INTO wip (parent, path, name, notes) VALUES (?, ?, ?, ?)",
            (current_id, new_path, name, notes))
        new_id = self.cursor.lastrowid
        self.set_current_node(new_id)
        self.conn.commit()

    def pop(self) -> str:
        current_id, current_path, current_name, _ = self.get_current_node()
        if current_path == '/':
            return "Cannot delete root node"

        self.cursor.execute("SELECT parent FROM wip WHERE id = ?",
                            (current_id, ))
        parent_id = self.cursor.fetchone()[0]

        # Archive the current node
        self.cursor.execute(
            "UPDATE wip SET archived_at = CURRENT_TIMESTAMP WHERE id = ?",
            (current_id, ))

        self.set_current_node(parent_id)
        self.conn.commit()

        self.cursor.execute("SELECT path, name FROM wip WHERE id = ?",
                            (parent_id, ))
        parent_path, parent_name = self.cursor.fetchone()
        return f"Deleted node and moved to parent: {parent_path} ({parent_name})"

    def current_info(self) -> str:
        _, path, name, notes = self.get_current_node()
        return f"Current WIP: {name}\nPath: {path}\nNotes: {notes or 'None'}"

    def edit_note(self, new_note: Optional[str] = None) -> None:
        current_id, _, _, current_notes = self.get_current_node()
        if new_note is not None:
            updated_notes = f"{current_notes or ''}\n{new_note}".strip()
        else:
            editor = os.environ.get('EDITOR', 'vi')
            with tempfile.NamedTemporaryFile(mode='w+',
                                             suffix=".txt",
                                             delete=False) as temp_file:
                if current_notes:
                    temp_file.write(current_notes)
                temp_file.close()
                subprocess.call([editor, temp_file.name])
                with open(temp_file.name, 'r') as updated_file:
                    updated_notes = updated_file.read().strip()
            os.unlink(temp_file.name)

        self.cursor.execute("UPDATE wip SET notes = ? WHERE id = ?",
                            (updated_notes, current_id))
        self.conn.commit()

    def up(self) -> str:
        current_id, current_path, _, _ = self.get_current_node()
        if current_path == '/':
            return "Already at root node"

        self.cursor.execute("SELECT parent FROM wip WHERE id = ?",
                            (current_id, ))
        parent_id = self.cursor.fetchone()[0]
        self.set_current_node(parent_id)
        return self.current_info()

    def down(self) -> str:
        current_id, _, _, _ = self.get_current_node()
        self.cursor.execute(
            """
            SELECT id, name 
            FROM wip 
            WHERE parent = ? AND archived_at IS NULL
            ORDER BY name
        """, (current_id, ))
        children = self.cursor.fetchall()

        if not children:
            return "No children nodes"
        elif len(children) == 1:
            self.set_current_node(children[0][0])
            return self.current_info()
        else:
            print("Select a child node:")
            for i, (_, child_name) in enumerate(children, 1):
                print(f"{i}. {child_name}")

            while True:
                try:
                    choice = int(input("Enter the number of your choice: "))
                    if 1 <= choice <= len(children):
                        self.set_current_node(children[choice - 1][0])
                        return self.current_info()
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    return "\n...cancelled"
                except EOFError:
                    return "\n...cancelled"

    def get_all_paths(self) -> List[str]:
        self.cursor.execute("SELECT path FROM wip WHERE archived_at IS NULL")
        return [row[0] for row in self.cursor.fetchall()]

    def switch(self) -> str:
        all_paths = self.get_all_paths()
        path_completer = FuzzyWordCompleter(all_paths)

        try:
            selected_path = prompt("Switch to: ", completer=path_completer)
        except KeyboardInterrupt:
            return "...cancelled"
        except EOFError:
            return "...cancelled"

        if not selected_path:
            return "No path selected"

        self.cursor.execute("SELECT id FROM wip WHERE path = ?",
                            (selected_path, ))
        result = self.cursor.fetchone()
        if result:
            self.set_current_node(result[0])
            return f"Switched to: {self.current_info()}"
        else:
            return f"Error: Could not find node with path {selected_path}"

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="wip-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser(
        "push", help="Create a new WIP as a child of the current WIP")
    push_parser.add_argument("name", help="Name of the new WIP")
    push_parser.add_argument("--notes", help="Optional notes for the new WIP")

    subparsers.add_parser(
        "current",
        help="Display the name, path, and notes for the current WIP")
    subparsers.add_parser(
        "pop",
        help="Delete the current WIP and set the parent WIP to be current")

    note_parser = subparsers.add_parser(
        "note", help="Edit the note for the current WIP")
    note_parser.add_argument("note",
                             nargs='?',
                             help="New note content (optional)")

    subparsers.add_parser(
        "up",
        help="Set current to the parent node and display the new current node")
    subparsers.add_parser(
        "down", help="List children and select which child to set as current")
    subparsers.add_parser("path",
                          help="Print the full path to the current WIP")
    subparsers.add_parser("switch",
                          help="Interactively switch to a WIP based on path")

    args: argparse.Namespace = parser.parse_args()

    tracker = WIPTracker()

    if args.command == "push":
        tracker.push(args.name, args.notes)
        print(f"Created new WIP: {args.name}")
    elif args.command == "current":
        print(tracker.current_info())
    elif args.command == "pop":
        print(tracker.pop())
    elif args.command == "note":
        tracker.edit_note(args.note)
        print("Note updated successfully")
    elif args.command == "up":
        print(tracker.up())
    elif args.command == "down":
        print(tracker.down())
    elif args.command == "path":
        print(tracker.get_current_node()[1])
    elif args.command == "switch":
        print(tracker.switch())


if __name__ == "__main__":
    main()
