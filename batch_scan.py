"""
@author: François Laboureur

Simple script for brother DS-640, to scan files in a batch. Sane's scanimage has
a batch mode command, but it doesn't work with this printer because the batch 
scan stops when the feeder is empty, and the DS-640 doesn't have a real feeder
(only one document is present in the "feeder").

The scanning occurs in the following steps:
    1. Scan images as long as the user asks for it, in 300dpi resolution in 
       separate tiff image files.
    2. For each page, perform OCR on the document using tesseract in hocr format,
       then convert hocr file to djvu compatible hidden text format.
    3. If the output config is set to bitonal (currently the only mode 
       implemented), convert the file to .pbm image format which is expected by
       cjb2 for djvu conversion.
    4. Convert files to djvu, and merge them with respective ocr
    5. Merge all djvu files to a single multipage file.
    6. Remove temporary files.

To add:
    metadata (scan date in djvu hidden text)

dependencies:
    - sane and the scanimage command to perform the scan
    - tesseract to perform ocr on the pdf file
    - magick to convert image from one format to another
    - beautifulsoup to parse hocr file and convert it to djvu txt file
"""
import os
import sys

from hocr2djvu import hocr_to_djvutxt

# import argparse

# parser = argparse.ArgumentParser(description="Batch scan mode for brother ds-640 using scanimage.")
# parser.add_argument('

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Error codes returned by scanimage. This is not very pretty as I am not sure they
# won't change with updates to sane, but this will do and is an easy fix in case
# they change.
SCANNER_NOT_FOUND = 256
FEEDER_EMPTY = 1792
FEEDER_JAMMED = 1536

# Document sizes:
# | Document          | width [mm] | height [mm] |
# |-------------------+------------+-------------|
# | A4                |        210 |         297 |
# | A5                |        148 |         21O |
# | A6                |        105 |         148 |
# | A7                |         74 |         105 |
# | A8                |         52 |          74 |
# | Carte credit      |         86 |          55 |
# | Attestation Soins |        106 |         283 |
#
# Note that some of these sizes are country-specific. I just like having the common sizes of the documents I scan on hand.
# There is of course AutoDocumentSize option, but I don't like using it, because it may not be perfect.
# Whereas a fixed value will always be what is asked (Except for a negligible rounding error, but it will always be the same).

# Uncomment one of these lines comment the others
scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 210 -y 297 --resolution=300 -o {}" # A4 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 210 -y 148 --resolution=300 -o {}" # A5 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 148 -y 210 --resolution=300 -o {}" # A5 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 148 -y 105 --resolution=300 -o {}" # A6 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 105 -y 148 --resolution=300 -o {}" # A6 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 105 -y 74  --resolution=300 -o {}" # A7 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 74  -y 105 --resolution=300 -o {}" # A7 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 74  -y 52  --resolution=300 -o {}" # A8 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 52  -y 74  --resolution=300 -o {}" # A8 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 86  -y 55  --resolution=300 -o {}" # Carte de credit   - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=no -x 106 -y 283 --resolution=300 -o {}" # Attestation Soins - Portrait

tiff_to_pbm_cmd = "magick {0}.tiff -threshold 70% {0}.pbm"
merge_ocr_cmd = "djvused -e 'select 1; set-txt {0}.djvutxt; save' {0}.djvu"
merge_cmd = "djvm -c {}.djvu *.djvu"

# After a lot of experimentation, I found that the best compression format was 
# djvu bitonal using cjb2 command. Files are small enough that 300dpi is 
# acceptable, although 150dpi is still readable. Below, quality is too bad.
# Reducing dpi must be done before using cjb2, (for instance using 
# magick -resize 50%) as the setting given to cjb2, is a metadata used for 
# scaling of the image.
bitonal_compress_cmd = "cjb2 {0}.pbm {0}.djvu -losslevel 100"
# bitonal_compress_cmd = "cjb2 {0}.pbm {0}.djvu"
ocr_cmd = "tesseract -l fra {} {} hocr"

ret = 1
i = 1
stop = False

msg_string = "q: stop and cancel\ns: stop and save\nnumber: go back to this page\nanything else: scan page {} and keep going."

scans = []

while stop == False:
    print(msg_string.format(i, i))
    cmd = input().strip()

    if cmd == "q":
        stop = True
        print("Exited without saving output")
    elif cmd == "s":
        stop = True

        # Go through all scans, convert hocr to djvutxt if it exists, then write
        # the result to djvu page.
        for (p, filename) in scans:
            os.system(bitonal_compress_cmd.format(p))
            try:
                with open("{}.hocr".format(p)) as fp:
                    hocr_txt = fp.read()
                    djvu_txt = hocr_to_djvutxt(hocr_txt)
                    
                with open("{}.djvutxt".format(p), "w") as fp:
                    fp.write(djvu_txt)

                print("Adding ocr data to page {}".format(p))
                os.system(merge_ocr_cmd.format(p))


            except:
                # TODO: Check that the process has returned somehow?
                eprint("Unable to open {}.hocr, maybe tesseract didn't finish".format(i))
        os.system(merge_cmd.format("0"))
        print("File saved to 0.djvu")

        # ret = os.system(merge_cmd)  
    elif cmd.isdigit() and (n := int(cmd)) > 0:
        i = n

    else:
        out = "{}.tiff".format(i)
        ret = os.system(scan_cmd.format(out))
        if ret == 0:
            scans.append((i, out))
            ret = os.system(ocr_cmd.format(out, i))
            ret = os.system(tiff_to_pbm_cmd.format(i))
            i+=1

