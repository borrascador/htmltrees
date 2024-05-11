import re, html
from xml.etree.ElementTree import Element, tostring
from bs4 import BeautifulSoup

id_dict = {}

class Tree(object):
    def __init__(self, data=None, children=None):
        self.children = children or []
        self.props = data.copy()
        self.set_unique_id()

    def set_unique_id(self):
        """Sets a unique ID prop for current node."""
        name = self.get_prop('name','')
        # split node name on spaces, force lowercase, strip non alphanumerics
        id = re.sub(r'[^A-Za-z0-9]+', '', name.split(' ', 1)[0].lower())
        counter = 0
        test_id = id
        while test_id in id_dict.keys():
            # if ID not unique, increment ID and check again if unique
            counter += 1
            test_id = id + str(counter)
        # if unique, use that ID
        id = test_id
        id_dict[id] = self
        self.props['id'] = id
    
    def get_child_ids(self):
        """Return a space-separated string list of child IDs for current node."""
        aria_owns = ''
        if self.children:
            for child in self.children:
                child_id = child.get_prop('id', '')
                aria_owns = f'{aria_owns} {child_id}'
        return aria_owns.strip()
    
    @property
    def is_leaf(self):
        """Return True if the current node is a leaf."""
        return not self.children

    def get_prop(self, prop, default=None):
        """Return the node's property prop (an attribute or in self.props)."""
        attr = getattr(self, prop, None)
        return attr if attr is not None else self.props.get(prop, default)

    def to_str(self, show_internal=True, compact=False, props=None,
               px=None, py=None, px0=0, py0=0, render_html=False):
        """Return a string containing an ascii drawing of the tree.

        :param show_internal: If True, show the internal nodes too.
        :param compact: If True, use exactly one line per tip.
        :param props: List of node properties to show. If None, show all.
        :param px, py, px0: Paddings (x, y, x for leaves). Overrides `compact`.
        :param render_html: If True, format output as accessible HTML
        """
        return to_str(self, show_internal, compact, props,
                               px, py, px0, py0, render_html)

"""
Tree text visualization.

Functions to show a string drawing of a tree suitable for printing on
a console or to HTML.
"""

# These functions would not normally be used directly. Instead, they
# are used when doing things like:
#   print(t)
# or like:
#   t.to_str(...)

def to_str(tree, show_internal=True, compact=False, props=None,
           px=None, py=0, px0=0, py0=0, render_html=False):
    """Return a string containing an ascii drawing of the tree.

    :param show_internal: If True, show the internal nodes too.
    :param compact: If True, use exactly one line per tip.
    :param props: List of node properties to show. If None, show all.
    :param px, py, px0: Paddings (x, y, x for leaves). Overrides `compact`.
    :param render_html: bullshit
    """
    px = px if px is not None else (0 if show_internal else 1)
    py = py if py is not None else (0 if compact else 1)

    lines, _ = ascii_art(tree, show_internal, props, px, py, px0, py0, render_html)
    lines = '\n'.join(lines)
    if render_html:
        lines = f'<span aria-hidden="true">{lines}</span>'
    return lines


# For representations like:
#    ╭╴a
# ╴h╶┤   ╭╴b
#    ╰╴g╶┼╴e╶┬╴c
#        │   ╰╴d
#        ╰╴f

def ascii_art(tree, show_internal=True, props=None, px=0, py=0, px0=0, py0=0, render_html=False):
    """Return list of strings representing the tree, and their middle point.

    :param tree: Tree to represent as ascii art.
    :param show_internal: If True, show the internal node names too.
    :param props: List of properties to show for each node. If None, show all.
    :param px, py: Padding in x and y.
    :param px0: Padding in x for leaves.
    """
    # Node description (including all the requested properties).
    descr = get_descr(tree, props, render_html)
    if render_html:
        tag = str(get_tag(tree, props, descr))
    else:
        tag = descr

    if tree.get_prop('px',''):
        px = tree.get_prop('px','')
    if tree.get_prop('py',''):
        py = tree.get_prop('py','')
    if tree.get_prop('px0',''):
        px0 = tree.get_prop('px0','')
    if tree.get_prop('py0',''):
        py0 = tree.get_prop('py0','')
    if tree.get_prop('cpy0',''):
        cpy0 = tree.get_prop('cpy0','')
    else:
        cpy0 = 0
        # print(py0)
    # TODO add py0, and also perhaps cpx, cpy - child directives

    if tree.is_leaf:
        if render_html:
            tag = wrap_tag(tag)
            if '<img' in tag:
                return (['─' * px0 + tag], 0)
        return (['─' * px0 + '╴' + tag], 0)
    
    

    lines = []

    padding = ((px0 + 1 + len(descr) + 1) if show_internal else 0) + px
    for child in tree.children:
        lines_child, mid = ascii_art(child, show_internal, props, px, py, px0, cpy0, render_html)

        if len(tree.children) == 1:       # only one child
            lines += add_prefix(lines_child, padding, mid, ' ',
                                                           '─',
                                                           ' ')
            lines.extend([' ' * padding] * py0)  # y padding
            pos_first = mid
            pos_last = len(lines) - mid
        elif child == tree.children[0]:   # first child
            lines += add_prefix(lines_child, padding, mid, ' ',
                                                           '┌',
                                                           '│')
            lines.extend([' ' * padding + '│'] * (py + py0))  # y padding
            pos_first = mid
        elif child != tree.children[-1]:  # a child in the middle
            lines += add_prefix(lines_child, padding, mid, '│',
                                                           '├',
                                                           '│')
            lines.extend([' ' * padding + '│'] * (py + py0))  # y padding
        else:                             # last child
            lines += add_prefix(lines_child, padding, mid, '│',
                                                           '└',
                                                           ' ')
            lines.extend([' ' * padding] * py0)  # y padding
            pos_last = len(lines_child) - mid + py0

    mid = (pos_first + len(lines) - pos_last) // 2  # middle point

    lines[mid] = add_base(lines[mid], px, px0, descr, tag, show_internal, render_html)

    return lines, mid

def get_descr(tree, props, render_html=False):
    if render_html:
        return str(tree.get_prop('name', '')) # only render name
    else:
        return ','.join(
            (f'{k}={v}' for k, v in tree.props.items()) if props is None else
            (str(tree.get_prop(p, '')) or '⊗' for p in props))

def get_tag(tree, props, descr):
    id = tree.get_prop('id', '')
    aria_owns = tree.get_child_ids()
    if tree.get_prop('type','') == 'link':
        href = tree.get_prop('href','')
        tag = Element('a', attrib={
            'id': id,
            'aria-owns': aria_owns,
            'href': href,
            'tabindex': '0',
        })
        tag.text = descr
    elif tree.get_prop('type','') == 'img':
        tag = Element('div', attrib={
            'id':id,
            'aria-owns': aria_owns,
            'class':'img-container',
        })

        href = tree.get_prop('href','')
        link = Element('a', attrib={
            'href': href,
            'tabindex': '0',
        })

        src = tree.get_prop('src','')
        width = tree.get_prop('width','')
        img = Element('img', attrib={
            'class': 'img-content',
            'alt': descr,
            'src': src,
            'width': width,
        })

        link.append(img)
        tag.append(link)
    else:
        tag = Element('span', attrib={
            'id': id,
            'aria-owns': aria_owns
        })
        tag.text = descr
    if tree.get_prop('type','') == 'img':
        if tree.is_leaf:
            return tostring(tag, encoding='unicode', method='html') + '──────' # temp
        return tostring(tag, encoding='unicode', method='html') + '────────────' # temp
    else:
        return tostring(tag, encoding='unicode', method='html')

def wrap_tag(tag):
    return f'</span>{tag}<span aria-hidden="true">'

def add_prefix(lines, px, mid, c1, c2, c3):
    """Return the given lines adding a prefix.

    :param lines: List of strings, to return with prefixes.
    :param int px: Padding in x.
    :param int mid: Middle point (index of the row where the node would hang).
    :param c1, c2, c3: Character to use as prefix before, at, and after mid.
    """
    prefix = lambda i: ' ' * px + (c1 if i < mid else (c2 if i == mid else c3))

    return [prefix(i) + line for i, line in enumerate(lines)]

def add_base(line, px, px0, descr, txt, show_internal, render_html=False):
    """Return the same line but adding a base line."""
    # Example of change at the beginning of line: ' │' -> '─┤'
    replacements = {
        '│': '┤',
        '─': '─',
        '├': '┼',
        '┌': '┬'}

    padding = ((px0 + 1 + len(descr) + 1) if show_internal else 0) + px

    if render_html:
        txt = wrap_tag(txt)

    if '<img' in txt:
        prefix_txt = '─' * px0 + f'{txt}'
    else:
        prefix_txt = '─' * px0 + (f'╴{txt}╶' if txt else '──')

    return ((prefix_txt if show_internal else '') +
            '─' * px + replacements[line[padding]] + line[padding+1:])

def insert_text_into_html(filename, css_selector, markup):
    temp_soup = BeautifulSoup(markup, 'html.parser')
    new_tag = temp_soup.div

    with open(filename, "r") as src_file:
        soup = BeautifulSoup(src_file, 'html.parser')
        old_tag = soup.select_one(css_selector)
        old_tag.replace_with(new_tag)

    with open(filename, "w") as dest_file:
        dest_file.write(html.unescape(str(soup)))