class Node:
    def __init__(self, title="", path="", node_type="", parent=None):
        self.title = title
        self.path = path
        self.type = node_type
        self.parent = parent
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self

    def remove_child(self, child_node):
        self.children.remove(child_node)
        child_node.parent = None

    def __repr__(self):
        return f"Node(title={self.title}, path={self.path}, type={self.type})"

    def to_dict(self):
        node_dict = {
            "title": self.title,
            "path": self.path,
            "type": self.type,
            "children": [child.to_dict() for child in self.children],
        }
        return node_dict


def create_tree(launch_tree, parent=None):
    if "entity" not in launch_tree:
        if launch_tree.get("type","")=="Node":
            title = launch_tree.get("name", "")
            node = Node(title, "", "Node", parent)
            return node
        else:
            return None
    node_type = launch_tree["entity"]["type"]

    # Filter nodes by type
    # if node_type not in ["GroupAction", "IncludeLaunchDescription"]:
    #     return None
    title = launch_tree["entity"].get("file_name", "")
    path = launch_tree["entity"].get("full_path", "")

    node = Node(title, path, node_type, parent)

    for child in launch_tree.get("children", []):
        child_node = create_tree(child, node)
        if child_node:
            node.add_child(child_node)
    return node


def remove_group_action_nodes(node):
    # Recursively process children first (depth-first)
    for child in node.children[:]:
        remove_group_action_nodes(child)

    # If the current node is a GroupAction, reassign its children to its parent
    if node.type in ["GroupAction","LoadComposableNodes","ComposableNodeContainer"]:
        if node.parent:
            for child in node.children:
                node.parent.add_child(child)
            node.parent.remove_child(node)
        else:
            # If root node is a GroupAction, promote its children to root level
            for child in node.children:
                child.parent = None
            node.children = []
