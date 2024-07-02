# htmltrees

## Purpose

Generate HTML-formatted tree structures from structured metadata. htmltrees reads JSON-formatted tree data structures and outputs corresponding HTML for displaying interactive, multimedia ASCII-style trees on the web.

Through the use of metadata, htmltrees can display:

  * Plain text
  * Bold text
  * Links
  * Images
  * Embedded videos
  * Multiline textboxes

And all of this is accomplished with full ARIA accessibility support.

## Installation

  1. `$ git clone https://github.com/borrascador/htmltrees`
  2. `$ cd foo`
  3. `$ python setup.py install`

## How to Use

Once installed, you can make the package available in a local python project using the [editable install process](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs).

Here is an example of the python script I use to generate HTML pages from JSON.

```python
import re
from glob import glob
from htmltrees import JSONTreeLoader, insert_text_into_html
# https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs

filecount = 0

for in_filename in glob('html/**/*.json', recursive=True):
    if 'data-layout' not in in_filename:
        filecount += 1
        out_filename = re.sub('json$', 'html', in_filename)
        print(f'Converting {in_filename} to {out_filename}', end='... ')

        tree = JSONTreeLoader(in_filename)
        output_string = tree.to_str()

        css_selector = 'div[id="tree-target"]'
        markup = f'<div class="ascii-art pre-like" id="tree-target">{output_string}</div>'
        result = insert_text_into_html(out_filename, css_selector, markup)
        if result == 'Success':
            print(f'Done. Successfully converted {in_filename} to {out_filename}.')
        elif result == 'Output file not found':
            print(f'Output file not found. Skipping {in_filename}.')
        elif result == 'Selector not found':
            print(f'Selector not found. Skipping {in_filename}.')

print(f'Successfully converted {filecount} files from json to html.')
```

For this to work, there needs to be a JSON file and an HTML file with the same name in the same directory somewhere in `html/`, for example `html/index.html` and `html/index.json`. In this example, `index.html` must have `<div class="pre-like" id="tree-target"></div>` with the following CSS applied to simulate `<pre>` tag styling.

```css
.pre-like {
    display: inline-block;
    unicode-bidi: embed;
    font-family: monospace;
    white-space: pre;
}
```

And here is an example of a valid `index.json` file (a subset of my current homepage) showcasing all listed features:

```json
{
  "render_args": {
    "px0": 1,
    "px": 1,
    "py": 1,
    "py0": 0,
    "props": ["name"],
    "show_internal": true,
    "sharp_corners": false,
    "render_html": true,
    "waterfall": true
  },
  "tree": {
    "name": "Jan",
    "weight": "bold",
    "children": [
      {
        "name": "Photo",
        "weight": "bold",
        "py0": 1,
        "children": [
          {
            "name": "Aquadom",
            "type": "link",
            "href": "photo/aquadom.html",
            "px": 2,
            "py0": 5,
            "children": [
              {
                "name": "Run Slow Description",
                "type": "textbox",
                "text": "<span class=\"textbox\">Using self-made software I turn videos into \nimages, crystallizing moments frozen in time.\n \nI freeze fish, malls, deserts, marathons.</span>",
                "px": 0,
                "px0": 0
              }
            ]
          }
        ]
      },
      {
        "name": "Video",
        "weight": "bold",
        "children": [
          {
            "name": "Run Slow",
            "type": "vimeo",
            "src": "https://player.vimeo.com/video/875121292?badge=0&amp;autopause=0&amp;player_id=0&amp;app_id=58479",
            "width": 334,
            "height": 188,
            "px": 2,
            "children": [
              {
                "name": "Run Slow Description",
                "type": "textbox",
                "text": "<span class=\"textbox\">Experimental music video filmed at the \n2023 Berlin Marathon and set to music by \nCanadian dream-pop trio, \"Men I Trust\".</span><span aria-hidden=\"true\">\n\n\n\n</span>",
                "px": 0,
                "px0": 0
              }
            ]
          }
        ]
      },
      {
        "name": "About me",
        "weight": "bold",
        "type": "link",
        "href": "about.html"
      }
    ]
  }
}
```

## Example Sites

My homepage at https://jantabaczynski.com was generated using `htmltrees`.

## Credits / License

This repository is based on the GPL licensed ETE Toolkit, hosted at https://github.com/etetoolkit/ete.

The purpose of the library is to generate HTML-formatted tree structures from structured metadata. This library recognizes input metadata allowing for the rendering of links and images and with full ARIA accessbility support.