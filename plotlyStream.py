# -*- coding: utf-8 -*-
"""

Plotly offline streaming through ipywidgets

Hsiou-Yuan Liu   hyliu@berkeley.edu
Apr 15, 2017 
"""
from __future__ import division, print_function, with_statement
import plotly.offline as py
import IPython.display
import ipywidgets
from traitlets import Unicode

class UpdaterJS(ipywidgets.HTML): # a widget that has a JavaScript as its content
    _view_module = Unicode("widget-dynamicJS-exec").tag(sync=True)
    _view_name = Unicode("HelloView").tag(sync=True)
    value = Unicode("").tag(sync=True)

class JupyterNotebookPlotlyStream:
    def __init__(self):
        initialized = getattr(py.offline, '__PLOTLY_OFFLINE_INITIALIZED') # due to name mangling...
        if not initialized:
            raise RuntimeError('\n'.join([
                'Plotly Offline mode requires an initialization.',
                'Run the following at the start of a Jupyter notebook:',
                '    import plotly',
                '    plotly.offline.init_notebook_mode()']))
        self._fig = None
        self._div_id = None
        self._already_plotted = False

    def setToPlotInNewCell(self):
        """reset the flags for plotting in a new notebook cell
        
        Note that the contents of logs are not reset(!)
        """
        self._already_plotted = False
        self._div_id = None
        
    def firstRun(self):
        assert self._fig is not None

        ## Register interactive JS functions
        # This code is short so being registered multiple times does not hurt
        obj = IPython.display.Javascript(
            'require.undef("widget-dynamicJS-exec");'
            'define("widget-dynamicJS-exec", ["jupyter-js-widgets"], function(widget){'
                'var HelloView = widget.DOMWidgetView.extend({'
                    'render: function(){'
                        'this.pagetitle = document.createElement("div");'
                        'this.pagetitle.appendChild(document.createElement("div"));' # dummy child, needed because update() removes a child
                        'this.el.appendChild(this.pagetitle);'
                    '},'
                    'update: function(){'
                        'var container = this.pagetitle;'
                        'container.removeChild(container.childNodes[0]);'
                        
                        'var child = document.createElement("script");'
                        'child.setAttribute("type", "text/javascript");'
                        'child.textContent = this.model.get("value");'
                        'container.appendChild(child);'
                    '}'
                '});'
                'return {HelloView: HelloView}'
            '})'
        )
        IPython.display.display(obj)

        ## Display the widget 
        self._widget_JS = UpdaterJS()
        IPython.display.display(self._widget_JS)

        ## iplot alternative
        config = {'showLink':True, 'linkText':'Export to plot.ly'}
        validate = True
        plot_html, plotdivid, width, height = py.offline._plot_html(
            self._fig, config, validate, '100%', 525, True # default settings of plotly.offline.iplot
        )

        ## Update
        IPython.display.display(IPython.display.HTML(plot_html))
        self._div_id = str(plotdivid)
        self._already_plotted = True

    def update(self, n_parse_char=1024):
        assert self._fig is not None
        assert self._div_id is not None
        assert self._already_plotted == True

        ## iplot alternative
        config = {'showLink':True, 'linkText':'Export to plot.ly'}
        validate = True
        plot_html, plotdivid, width, height = py.offline._plot_html(
            self._fig, config, validate, '100%', 525, True # default settings of plotly.offline.iplot
        )
        
        ## Process the html text to obtain JS
        # assuming n_parse_char contains all the headers that I want to get rid of
        # The reason to use n_parse_char is that plot_html can be extremely long
        cut_head = plot_html[:n_parse_char].split('<script type="text/javascript">')[-1]
        cut_head += plot_html[n_parse_char:]
        plot_js = cut_head[:-9] # get rid of ending 9 characters "</script>" at the end (without quotations)
        segs = plot_js[:n_parse_char].split(str(plotdivid))
        plot_js = self._div_id.join(segs) + plot_js[n_parse_char:]

        ## Update
        self._widget_JS.value = plot_js

