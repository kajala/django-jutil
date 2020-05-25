import re
from typing import Optional, Iterable, Dict, Any, List
from xml import etree
from xml.etree.ElementTree import Element, SubElement


def _xml_element_value(el: Element, is_int: bool = False) -> Any:
    """
    Gets XML Element value.
    :param el: Element
    :param is_int: If True return value is converted to int (if possible)
    :return: value of the element (int/str)
    """
    # None
    if el.text is None:
        return None
    # int
    try:
        if is_int:
            return int(el.text)
    except Exception:  # nosec
        pass
    # default to str if not empty
    s = str(el.text).strip()
    return s if s else None


def _xml_tag_filter(s: str, strip_namespaces: bool) -> str:
    """
    Returns tag name and optionally strips namespaces.
    :param s: Tag name
    :param strip_namespaces: Strip namespace prefix
    :return: str
    """
    if strip_namespaces:
        ns_end = s.find('}')
        if ns_end != -1:
            s = s[ns_end+1:]
        else:
            ns_end = s.find(':')
            if ns_end != -1:
                s = s[ns_end+1:]
    return s


def _xml_set_element_data_r(data: dict, el: Element,  # pylint: disable=too-many-arguments,too-many-locals
                            array_tags: Iterable[str], int_tags: Iterable[str],
                            strip_namespaces: bool, parse_attributes: bool,
                            value_key: str, attribute_prefix: str):

    tag = _xml_tag_filter(el.tag, strip_namespaces)

    # complex type?
    attrib = el.attrib if parse_attributes else {}
    is_complex = len(attrib) > 0 or len(list(el)) > 0
    is_array = tag in data or tag in array_tags
    is_int = not is_array and tag in int_tags

    # set obj value
    value = _xml_element_value(el, is_int=is_int)
    if is_complex:
        obj = {}
        if value is not None:
            obj[value_key] = value
    else:
        obj = value

    # set attributes
    for a_key, a_val in attrib.items():
        obj[attribute_prefix + _xml_tag_filter(a_key, strip_namespaces)] = a_val  # pytype: disable=unsupported-operands

    # recurse children
    for el2 in list(el):
        _xml_set_element_data_r(obj, el2, array_tags=array_tags, int_tags=int_tags,
                                strip_namespaces=strip_namespaces, parse_attributes=parse_attributes,
                                value_key=value_key, attribute_prefix=attribute_prefix)

    # store result
    if is_array:
        data.setdefault(tag, [])
        if not isinstance(data[tag], list):
            data[tag] = [data[tag]]
        data[tag].append(obj)
    else:
        if tag in data:
            raise Exception('XML parsing failed, tag {} collision'.format(tag))
        data[tag] = obj


def xml_to_dict(xml_bytes: bytes,  # pylint: disable=too-many-arguments,too-many-locals
                tags: Optional[Iterable[str]] = None, array_tags: Optional[Iterable[str]] = None,
                int_tags: Optional[Iterable[str]] = None,
                strip_namespaces: bool = True, parse_attributes: bool = True,
                value_key: str = '@', attribute_prefix: str = '@',
                document_tag: bool = False) -> Dict[str, Any]:
    """
    Parses XML string to dict. In case of simple elements (no children, no attributes) value is stored as is.
    For complex elements value is stored in key '@', attributes '@xxx' and children as sub-dicts.
    Optionally strips namespaces.

    For example:
        <Doc version="1.2">
          <A class="x">
            <B class="x2">hello</B>
          </A>
          <A class="y">
            <B class="y2">world</B>
          </A>
          <C>value node</C>
        </Doc>
    is returned as follows:
        {'@version': '1.2',
         'A': [{'@class': 'x', 'B': {'@': 'hello', '@class': 'x2'}},
               {'@class': 'y', 'B': {'@': 'world', '@class': 'y2'}}],
         'C': 'value node'}

    Args:
        xml_bytes: XML file contents in bytes
        tags: list of tags to parse (pass empty to return all chilren of top-level tag)
        array_tags: list of tags that should be treated as arrays by default
        int_tags: list of tags that should be treated as ints
        strip_namespaces: if true namespaces will be stripped
        parse_attributes: Elements with attributes are stored as complex types with '@' identifying text value and @xxx identifying each attribute
        value_key: Key to store (complex) element value. Default is '@'
        attribute_prefix: Key prefix to store element attribute values. Default is '@'
        document_tag: Set True if Document root tag should be included as well

    Returns: dict
    """
    if tags is None:
        tags = []
    if array_tags is None:
        array_tags = []
    if int_tags is None:
        int_tags = []

    root = etree.ElementTree.fromstring(xml_bytes)
    if tags:
        if document_tag:
            raise Exception('xml_to_dict: document_tag=True does not make sense when using selective tag list '
                            'since selective tag list finds tags from the whole document, not only directly under root document tag')
        root_elements: List[Element] = []
        for tag in tags:
            root_elements.extend(root.iter(tag))
    else:
        root_elements = list(root)

    data: Dict[str, Any] = {}
    for el in root_elements:
        _xml_set_element_data_r(data, el, array_tags=array_tags, int_tags=int_tags,
                                strip_namespaces=strip_namespaces, parse_attributes=parse_attributes,
                                value_key=value_key, attribute_prefix=attribute_prefix)

    # set root attributes
    if parse_attributes:
        for a_key, a_val in root.attrib.items():
            data[attribute_prefix + _xml_tag_filter(a_key, strip_namespaces)] = a_val

    return data if not document_tag else {root.tag: data}


def _xml_filter_tag_name(tag: str) -> str:
    return re.sub(r'\[\d+\]', '', tag)


def _xml_element_set_data_r(el: Element, data: dict, value_key: str, attribute_prefix: str):
    # print('_xml_element_set_data_r({}): {}'.format(el.tag, data))
    if not hasattr(data, 'items'):
        data = {'@': data}
    for k, v in data.items():
        if k == value_key:
            el.text = str(v)
        elif k.startswith(attribute_prefix):
            el.set(k[1:], str(v))
        elif isinstance(v, (list, tuple)):
            for v2 in v:
                el2 = SubElement(el, _xml_filter_tag_name(k))
                assert isinstance(el2, Element)
                _xml_element_set_data_r(el2, v2, value_key, attribute_prefix)
        elif isinstance(v, dict):
            el2 = SubElement(el, _xml_filter_tag_name(k))
            assert isinstance(el2, Element)
            _xml_element_set_data_r(el2, v, value_key, attribute_prefix)
        else:
            el2 = SubElement(el, _xml_filter_tag_name(k))
            assert isinstance(el2, Element)
            el2.text = str(v)


def dict_to_element(doc: dict, value_key: str = '@', attribute_prefix: str = '@') -> Element:
    """
    Generates XML Element from dict.
    Generates complex elements by assuming element attributes are prefixed with '@', and value is stored to plain '@'
    in case of complex element. Children are sub-dicts.

    For example:
        {
            'Doc': {
                '@version': '1.2',
                'A': [{'@class': 'x', 'B': {'@': 'hello', '@class': 'x2'}},
                      {'@class': 'y', 'B': {'@': 'world', '@class': 'y2'}}],
                'C': 'value node',
                'D[]': 'value node line 1',
                'D[]': 'value node line 2',
            }
         }
    is returned as follows:
        <?xml version="1.0" ?>
        <Doc version="1.2">
            <A class="x">
                <B class="x2">hello</B>
            </A>
            <A class="y">
                <B class="y2">world</B>
            </A>
            <C>value node</C>
            <D>value node line 1</D>
            <D>value node line 2</D>
        </Doc>

    Args:
        doc: dict. Must have sigle root key dict.
        value_key: Key to store (complex) element value. Default is '@'
        attribute_prefix: Key prefix to store element attribute values. Default is '@'

    Returns: xml.etree.ElementTree.Element
    """
    if len(doc) != 1:
        raise Exception('Invalid data dict for XML generation, document root must have single element')

    for tag, data in doc.items():
        el = Element(_xml_filter_tag_name(tag))
        assert isinstance(el, Element)
        _xml_element_set_data_r(el, data, value_key, attribute_prefix)
        return el  # pytype: disable=bad-return-type

    return Element('empty')
