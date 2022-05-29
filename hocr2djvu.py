"""
    Converts an hocr file to a file compatible with djvu hidden text
"""

import re
from bs4 import BeautifulSoup
import bs4

def remove_accents(string):
    """ Not sure if needed"""
    string = re.sub(r"&quot;", r'\"', string)
    string = re.sub(r"&#39;", r"'", string)
    string = re.sub(r"é", r"\\303\\251", string)
    string = re.sub(r"è", r"\\303\\250", string)
    string = re.sub(r"—", r"\\342\\200\\224", string)
    string = re.sub(r"°", r"\\302\\260", string)
    string = re.sub(r"ç", r"\\303\\247", string)
    string = re.sub(r"à", r"\\303\\240", string)
    string = string.strip().rstrip()

    return string

def escape_quotes(string):
    return re.sub("\"", r'\"', string)

def escape_escapes(string):
    return re.sub(r"\\", r'\\\\', string)

def get_bbox(string):
    m = re.search("bbox (\d+) (\d+) (\d+) (\d+)", string)
    xmin = int(m.group(1))
    ymin = int(m.group(2))
    xmax = int(m.group(3))
    ymax = int(m.group(4))

    return (xmin, ymin, xmax, ymax)

def bbox_to_str_flip_y(bbox, page_height):
    (xmin, ymin, xmax, ymax) = bbox
    string = "{} {} {} {}".format(xmin, page_height-ymin, xmax, page_height-ymax)
    return string

def get_bbox_y_flipped(string, page_height):
    bbox = get_bbox(string)
    return bbox_to_str_flip_y(bbox, page_height)

def hocr_to_djvutxt_old(string):
    """ Converts an "hocr" formatted ocr text string to the format compatible
    with djvu hidden text """

    soup = BeautifulSoup(string, 'html.parser', multi_valued_attributes=None)

    # Filtering functions
    is_not_NavigableString = lambda a: type(a) != bs4.element.NavigableString
    is_ocr_page = lambda a: is_not_NavigableString(a) and a['class']  == 'ocr_page'  # page
    is_ocr_carea = lambda a: is_not_NavigableString(a) and a['class'] == 'ocr_carea' # column
    is_ocr_par = lambda a: is_not_NavigableString(a) and a['class']   == 'ocr_par'   # paragraph
    is_ocr_line = lambda a: is_not_NavigableString(a) and a['class']  == 'ocr_line'  # line
    is_ocrx_word = lambda a: is_not_NavigableString(a) and a['class'] == 'ocrx_word' # word
    is_ocr_header = lambda a: is_not_NavigableString(a) and a['class'] == 'ocr_header' # region

    string = ""
    for p in filter(is_ocr_page, soup.body):
        (p_xmin, p_ymin, p_xmax, p_ymax) = get_bbox(str(p['title']))
        string += "\n(page {} {} {} {}".format(p_xmin, p_ymin, p_xmax, p_ymax)
        p_h = p_ymax - p_ymin
        #string += p['title']
       
        for c in filter(is_ocr_carea, p):
            bbox = get_bbox(str(c['title']))
            string += "\n (column {}".format(get_bbox_y_flipped(c['title'], p_h))
            # string += c['title']
            # string += c.attrs)

            for par in filter(is_ocr_par, c):
                string += "\n  (para {}".format(get_bbox_y_flipped(par['title'], p_h))
                # string += par['title']
                # string += par.attrs)

                for l in filter(is_ocr_line, par):
                    string += "\n   (line {}".format(get_bbox_y_flipped(l['title'], p_h))
                    # string += l['title']
                    # string += l.attrs)

                    for word in filter(is_ocrx_word, l):
                        string += "\n    (word {} \"{}\"".format(get_bbox_y_flipped(word['title'], p_h), escape_quotes(word.string))
                        # string += word['title']
                        string += ")"

                    # Closing line
                    string += ")"
                
                # Closing paragraph
                string += ")"

            # Closing column
            string += ")"
        
        # Closing page
        string += ")"

    string = string.strip().rstrip()

    return string

def hocr_to_djvutxt(string):
    """ Converts an "hocr" formatted ocr text string to the format compatible
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



if __name__ == "__main__":
    input_file_stem = "3"

    with open(input_file_stem + ".hocr") as fp:
        data = fp.read()

    string = hocr_to_djvutxt(data)

# string = remove_accents(string)
    print(string)

    with open(input_file_stem + ".djvu.txt", "w") as fp:
        fp.write(string)
