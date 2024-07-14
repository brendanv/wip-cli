import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter


class WIPNode:

    def __init__(self,
                 name: str,
                 notes: Optional[str] = None,
                 created_time: Optional[str] = None):
        self.name: str = name
        self.notes: Optional[str] = notes
        self.created_time: str = created_time or datetime.now().isoformat()
        self.children: List['WIPNode'] = []


class WIPTracker:

    def __init__(self):
        self.root: WIPNode = WIPNode("Root")
        self.current: WIPNode = self.root
        self.current_path: List[str] = []
        self.state_file = Path.home() / ".wip" / "state.json"
        self.archive_file = Path.home() / ".wip" / "archive.json"
        self.load_state()

    def save_state(self) -> None:

        def serialize_node(node: WIPNode) -> Dict[str, Any]:
            return {
                "name": node.name,
                "notes": node.notes,
                "created_time": node.created_time,
                "children": [serialize_node(child) for child in node.children]
            }

        state: Dict[str, Any] = {
            "root": serialize_node(self.root),
            "current_path": self.current_path
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> None:
        if not self.state_file.exists():
            return

        with open(self.state_file, "r") as f:
            state: Dict[str, Any] = json.load(f)

        def deserialize_node(data: Dict[str, Any]) -> WIPNode:
            node = WIPNode(data["name"], data["notes"], data["created_time"])
            node.children = [
                deserialize_node(child) for child in data["children"]
            ]
            return node

        self.root = deserialize_node(state["root"])
        self.current_path = state["current_path"]
        self.current = self.root
        for name in self.current_path:
            child = next((c for c in self.current.children if c.name == name),
                         None)
            if child:
                self.current = child
            else:
                print(
                    f"Warning: Could not find node {name} in path. Resetting to last valid node."
                )
                break

    def archive_node(self, node: WIPNode, path: List[str]) -> None:
        if self.archive_file.exists():
            with open(self.archive_file, "r") as f:
                archived_nodes = json.load(f)
        else:
            archived_nodes = []

        def archive_node_recursive(node: WIPNode, path: List[str]):
            for child in node.children:
                archive_node_recursive(child, path + [child.name])
            archived_node = {
                "name": node.name,
                "notes": node.notes,
                "path": "/" + "/".join(path),
                "created_time": node.created_time,
                "archived_time": datetime.now().isoformat()
            }
            archived_nodes.append(archived_node)

        archive_node_recursive(node, path)

        with open(self.archive_file, "w") as f:
            json.dump(archived_nodes, f, indent=2)

    def push(self, name: str, notes: Optional[str] = None) -> None:
        new_node = WIPNode(name, notes)
        self.current.children.append(new_node)
        self.current = new_node
        self.current_path.append(name)
        self.save_state()

    def pop(self) -> str:
        if self.current == self.root:
            return "Cannot delete root node"

        parent = self.find_parent(self.root, self.current)
        if parent:
            # Archive the current node along with all of its children
            self.archive_node(self.current, self.current_path)
            parent.children.remove(self.current)
            self.current = parent
            self.current_path.pop()
            self.save_state()
            return f"Deleted node and moved to parent: {self.current_info()}"
        else:
            return "Error: Parent node not found"

    def find_parent(self, node: WIPNode, target: WIPNode) -> Optional[WIPNode]:
        for child in node.children:
            if child == target:
                return node
            result = self.find_parent(child, target)
            if result:
                return result
        return None

    def current_info(self) -> str:
        return f"Current WIP: {self.current.name}\nPath: {self.get_path()}\nNotes: {self.current.notes or 'None'}"

    def edit_note(self, new_note: Optional[str] = None) -> None:
        if new_note is not None:
            self.current.notes = new_note
        else:
            editor = os.environ.get('EDITOR',
                                    'vi')  # Default to vi if EDITOR is not set
            with tempfile.NamedTemporaryFile(mode='w+',
                                             suffix=".txt",
                                             delete=False) as temp_file:
                if self.current.notes:
                    temp_file.write(self.current.notes)
                temp_file.flush()
                subprocess.call([editor, temp_file.name])
                temp_file.seek(0)
                self.current.notes = temp_file.read().strip()
            os.unlink(temp_file.name)
        self.save_state()

    def up(self) -> str:
        if not self.current_path:
            return "Already at root node"

        self.current_path.pop()
        self.current = self.root
        for name in self.current_path:
            self.current = next(c for c in self.current.children
                                if c.name == name)
        self.save_state()
        return self.current_info()

    def down(self) -> str:
        if not self.current.children:
            return "No children nodes"
        elif len(self.current.children) == 1:
            self.current = self.current.children[0]
            self.current_path.append(self.current.name)
            self.save_state()
            return self.current_info()
        else:
            print("Select a child node:")
            for i, child in enumerate(self.current.children, 1):
                print(f"{i}. {child.name}")

            while True:
                try:
                    choice = int(input("Enter the number of your choice: "))
                    if 1 <= choice <= len(self.current.children):
                        self.current = self.current.children[choice - 1]
                        self.current_path.append(self.current.name)
                        self.save_state()
                        return self.current_info()
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    return "\n...cancelled"
                except EOFError:
                    return "\n...cancelled"

    def get_path(self) -> str:
        if not self.current_path:
            return "/"
        return "/" + "/".join(self.current_path)

    def switch(self) -> str:
        all_paths = ["root"] + self.get_all_paths()
        path_completer = FuzzyWordCompleter(all_paths)

        try: 
            selected_path = prompt("Switch to: ", completer=path_completer)
        except KeyboardInterrupt:
            return "...cancelled"
        except EOFError:
            return "...cancelled"

        if not selected_path:
            return "No path selected"

        if selected_path.lower() == "root":
            self.current = self.root
            self.current_path = []
        else:
            path_components = selected_path.strip("/").split("/")

            self.current = self.root
            self.current_path = []

            for component in path_components:
                child = next((c for c in self.current.children if c.name == component), None)
                if child:
                    self.current = child
                    self.current_path.append(component)
                else:
                    return f"Error: Could not find node {component} in path"

        self.save_state()
        return f"Switched to: {self.current_info()}"

    def get_all_paths(self) -> List[str]:
        paths = []

        def traverse(node: WIPNode, current_path: List[str]):
            if node != self.root:
                paths.append("/" + "/".join(current_path))
            for child in node.children:
                traverse(child, current_path + [child.name])

        traverse(self.root, [])
        return paths

def main() -> None:
    parser = argparse.ArgumentParser(description="WIP Tracker CLI")
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
    subparsers.add_parser(
        "switch", help="Interactively switch to a WIP based on path")

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
        print(tracker.get_path())
    elif args.command == "switch":
        print(tracker.switch())


if __name__ == "__main__":
    main()