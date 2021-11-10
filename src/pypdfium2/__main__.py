# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import argparse
import concurrent.futures
import pypdfium2 as pdfium
from os.path import (
    join,
    basename,
    splitext
)


def rotation_type(string):
    rotation = int(string)
    assert rotation in (0, 90, 180, 270)
    return rotation

def hex_or_none_type(string):
    if string.lower() == 'none':
        return None
    else:
        return int(string, 0)

def optimise_mode_type(string):
    return pdfium.OptimiseMode[string.lower()]


def pagetext_type(value):
    
    if value == "":
        return
    
    page_indices = []
    splitted = value.split(',')
    
    for page_or_range in splitted:
        
        if '-' in page_or_range:
            
            start, end = page_or_range.split('-')
            start = int(start) - 1
            end   = int(end)   - 1
            
            if start < end:
                pages = [i for i in range(start, end+1)]
            else:
                pages = [i for i in range(start, end-1, -1)]
            
            page_indices.extend(pages)
        
        else:
            
            page_indices.append(int(page_or_range))
    
    return page_indices


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Rasterise PDFs with PyPDFium2"
    )
    parser.add_argument(
        'pdffile',
        help = "Path to the PDF document to render.",
    )
    parser.add_argument(
        '--output', '-o',
        help = "Output directory where to place the serially numbered images.",
    )
    parser.add_argument(
        '--prefix', '-p',
        default = None,
        help = "Prefix for each image filename.",
    )
    parser.add_argument(
        '--password',
        default = None,
        help = "A password to unlock the document, if encrypted.",
    )
    parser.add_argument(
        '--pages',
        default = "",
        type = pagetext_type,
        help = "Numbers of the pages to render. Defaults to all.",
    )
    parser.add_argument(
        '--scale',
        default = '2',
        type = float,
        help = ("Define the resolution of the output images. "
                "By default, one PDF point (1/72in) is rendered to 1x1 pixel. "
                "This factor scales the number of pixels that represent one point."),
    )
    parser.add_argument(
        '--rotation',
        default = 0,
        type = rotation_type,
        help = "Rotate pages by 90, 180 or 270 degrees.",
    )
    parser.add_argument(
        '--background-colour',
        default = '0xFFFFFFFF',
        type = hex_or_none_type,
        help = ("Page background colour as 32-bit ARGB hex string. "
                "Use None for an alpha channel. Defaults to white (0xFFFFFFFF)."),
    )
    parser.add_argument(
        '--no-annotations',
        action = 'store_true',
        help = "Do not render PDF annotations.",
    )
    parser.add_argument(
        '--optimise-mode',
        default = 'none',
        type = optimise_mode_type,
        help = "Select a rendering optimisation mode (none, lcd_display, printing)",
    )
    parser.add_argument(
        '--processes',
        default = os.cpu_count(),
        type = int,
        help = "The number of processes to use for rendering. Defaults to the number of CPU cores."
    )
    return parser.parse_args()


def process_page(
        pdffile,
        i,
        password,
        scale,
        rotation,
        background_colour,
        no_annotations,
        optimise_mode,
        output,
        prefix,
        n_digits,
    ):
    
    with pdfium.PdfContext(pdffile, password) as pdf:
        
        pil_image = pdfium.render_page(
            pdf,
            page_index = i,
            scale = scale,
            rotation = rotation,
            background_colour = background_colour,
            render_annotations = not no_annotations,
            optimise_mode = optimise_mode,
        )
        
    filename = join(output, f"{prefix}{i+1:0{n_digits}}.png")
    pil_image.save(filename)
    
    return filename


def invoke_process_page(args):
    return process_page(*args)


def get_pageargs(args, page_indices, prefix, n_digits):
    
    meta_args = []
    
    for i in page_indices:
        subgroup = [
            args.pdffile,
            i,
            args.password,
            args.scale,
            args.rotation,
            args.background_colour,
            args.no_annotations,
            args.optimise_mode,
            args.output,
            prefix,
            n_digits,
        ]
        meta_args.append(subgroup)
    
    return meta_args


def main():
    
    args = parse_args()  
    
    with pdfium.PdfContext(args.pdffile, args.password) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
    
    if args.pages is None:
        page_indices = [i for i in range(n_pages)]
    else:
        page_indices = args.pages
    
    n_digits = len(str(n_pages))
    
    if args.prefix is None:
        prefix = splitext(basename(args.pdffile))[0] + '_'
    else:
        prefix = args.prefix
    
    pageargs = get_pageargs(args, page_indices, prefix, n_digits)
    
    with concurrent.futures.ProcessPoolExecutor(args.processes) as pool:
        map = pool.map(invoke_process_page, pageargs)
        for filename in map:
            print(filename)


# the if-main guard is necessary for multiprocessing to work correctly
if __name__ == '__main__':
    main()
