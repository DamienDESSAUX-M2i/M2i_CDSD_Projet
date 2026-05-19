import xml.etree.ElementTree as ET


class ElementTreeWrapper:
    def __init__(self, tree: ET.ElementTree):
        self.tree = tree
        self.root = tree.getroot()

    def get_value(self, path: str, element: ET.Element = None) -> str | None:
        """Get the Element.text value matching the path.

        Args:
            path (str): Path in the tree. Two elements of the path are separated by "/".
            element (ET.Element | None): Root of the path. Default to 'self.root'.

        Returns:
            str | None: Element.text value or None.
        """
        if element is None:
            element = self.root

        element = element.find(path)
        if element is None:
            return None

        return element.text

    def get_values(self, path: str, element: ET.Element = None) -> list[str]:
        """Get all Element.text values matching the path.

        Args:
            path (str): Path in the tree. Elements are separated by "/".
            element (ET.Element | None): Root of the path. Default 'self.root'.

        Returns:
            list[str]: List of Element.text values (empty if no match).
        """
        if element is None:
            element = self.root

        elements = element.findall(path)

        return [el.text for el in elements if el.text is not None]

    def get_element(self, path: str) -> ET.Element | None:
        """Get the Element node matching the path.

        Args:
            path (str): Path in the tree. Two elements of the path are separated by "/".

        Returns:
            str | None: Element node or None.
        """
        return self.root.find(path)

    def get_elements(self, path: str) -> list[ET.Element]:
        """Get all Element nodes matching the path.

        Args:
            path (str): Path in the tree. Two elements of the path are separated by "/".

        Returns:
            list[str]: List of Element nodes (empty if no match).
        """
        return self.root.findall(path)

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

    def to_list(self, element: ET.Element = None) -> list[dict]:
        """Cast children of an Element to a list of dictionaries.

        Args:
            element (ET.Element | None): Element whose children will be cast.
                Default self.root.

        Returns:
            list[dict]: List of dictionaries representing child elements.
        """
        if element is None:
            element = self.root

        return [self.to_dict(child) for child in element]
