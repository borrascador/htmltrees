import re, html, json
from xml.etree.ElementTree import Element, tostring
from bs4 import BeautifulSoup

CHAR_WIDTH_PX = 19.2667
CHAR_HEIGHT_PX = 38

class JSONTreeLoader(object):
    def __init__(self, json_filename):
        f = open(json_filename)
        data = json.load(f)
        self.id_dict = {}
        self.tree = Tree(data=data['tree'], id_dict=self.id_dict)
        self.render_args = data['render_args']
        
    def to_str(self):
        return self.tree.to_str(**self.render_args)

class Tree(object):
    def __init__(self, data=None, children=None, id_dict={}):
        self.id_dict = id_dict
        if 'children' in data:
            self.children = []
            for child in data['children']:
                self.children.append(Tree(data=child, id_dict=self.id_dict))
            del data['children']
            self.props = data.copy()
        else:
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
        while test_id in self.id_dict.keys():
            # if ID not unique, increment ID and check again if unique
            counter += 1
            test_id = id + str(counter)
        # if unique, use that ID
        id = test_id
        self.id_dict[id] = self
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
               px=None, py=None, px0=0, py0=0, blank_start=0, sharp_corners=False, render_html=False, cascade=False, waterfall=False):
        """Return a string containing an ascii drawing of the tree.

        :param show_internal: If True, show the internal nodes too.
        :param compact: If True, use exactly one line per tip.
        :param props: List of node properties to show. If None, show all.
        :param px, py, px0: Paddings (x, y, x for leaves). Overrides `compact`.
        :param sharp_corners: If True, show sharp corners in graph, otherwise use rounded corners.
        :param render_html: If True, format output as accessible HTML
        :param cascade: Use a cascade representation. Overrides
            `show_internal`, `compact`, `px`, `py`, `px0`.
        :param waterfall: Use a waterfall representation.
        """
        return to_str(self, show_internal, compact, props,
                               px, py, px0, py0, blank_start, sharp_corners, render_html, cascade, waterfall)

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
           px=None, py=0, px0=0, py0=0, blank_start=0, sharp_corners=False, render_html=False, cascade=False, waterfall=False):
    """Return a string containing an ascii drawing of the tree.

    :param show_internal: If True, show the internal nodes too.
    :param compact: If True, use exactly one line per tip.
    :param props: List of node properties to show. If None, show all.
    :param px, py, px0: Paddings (x, y, x for leaves). Overrides `compact`.
    :param sharp_corners: If True, show sharp corners in graph, otherwise use rounded corners.
    :param render_html: If True, format output as accessible HTML
    :param cascade: Use a cascade representation. Overrides
        `show_internal`, `compact`, `px`, `py`, `px0`.
        Warning: cascade does not support HTML output.
    :param waterfall: Use a waterfall representation.
    """
    if cascade:
        px = px if px is not None else 1
        return to_cascade(tree, props, px, sharp_corners)
    else:
        px = px if px is not None else (0 if show_internal else 1)
        py = py if py is not None else (0 if compact else 1)

        lines, _ = ascii_art(tree, show_internal, props, px, py, px0, py0, sharp_corners, render_html, waterfall)
        
        # Add empty lines at start
        if type(blank_start) is int:
            for index in range(blank_start):
                lines.insert(index,'')

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
#
# Or, if waterfall=True:
# ╴h╶┬╴a
#    ╰╴g╶┬╴b
#        ├╴e╶┬╴c
#        │   ╰╴d
#        ╰╴f

def ascii_art(tree, show_internal=True, props=None, px=0, py=0, px0=0, py0=0, sharp_corners=False, render_html=False, waterfall=False):
    """Return list of strings representing the tree, and their middle point.

    :param tree: Tree to represent as ascii art.
    :param show_internal: If True, show the internal node names too.
    :param props: List of properties to show for each node. If None, show all.
    :param px, py: Padding in x and y.
    :param px0: Padding in x for leaves.
    :param sharp_corners: If True, show sharp corners in graph, otherwise use rounded corners.
    :param render_html: If True, format output as accessible HTML
    :param waterfall: Use a waterfall representation.
    """
    # Node description (including all the requested properties).
    descr = get_descr(tree, props, render_html)
    if render_html:
        tag = str(get_tag(tree, props, descr))
    else:
        tag = descr

    if type(tree.get_prop('px','')) is int:
        px = tree.get_prop('px','')
    if type(tree.get_prop('py','')) is int:
        py = tree.get_prop('py','')
    if type(tree.get_prop('px0','')) is int:
        px0 = tree.get_prop('px0','')
    if type(tree.get_prop('py0','')) is int:
        py0 = tree.get_prop('py0','')
    if type(tree.get_prop('cpy0','')) is int:
        cpy0 = tree.get_prop('cpy0','')
    else:
        cpy0 = 0
        # print(py0)
    # TODO add py0, and also perhaps cpx, cpy - child directives

    if tree.is_leaf:
        if render_html:
            tag = wrap_tag(tag)
            if 'node-container' in tag:
                if tree.get_prop('type','') == 'textbox':
                    return (['─' * px0 + '╴' + tag], 0)
                return (['─' * (px0 + 1) + tag], 0)
        return (['─' * px0 + '╴' + tag], 0)

    lines = []

    padding = ((px0 + 1 + len(descr) + 1) if show_internal else 0) + px
    for child in tree.children:
        lines_child, mid = ascii_art(child, show_internal, props, px, py, px0, cpy0, sharp_corners, render_html, waterfall)

        if len(tree.children) == 1:       # only one child
            lines += add_prefix(lines_child, padding, mid, ' ',
                                                           '─',
                                                           ' ')
            lines.extend([' ' * padding] * py0)  # y padding
            pos_first = mid
            pos_last = len(lines) - mid
        elif child == tree.children[0]:   # first child
            lines += add_prefix(lines_child, padding, mid, ' ',
                                                           '┌' if sharp_corners else '╭',
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
                                                           '└' if sharp_corners else '╰',
                                                           ' ')
            lines.extend([' ' * padding] * py0)  # y padding
            pos_last = len(lines_child) - mid + py0

    mid = (pos_first + len(lines) - pos_last) // 2  # middle point
    if waterfall:
        mid = pos_first

    lines[mid] = add_base(lines[mid], px, px0, descr, tag, show_internal, render_html)

    return lines, mid

def get_descr(tree, props, render_html=False):
    if render_html:
        if tree.get_prop('type', '') in ['img', 'vimeo']:
            char_width = tree.get_prop('char_width',0)
            if tree.get_prop('type','') == 'vimeo':
                width = tree.get_prop('width','')
                char_width = round(int(width) / CHAR_WIDTH_PX)
            if tree.is_leaf:
                return '─' * ((char_width) // 2)
            else:
                return '─' * (char_width)
        if tree.get_prop('type', '') == 'textbox':
            char_width = tree.get_prop('char_width',0)
            return '&nbsp;' * (char_width)
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
        target = tree.get_prop('target','')
        weight = tree.get_prop('weight','regular')
        tag = Element('a', attrib={
            'id': id,
            'aria-owns': aria_owns,
            'aria-label': descr,
            'href': href,
            'target': target,
            'tabindex': '0',
            'style': f'font-weight:{weight};'
        })
        tag.text = descr
    elif tree.get_prop('type','') == 'vimeo':
        tag = Element('div', attrib={
            'id': id,
            'aria-owns': aria_owns,
            'class':'node-container',
        })
        outer = Element('div')
        inner = Element('div', attrib={
            'class':'node-content'
        })

        src = tree.get_prop('src','')
        name = tree.get_prop('name','')
        width = tree.get_prop('width', 334) # 384
        height = tree.get_prop('height', 188) # 216
        iframe_player = Element('iframe', attrib={
            'src': src,
            'title': name,
            'alt': name,
            'width': str(width),
            'height': str(height),
            'frameborder': '0',
            'allow': 'picture-in-picture; clipboard-write;'
        })

        inner.append(iframe_player)
        outer.append(inner)
        tag.append(outer)
    elif tree.get_prop('type','') == 'img':
        tag = Element('div', attrib={
            'id':id,
            'aria-owns': aria_owns,
            'class':'node-container',
        })

        outer = None
        if tree.get_prop('href',''):
            href = tree.get_prop('href','')
            target = tree.get_prop('target','')
            outer = Element('a', attrib={
                'href': href,
                'tabindex': '0',
                'target': target
            })
        else:
            outer = Element('div')

        src = tree.get_prop('src','')
        name = tree.get_prop('name','')
        char_width = tree.get_prop('char_width','')
        img = Element('img', attrib={
            'class': 'node-content',
            'alt': name,
            'src': src,
            'style': f'width:{str(char_width * CHAR_WIDTH_PX)}px;',
        })

        outer.append(img)
        tag.append(outer)
    elif tree.get_prop('type','') == 'textbox':
        char_width = tree.get_prop('char_width','')

        tag = Element('div', attrib={
            'id':id,
            'aria-owns': aria_owns,
            'class':'node-container',
        })
        outer_div = Element('div')

        inner_div = Element('div', attrib={
            'class':'node-content'
        })

        text = tree.get_prop('text','')
        inner_div.text = text
        outer_div.append(inner_div)
        tag.append(outer_div)
    else:
        weight = tree.get_prop('weight','regular')
        tag = Element('span', attrib={
            'id': id,
            'aria-owns': aria_owns,
            'style': f'font-weight:{weight};'
        })
        tag.text = descr
    if tree.get_prop('type','') in ['img', 'vimeo']:
        return tostring(tag, encoding='unicode', method='html') + wrap_tag(descr, False)
    if tree.get_prop('type','') in ['textbox']:
        return tostring(tag, encoding='unicode', method='html') + wrap_tag(descr, False, True)
    else:
        return tostring(tag, encoding='unicode', method='html')

def wrap_tag(tag, reverse=True, textbox=False):
    if reverse:
        return f'</span>{tag}<span aria-hidden="true">'
    if textbox:
        return f'<span class="textbox" aria-hidden="true">{tag}</span>'
    return f'<span aria-hidden="true">{tag}</span>'

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
        '┌': '┬',
        '╭': '┬'}

    padding = ((px0 + 1 + len(descr) + 1) if show_internal else 0) + px

    if render_html:
        txt = wrap_tag(txt)

    if 'node-container' in txt:
        prefix_txt = '─' * px0 + f'{txt}'
    else:
        prefix_txt = '─' * px0 + (f'╴{txt}╶' if txt else '──')

    return ((prefix_txt if show_internal else '') +
            '─' * px + replacements[line[padding]] + line[padding+1:])

# For representations like:
# h
# ├─╴a
# └─┐g
#   ├─╴b
#   ├─┐e
#   │ ├─╴c
#   │ └─╴d
#   └─╴f

def to_cascade(tree, props=None, px=1, are_last=None, sharp_corners=False):
    """Return string with a visual representation of the tree as a cascade."""
    are_last = are_last or []

    # Node description (including all the requested properties).
    descr = ','.join(
        (f'{k}={v}' for k, v in tree.props.items()) if props is None else
        (str(tree.get_prop(p, '')) or '⊗' for p in props))

    branches = get_branches_repr(are_last, tree.is_leaf, px, sharp_corners)

    wf = lambda n, lasts: to_cascade(n, props, px, lasts, sharp_corners)  # shortcut

    return '\n'.join([branches + descr] +
                     [wf(n, are_last + [False]) for n in tree.children[:-1]] +
                     [wf(n, are_last + [True] ) for n in tree.children[-1:]])


def get_branches_repr(are_last, is_leaf, px, sharp_corners):
    """Return a text line representing the open branches according to are_last.

    :param are_last: List of bools that say per level if we are the last node.
    :param is_leaf: says if the node to represent in this line has no children.
    :param px: Padding in x.
    :param sharp_corners: If True, show sharp corners in graph, otherwise use rounded corners.

    Example (for is_leaf=True, px=6)::

      [True , False, True , True , True ] ->
      '│             │      │      ├──────╴'
    """
    if len(are_last) == 0:
        return ''

    prefix = ''.join((' ' if is_last else '│') + ' ' * px
                     for is_last in are_last[:-1])

    return (prefix   + (('└' if sharp_corners else '╰') if are_last[-1] else '├') +
            '─' * px + ('╴' if is_leaf        else '┐'))

def insert_text_into_html(filename, css_selector, markup):
    temp_soup = BeautifulSoup(markup, 'html.parser')
    new_tag = temp_soup.div

    try:
        src_file = open(filename, "r")
    except FileNotFoundError:
        return 'Output file not found'
    else:
        with src_file:
            soup = BeautifulSoup(src_file, 'html.parser')
            old_tag = soup.select_one(css_selector)
            if old_tag:
                old_tag.replace_with(new_tag)
            else:
                return 'Selector not found'

    try:
        dest_file = open(filename, "w")
    except FileNotFoundError:
        return 'Output file not found'
    else:
        with dest_file:
            dest_file.write(html.unescape(str(soup)))
            return 'Success'
