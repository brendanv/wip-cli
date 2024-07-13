import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class WIPNode:
    def __init__(self, name: str, notes: Optional[str] = None):
        self.name: str = name
        self.notes: Optional[str] = notes
        self.children: List['WIPNode'] = []

class WIPTracker:
    def __init__(self):
        self.root: WIPNode = WIPNode("Root")
        self.current: WIPNode = self.root
        self.current_path: List[str] = []
        self.archived_nodes: List[Dict[str, Any]] = []
        self.state_file = Path.home() / ".wip" / "state.json"
        self.load_state()

    def save_state(self) -> None:
        def serialize_node(node: WIPNode) -> Dict[str, Any]:
            return {
                "name": node.name,
                "notes": node.notes,
                "children": [serialize_node(child) for child in node.children]
            }

        state: Dict[str, Any] = {
            "root": serialize_node(self.root),
            "current_path": self.current_path,
            "archived_nodes": self.archived_nodes
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
            node = WIPNode(data["name"], data["notes"])
            node.children = [deserialize_node(child) for child in data["children"]]
            return node

        self.root = deserialize_node(state["root"])
        self.current_path = state["current_path"]
        self.archived_nodes = state.get("archived_nodes", [])
        self.current = self.root
        for name in self.current_path:
            child = next((c for c in self.current.children if c.name == name), None)
            if child:
                self.current = child
            else:
                print(f"Warning: Could not find node {name} in path. Resetting to last valid node.")
                break

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
            parent.children.remove(self.current)
            archived_node = {
                "name": self.current.name,
                "notes": self.current.notes,
                "path": self.get_path()
            }
            self.archived_nodes.append(archived_node)
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
            editor = os.environ.get('EDITOR', 'vi')  # Default to vi if EDITOR is not set
            with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", delete=False) as temp_file:
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
            self.current = next(c for c in self.current.children if c.name == name)
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

    def get_path(self) -> str:
        if not self.current_path:
            return "/"
        return "/" + "/".join(self.current_path)

def main() -> None:
    parser = argparse.ArgumentParser(description="WIP Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="Create a new WIP as a child of the current WIP")
    push_parser.add_argument("name", help="Name of the new WIP")
    push_parser.add_argument("--notes", help="Optional notes for the new WIP")

    subparsers.add_parser("current", help="Display the name, path, and notes for the current WIP")
    subparsers.add_parser("pop", help="Delete the current WIP and set the parent WIP to be current")

    note_parser = subparsers.add_parser("note", help="Edit the note for the current WIP")
    note_parser.add_argument("note", nargs='?', help="New note content (optional)")

    subparsers.add_parser("up", help="Set current to the parent node and display the new current node")
    subparsers.add_parser("down", help="List children and select which child to set as current")
    subparsers.add_parser("path", help="Print the full path to the current WIP")

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

if __name__ == "__main__":
    main()