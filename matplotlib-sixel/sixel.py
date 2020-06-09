

"""
A matplotlib backend for displaying figures via sixel terminal graphics

Based on the ipykernel source  code "backend_inline.py"

Based on python example from libsixel "converter.py"

# Copyright (c) IPython Development Team.
# Copyright (c) Hayaki Saito.
# Distributed under the terms of the Modified BSD License.

"""


import io
import sys
import matplotlib

from matplotlib._pylab_helpers import Gcf
from libsixel import *
from PIL import Image

from .xterm import xterm_pixels

from matplotlib.backends.backend_agg import new_figure_manager, FigureCanvasAgg
new_figure_manager  # for check


def resize_fig(figure):
    """ resize figure size, so that it fits into the terminal

    Checks the width and height
    Only makes the figure smaller

    """
    dpi = figure.get_dpi()
    size = figure.get_size_inches()  # w, h
    pixel_size = size * dpi

    pixel_factor = pixel_size / xterm_pixels()

    factor = max(max(pixel_factor), 1)

    size /= factor

    figure.set_size_inches(size)


def write_sixel(image, outfile):
    data = image.tobytes()
    width, height = image.size

    output = sixel_output_new(lambda data, s: s.write(data), outfile)

    try:
        if image.mode == 'RGBA':
            dither = sixel_dither_new(256)
            sixel_dither_initialize(dither, data, width, height, SIXEL_PIXELFORMAT_RGBA8888)
        elif image.mode == 'RGB':
            dither = sixel_dither_new(256)
            sixel_dither_initialize(dither, data, width, height, SIXEL_PIXELFORMAT_RGB888)
        elif image.mode == 'P':
            palette = image.getpalette()
            dither = sixel_dither_new(256)
            sixel_dither_set_palette(dither, palette)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_PAL8)
        elif image.mode == 'L':
            dither = sixel_dither_get(SIXEL_BUILTIN_G8)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G8)
        elif image.mode == '1':
            dither = sixel_dither_get(SIXEL_BUILTIN_G1)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G1)
        else:
            raise RuntimeError('unexpected image mode')
        try:
            sixel_encode(data, width, height, 1, dither, output)
        finally:
            sixel_dither_unref(dither)
    finally:
        sixel_output_unref(output)


def display(figure):
    """ Display figure on stdout as sixel graphic """

    resize_fig(figure)

    buf = io.BytesIO()
    figure.savefig(buf, format="png")
    buf.seek(0)
    image = Image.open(buf)

    write_sixel(image, sys.stdout.buffer)
    sys.stdout.write("\n")


def show(close=False, block=None):
    """Show all figures as SVG/PNG payloads sent to the IPython clients.

    Parameters
    ----------
    close : bool, optional
      If true, a ``plt.close('all')`` call is automatically issued after
      sending all the figures. If this is set, the figures will entirely
      removed from the internal list of figures.
    block : Not used.
      The `block` parameter is a Matplotlib experimental parameter.
      We accept it in the function signature for compatibility with other
      backends.
    """
    try:
        for figure_manager in Gcf.get_all_fig_managers():
            display(figure_manager.canvas.figure)
    finally:
        show._to_draw = []
        # only call close('all') if any to close
        # close triggers gc.collect, which can be slow
        if close and Gcf.get_all_fig_managers():
            matplotlib.pyplot.close('all')


# This flag will be reset by draw_if_interactive when called
show._draw_called = False
# list of figures to draw when flush_figures is called
show._to_draw = []


def draw_if_interactive():
    """
    Is called after every pylab drawing command
    """
    # signal that the current active figure should be sent at the end of
    # execution.  Also sets the _draw_called flag, signaling that there will be
    # something to send.  At the end of the code execution, a separate call to
    # flush_figures() will act upon these values
    manager = Gcf.get_active()
    if manager is None:
        return
    fig = manager.canvas.figure

    # Hack: matplotlib FigureManager objects in interacive backends (at least
    # in some of them) monkeypatch the figure object and add a .show() method
    # to it.  This applies the same monkeypatch in order to support user code
    # that might expect `.show()` to be part of the official API of figure
    # objects.
    # For further reference:
    # https://github.com/ipython/ipython/issues/1612
    # https://github.com/matplotlib/matplotlib/issues/835

    if not hasattr(fig, 'show'):
        # Queue up `fig` for display
        fig.show = lambda *a: display(fig)

    # If matplotlib was manually set to non-interactive mode, this function
    # should be a no-op (otherwise we'll generate duplicate plots, since a user
    # who set ioff() manually expects to make separate draw/show calls).
    if not matplotlib.is_interactive():
        return

    # ensure current figure will be drawn, and each subsequent call
    # of draw_if_interactive() moves the active figure to ensure it is
    # drawn last
    try:
        show._to_draw.remove(fig)
    except ValueError:
        # ensure it only appears in the draw list once
        pass
    # Queue up the figure for drawing in next show() call
    show._to_draw.append(fig)
    show._draw_called = True


def flush_figures():
    """Send all figures that changed

    This is meant to be called automatically and will call show() if, during
    prior code execution, there had been any calls to draw_if_interactive.

    This function is meant to be used as a post_execute callback in IPython,
    so user-caused errors are handled with showtraceback() instead of being
    allowed to raise.  If this function is not called from within IPython,
    then these exceptions will raise.
    """
    if not show._draw_called:
        return

    try:
        # exclude any figures that were closed:
        active = set([fm.canvas.figure for fm in Gcf.get_all_fig_managers()])
        for fig in [fig for fig in show._to_draw if fig in active]:
            display(fig)
    finally:
        # clear flags for next round
        show._to_draw = []
        show._draw_called = False


# Changes to matplotlib in version 1.2 requires a mpl backend to supply a
# default figurecanvas. This is set here to a Agg canvas
# See https://github.com/matplotlib/matplotlib/pull/1125
FigureCanvas = FigureCanvasAgg
