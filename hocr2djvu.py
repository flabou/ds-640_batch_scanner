"""hocr to djvutxt converter

Converts an hocr OCR file to a file compatible with djvu hidden text.

This module can be used as a script from the command line by providing the
-f argument for the hocr file to convert to a .djvutxt file. It can also 
be imported to use the hocr_to_djvutxt function which doesn't mannage files
and simply outputs a string.
"""

import re
from bs4 import BeautifulSoup
import bs4
import os
import argparse
import sys
from pathlib import Path
from typing import Tuple


def path_arg_type(path_str: str) -> Path:
    """Simple validator for the provided path."""
    p = Path(path_str)
    if not p.exists():
        raise ValueError

    return p

# Argument parser to allow usage from command line
parser = argparse.ArgumentParser(description='Convert hocr format OCR file to djvutxt format.')

parser.add_argument('--file', '-f', type=path_arg_type,
                    help="hocr file to convert to djvutxt.")

# Parse arguments from command line
args = parser.parse_args(sys.argv[1:])


def escape_quotes(string: str) -> str:
    return re.sub("\"", r'\"', string)

def escape_escapes(string: str) -> str:
    return re.sub(r"\\", r'\\\\', string)

def get_bbox(string: str) -> tuple[int, int , int, int]:
    m = re.search("bbox (\d+) (\d+) (\d+) (\d+)", string)
    xmin = int(m.group(1))
    ymin = int(m.group(2))
    xmax = int(m.group(3))
    ymax = int(m.group(4))

    return (xmin, ymin, xmax, ymax)

def bbox_to_str_flip_y(bbox: tuple[int, int, int, int], page_height: int) -> str:
    (xmin, ymin, xmax, ymax) = bbox
    string = "{} {} {} {}".format(xmin, page_height-ymin, xmax, page_height-ymax)
    return string

def get_bbox_y_flipped(string: str, page_height: int) -> str:
    bbox = get_bbox(string)
    return bbox_to_str_flip_y(bbox, page_height)

def hocr_to_djvutxt(string: str) -> str:
    """Converts an hocr formatted OCR text string to the format compatible
    with djvu hidden text """

    soup = BeautifulSoup(string, 'html.parser', multi_valued_attributes=None)

    # List of hocr elements and their corresponding keyword in djvutxt.
    # The syntax of djvutxt is found in the man page of 'djvused'
    hocr_corespondance = {
            'ocr_page': 'page',
            'ocr_carea': 'column',
            'ocr_par': 'para',
            'ocr_line': 'line',

            # There is no header in djuvtxt. Region would maybe make sense as 
            # an equivalent, but it causes trouble when a "region" comes before 
            # other elements of lower importance. djvutxt expects elements 
            # in decreasing order of importance. So we use line instead.
            'ocr_header': 'line',
            'ocr_textfloat': 'line',
            'ocr_caption': 'line',

            'ocrx_word': 'word',
            }


    p_h = 0
    
    def recursive_conversion(string_array, element, indentation):
        """ This function provides a simple general way of performing conversion
        to djvutxt. There is no assumption on the order of elements, they are
        added as they come. string_array should be a list of a single string [""].
        The need for a list is simply to keep the data in the string when leaving
        the function."""

        global p_h
        is_not_NavigableString = lambda a: type(a) != bs4.element.NavigableString

        for e in element:
            if is_not_NavigableString(e) and 'class' in e.attrs and e['class'] in hocr_corespondance.keys():
                string_array[0] += "\n{}({}".format(indentation, hocr_corespondance[e['class']])

                if e['class'] == 'ocr_page':
                    (p_xmin, p_ymin, p_xmax, p_ymax) = get_bbox(str(e['title']))
                    string_array[0] += " {} {} {} {}".format(p_xmin, p_ymin, p_xmax, p_ymax)
                    p_h = p_ymax - p_ymin
                else:
                    string_array[0] += " {}".format(get_bbox_y_flipped(e['title'], p_h))

                if e.string:
                    string_array[0] += " \"{}\"".format(escape_quotes(escape_escapes(e.string)))

                recursive_conversion(string_array, e, indentation + " ")
                string_array[0] += ")"

    string = [""]

    recursive_conversion(string, soup.body, "")

    return string[0]

if args.file:
    with open(args.file) as fp:
        s = fp.readlines()
        input_s = "".join(s)
    
    output_s = hocr_to_djvutxt(input_s)

    with open(args.file.with_suffix(".djvutxt"), "w") as fp:
        fp.write(output_s)
