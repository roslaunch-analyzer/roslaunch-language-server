import os
from itertools import chain


def modify_json(json_data: dict):
    modified_json = {}
    if json_data["type"] == "IncludeLaunchDescription":
        modified_json = {
            "title": os.path.basename(json_data["path"]),
            "path": json_data["path"],
            "type": json_data["type"],
        }
        modified_json["children"] = list(
            chain.from_iterable(modify_json(child) for child in json_data["children"])
        )

        return [modified_json]
    elif json_data["type"] == "Node":
        modified_json = {
            "title": json_data["name"],
            "path": "",
            "type": json_data["type"],
            "children": [],
        }
        return [modified_json]
    elif json_data["type"] == "LoadComposableNodes":
        return [
            {
                "title": f'{loaded_node["name"]} ({loaded_node["plugin"]})',
                "path": "",
                "type": "Node",
                "children": [],
            }
            for loaded_node in json_data["loaded_nodes"]
        ]

    elif json_data["type"] in [
        "GroupAction",
        "ComposableNodeContainer",
    ]:
        return list(
            chain.from_iterable(modify_json(child) for child in json_data["children"])
        )

    return []
