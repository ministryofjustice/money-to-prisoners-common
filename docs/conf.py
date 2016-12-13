#!/usr/bin/env python3
import datetime

from mtp_common import VERSION, __version__

extensions = ['sphinx.ext.autodoc']

project = 'Money to Prisoners - Common'
author = 'Ministry of Justice'
copyright = '%d, %s' % (datetime.date.today().year, author)
version = '.'.join(map(str, VERSION[0:2]))
release = __version__

templates_path = []
source_suffix = ['.rst']
master_doc = 'index'
exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']
todo_include_todos = True

pygments_style = 'sphinx'
html_theme = 'alabaster'
html_theme_options = {}
html_static_path = []
