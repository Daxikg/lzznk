import os


def build_dir_tree(base_path, rel_path=''):
    abs_path = os.path.join(base_path, rel_path)
    nodes = []
    try:
        for name in sorted(os.listdir(abs_path)):
            full_path = os.path.join(abs_path, name)
            if os.path.isdir(full_path):
                child_rel_path = os.path.join(rel_path, name) if rel_path else name
                node = {
                    'name': name,
                    'rel_path': child_rel_path.replace('\\', '/'),
                    'children': build_dir_tree(base_path, child_rel_path)
                }
                nodes.append(node)
    except PermissionError:
        pass
    return nodes

