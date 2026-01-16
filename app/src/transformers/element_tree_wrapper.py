import xml.etree.ElementTree as ET


class ElementTreeWrapper:
    def __init__(self, tree: ET.ElementTree):
        self.tree = tree
        self.root = tree.getroot()

    def get_value(self, path: str, element: ET.Element = None) -> str | None:
        """Get the Element.text of the Element that matches the path.

        Args:
            path (str): Path in the tree. Two elements of the path are separated by "/".
            element (ET.Element | None): Root of the path. Default to 'self.root'.

        Returns:
            str | None: Element.text of the Element that matches the path or None.
        """
        paths = path.split("/")
        if element is None:
            element = self.root
        for p in paths:
            element = element.find(p)
            if element is None:
                return None
        return element.text

    def to_dict(self, element: ET.Element = None) -> dict:
        """Cast an Element to dict.

        Args:
            element (ET.Element | None): Element to cast in dictionary. Default self.root.

        Returns:
            dict: Dictionary whose keys are Element.tag and values are Element.text.
        """
        if element is None:
            element = self.root
        data = {}
        for child in element:
            if len(child) > 0:
                data[child.tag] = self.to_dict(child)
            else:
                data[child.tag] = child.text
        return data
