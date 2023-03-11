"""

Code to get screen and window size information for sizing the GUI and choosing
the PDF preview size.

In tkinter there is no easy, portable way to get the full size of the current
window only.  The problem arises from multiple monitor systems, which create
one giant virtual screen window for all the screens.  The approach here is
to open a test window, zoom it, get window the sizing info, and destroy it.

"""

import os
import PySimpleGUI as sg
import tkinter as tk
from . import external_program_calls as ex

def get_usable_image_size(args, window, full_window_width, full_window_height,
                          test_im_wid, test_im_ht, left_pixels, zoom_failure):
    """Get the approximate size of the largest possible PDF preview image that
    can be drawn in `window` in the current screen.

    Pass in an invisible pySimpleGui window with all the usual widgets and
    controls as `window`.  The test image should be larger than the GUI
    controls on the right to measure the row height.

    The `im_wid` and `im_ht` parameters are the width and height of a known
    test image that is "displayed" in the (invisible) window.  The
    `left_pixels` parameter is the number of pixels added to the left side of
    window position."""
    open_win_width, open_win_height = window.Size
    #print(f"DEBUG {open_win_width=}  {open_win_height=}")
    #print(f"DEBUG {full_window_width=}  {full_window_height=}")

    if full_window_width < open_win_width: # Must be an error in full_window_width, fallback.
        if args.verbose:
            print("\nWarning in pdfCropMargins: Error in full window width calculation,"
                    " falling back to default window width.", file=sys.stderr)
        usable_width = open_win_width
    else:
        usable_width = full_window_width

    if full_window_height < open_win_height: # Must be an error in full_window_height, fallback.
        if args.verbose:
            print("\nWarning in pdfCropMargins: Error in full window height calculation,"
                    " falling back to default window height.", file=sys.stderr)
        usable_height = open_win_height
    else:
        usable_height = full_window_height

    non_im_width, non_im_height = (open_win_width - test_im_wid,
                                   open_win_height - test_im_ht)
    usable_im_width, usable_im_height = (usable_width - non_im_width - left_pixels,
                                         usable_height - non_im_height)
    return (usable_im_width, usable_im_height), (non_im_width, non_im_height)

def get_window_size(scaling):
    """Get physical screen dimension to determine the page image max size.  Some
    extra space is reserved for titlebars/borders or other unaccounted-for space
    in the windows."""
    zoom_failure = False
    os = ex.system_os
    if os == "Linuxx" or "Darwin": # Darwin not tested...
        width, height, zoom_failure = get_window_size_tk(scaling)
        width *= .95
        height *= .95
    elif os == "Windows":
        width, height, zoom_failure = get_window_size_sg(scaling)
        width *= .95
        height *= .95
    else:
        # Note this method doesn't always work for multiple-monitor setups
        # on non-Windows systems.  It reports the combined monitor window sizes.
        root = tk.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        #width, height = window.get_screen_size()

        width *= .90
        height *= .90
    return width, height, zoom_failure

def get_window_size_sg(scaling):
    """Get size from a big pySimpleGui window.  Not recommended for non-Windows
    because sg uses fullscreen mode there instead of zoomed mode for `maximize`,
    which doesn't account for taskbar size."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Your title is not a string.")
        layout = [  [sg.Text('Sizer...')], ]
        window = sg.Window('Sizer', alpha_channel=0,
                    no_titlebar=False, # Cannot maximize/zoom without a titlebar.
                    resizable=True, size=(200,200), scaling=scaling, layout=layout,
                    finalize=True)
    default_width, default_height = window.Size
    window.Maximize()
    window.Read(timeout=20) # Needs this to maximize correctly.
    zoomed_wid, zoomed_ht = window.Size
    window.close()
    if zoomed_width == default_width or zoomed_height == default_height:
        zoom_failure = True
    return zoomed_wid, zoomed_ht, zoom_failure

def get_window_size_tk(scaling):
    """Use tk to get an approximation to the usable screen area."""
    # Tkinter universal calls: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/universal.html
    # Mac, Linux, Windows attributes here: https://wiki.tcl-lang.org/page/wm+attributes

    root = tk.Tk()
    # Info on scaling: https://github.com/PySimpleGUI/PySimpleGUI/issues/1907
    root.tk.call('tk', 'scaling', scaling)

    default_width = root.winfo_width()
    default_height = root.winfo_height()

    try:
        if ex.system_os == "Linux":
            # Go to fullscreen mode to get screen size.  This seems to work with
            # multiple monitors (which otherwise get counted at a combined size).
            root.attributes("-alpha", 0) # Invisible on systems with compositing window manager.
            #root.attributes("-fullscreen", True) # Set to actual full-screen size.
            root.attributes("-zoomed", True) # Zoomed mode also includes the title bar.
            # This seems to eliminate the flash that occurs on the update below.
            root.attributes("-type", "splash") # https://www.tcl.tk/man/tcl8.6/TkCmd/wm.htm#M12

            #root.update()
            root.update_idletasks() # This works in place of .update, on Linux.
            width = root.winfo_width()
            height = root.winfo_height()
        elif ex.system_os == "Darwin":
            root.attributes("-alpha", 0) # Invisible on most systems.
            root.attributes("-fullscreen", True) # Set to actual full-screen size.
            #root.attributes("-zoomed", True) # Darwin doesn't support zoomed attribute.
            # This seems to eliminate the flash that occurs on the update below.
            root.attributes("-type", "splash") # https://www.tcl.tk/man/tcl8.6/TkCmd/wm.htm#M12

            #root.update()
            root.update_idletasks() # This works in place of .update, on Linux.
            width = root.winfo_width()
            height = root.winfo_height()
        elif ex.system_os == "Windows":
            root.state("zoomed") # Maximize the window on Windows.
            root.attributes("-alpha", 0) # Invisible on most systems.
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
        else:
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
    except tk.TclError as e:
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
    root.destroy()
    zoom_failure = False
    if width == default_width or height == default_height:
        zoom_failure = True
    return width, height, zoom_failure

