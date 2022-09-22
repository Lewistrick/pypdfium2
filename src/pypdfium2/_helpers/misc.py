# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import enum
import pypdfium2._pypdfium as pdfium


class PdfiumError (RuntimeError):
    """ An exception from the PDFium library, detected by function return code. """
    pass


class FileAccess (enum.Enum):
    """
    Different ways how files can be loaded.
    
    .. list-table:: Overview of file access modes
        :header-rows: 1
        :widths: auto
        
        * - Mode
          - PDFium loader
          - Comment
        * - :attr:`.NATIVE`
          - :func:`.FPDF_LoadDocument`
          - File access managed by PDFium in C/C++.
        * - :attr:`.BUFFER`
          - :func:`.FPDF_LoadCustomDocument`
          - Data read incrementally from Python file buffer.
        * - :attr:`.BYTES`
          - :func:`.FPDF_LoadMemDocument64`
          - Data loaded into memory and passed to PDFium at once.
    """
    NATIVE = 0
    BUFFER = 1
    BYTES  = 2


class OptimiseMode (enum.Enum):
    """ Modes defining how page rendering shall be optimised. """
    NONE = 0         #: No optimisation.
    LCD_DISPLAY = 1  #: Optimise for LCD displays (via subpixel rendering).
    PRINTING = 2     #: Optimise for printing.


class OutlineItem:
    """
    Class to store information about an entry in the table of contents ("bookmark").
    
    Parameters:
        level (int):
            Number of parent items.
        title (str):
            String of the bookmark.
        is_closed (bool):
            If :data:`True`, child items shall be hidden by default.
        n_kids (int):
            Number of child bookmarks (>= 0).
        page_index (int | None):
            Zero-based index of the page the bookmark points to.
            May be :data:`None` if the bookmark has no target page (or it could not be determined).
        view_mode (int):
            A view mode constant (:data:`PDFDEST_VIEW_*`) defining how the coordinates of *view_pos* shall be interpreted.
        view_pos (typing.Sequence[float]):
            Target position on the page the viewport should jump to when the bookmark is clicked.
            It is a sequence of :class:`float` values in PDF canvas units.
            Depending on *view_mode*, it can contain between 0 and 4 coordinates.
    """
    
    def __init__(
            self,
            level,
            title,
            is_closed,
            n_kids,
            page_index,
            view_mode,
            view_pos,
        ):
        self.level = level
        self.title = title
        self.is_closed = is_closed
        self.n_kids = n_kids
        self.page_index = page_index
        self.view_mode = view_mode
        self.view_pos = view_pos



def colour_tohex(colour, rev_byteorder):
    """
    Convert an RGBA colour specified by 4 integers ranging from 0 to 255 to a single 32-bit integer as required by PDFium.
    If using regular byte order, the output format will be ARGB. If using reversed byte order, it will be ABGR.
    """
    
    r, g, b, a = colour
    
    # colour is interpreted differently with FPDF_REVERSE_BYTE_ORDER (perhaps inadvertently?)
    if rev_byteorder:
        channels = (a, b, g, r)
    else:
        channels = (a, r, g, b)
    
    c_colour = 0
    shift = 24
    for c in channels:
        c_colour |= c << shift
        shift -= 8
    
    return c_colour


def get_functype(struct, funcname):
    """
    Parameters:
        struct (ctypes.Structure): A structure (e. g. ``FPDF_FILEWRITE``).
        funcname (str): Name of the callback function to implement (e. g. ``WriteBlock``).
    Returns:
        A :func:`ctypes.CFUNCTYPE` instance to wrap the callback function.
        For some reason, this is not done automatically, although the information is present in the bindings file.
        This is a convenience function to retrieve the declaration.
    """
    return {k: v for k, v in struct._fields_}[funcname]


def _invert_dict(dictionary):
    """
    Returns:
        A copy of *dictionary*, with inverted keys and values.
    """
    return {v: k for k, v in dictionary.items()}

def _transform_dict(main, transformer):
    """
    Remap each value of a *main* dictionary through a second *transformer* dictionary, if contained.
    Otherwise, take over the existing value as-is.
    
    Returns:
        Transformed variant of the *main* dictionary.
    """
    output = {}
    for key, value in main.items():
        if value in transformer.keys():
            output[key] = transformer[value]
        else:
            output[key] = value
    return output


#: Convert a PDFium pixel format constant to string, assuming regular byte order.
BitmapTypeToStr = {
    pdfium.FPDFBitmap_Gray: "L",
    pdfium.FPDFBitmap_BGR:  "BGR",
    pdfium.FPDFBitmap_BGRA: "BGRA",
    pdfium.FPDFBitmap_BGRx: "BGRX",
}

# Convert a reverse pixel format string to its regular counterpart.
BitmapStrReverseToRegular = {
    "BGR":  "RGB",
    "BGRA": "RGBA",
    "BGRX": "RGBX",
}

#: Convert a PDFium pixel format constant to string, assuming reversed byte order.
BitmapTypeToStrReverse = _transform_dict(BitmapTypeToStr, BitmapStrReverseToRegular)

#: Convert a PDFium view mode constant (:attr:`PDFDEST_VIEW_*`) to string.
ViewmodeToStr = {
    pdfium.PDFDEST_VIEW_XYZ:   "XYZ",
    pdfium.PDFDEST_VIEW_FIT:   "Fit",
    pdfium.PDFDEST_VIEW_FITH:  "FitH",
    pdfium.PDFDEST_VIEW_FITV:  "FitV",
    pdfium.PDFDEST_VIEW_FITR:  "FitR",
    pdfium.PDFDEST_VIEW_FITB:  "FitB",
    pdfium.PDFDEST_VIEW_FITBH: "FitBH",
    pdfium.PDFDEST_VIEW_FITBV: "FitBV",
    pdfium.PDFDEST_VIEW_UNKNOWN_MODE: "?",
}

#: Convert a PDFium error constant (:attr:`FPDF_ERR_*`) to string.
ErrorToStr = {
    pdfium.FPDF_ERR_SUCCESS:  "Success",
    pdfium.FPDF_ERR_UNKNOWN:  "Unknown error",
    pdfium.FPDF_ERR_FILE:     "File access error",
    pdfium.FPDF_ERR_FORMAT:   "Data format error",
    pdfium.FPDF_ERR_PASSWORD: "Incorrect password error",
    pdfium.FPDF_ERR_SECURITY: "Unsupported security scheme error",
    pdfium.FPDF_ERR_PAGE:     "Page not found or content error",
}

#: Convert a PDFium object type constant (:attr:`FPDF_PAGEOBJ_*`) to string.
ObjectTypeToStr = {
    pdfium.FPDF_PAGEOBJ_UNKNOWN: "unknown",
    pdfium.FPDF_PAGEOBJ_TEXT:    "text",
    pdfium.FPDF_PAGEOBJ_PATH:    "path",
    pdfium.FPDF_PAGEOBJ_IMAGE:   "image",
    pdfium.FPDF_PAGEOBJ_SHADING: "shading",
    pdfium.FPDF_PAGEOBJ_FORM:    "form",
}

#: Convert an object type string to a PDFium constant. Inversion of :data:`.ObjectTypeToStr`.
ObjectTypeToConst = _invert_dict(ObjectTypeToStr)

#: Convert a rotation value in degrees to a PDFium constant.
RotationToConst = {
    0:   0,
    90:  1,
    180: 2,
    270: 3,
}

#: Convert a PDFium rotation constant to a value in degrees. Inversion of :data:`.RotationToConst`.
RotationToDegrees = _invert_dict(RotationToConst)
