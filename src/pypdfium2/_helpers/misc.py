# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfiumError", "RenderOptimizeMode"]

import enum


class PdfiumError (RuntimeError):
    """ An exception from the PDFium library, detected by function return code. """
    pass


# FIXME non-prefixed public member
class RenderOptimizeMode (enum.Enum):
    """ Page rendering optimization modes. """
    LCD_DISPLAY = 1  #: Optimize for LCD displays (via subpixel rendering).
    PRINTING    = 2  #: Optimize for printing.
