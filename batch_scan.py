"""
@author: François Laboureur

Simple script for brother DS-640, to scan files in a batch. Sane's scanimage has
a batch mode command, but it doesn't work with this printer because the batch 
scan stops when the feeder is empty, and the DS-640 doesn't have a real feeder
(only one document is present in the "feeder").

The scanning occurs in the following steps:
    1. Scan images as long as the user asks for it, in 300dpi resolution in jpg files.
    2. Merge files as a single pdf file.
    3. Remove temporary files.

dependencies:
    - sane and the scanimage command to perform the scan
    - magick to convert image from one format to another
"""
import os
import sys
import shlex
from subprocess import check_output

# Quality of jpg can be reduce to produce smaller size pdf files
tiff_to_jpg_cmd = "magick {0}.tiff -quality 100 {0}.jpg"
merge_cmd = "magick {0} {1}"

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
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 210 -y 148 --resolution=300 -o {}" # A5 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 148 -y 210 --resolution=300 -o {}" # A5 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 148 -y 105 --resolution=300 -o {}" # A6 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 105 -y 148 --resolution=300 -o {}" # A6 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 105 -y 74  --resolution=300 -o {}" # A7 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 74  -y 105 --resolution=300 -o {}" # A7 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 74  -y 52  --resolution=300 -o {}" # A8 - Paysage
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 52  -y 74  --resolution=300 -o {}" # A8 - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 86  -y 55  --resolution=300 -o {}" # Carte de credit   - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev2' --AutoDeskew=yes --AutoDocumentSize=no -x 106 -y 283 --resolution=300 -o {}" # Attestation Soins - Portrait
#scan_cmd = "scanimage -d 'brother5:bus2;dev1' --AutoDeskew=yes --AutoDocumentSize=yes --resolution=300 -o {}" # Auto - Portrait

def exec_cmd(cmd, stderr=None):
    cmd_list = shlex.split(cmd)
    return check_output(cmd_list, stderr=stderr).decode()


original_dir = os.getcwd()
working_dir = exec_cmd("mktemp -d").strip()
os.chdir(working_dir)

ret = 1
i = 1
stop = False

msg_string = "q: cancel; s: end and save; number: go back to page; empty string: scan page {} and keep going."

last_page = 0
while stop == False:
    print(msg_string.format(i, i))
    cmd = input().strip()

    # Scan next page
    if cmd == "":
        try:
            out = "{}.tiff".format(i)
            exec_cmd(scan_cmd.format(out))
            if(i > last_page):
                last_page = i

            ret = exec_cmd(tiff_to_jpg_cmd.format(i))
            i+=1 
        
        except:
            print("Scan of page {} failed".format(i))

    # Exit without saving
    elif cmd == "q":
        stop = True
        print("Exited without saving output")
        print(exec_cmd(("rm -r {}".format(working_dir))))

    # Save result i.e. merge
    elif cmd == "s":
        stop = True

        page_sequence = " ".join([str(k) + ".jpg" for k in range(1, last_page+1)])
        print(exec_cmd(merge_cmd.format(page_sequence, "output.pdf")))
        print(exec_cmd(("mv {} {}".format("output.pdf", original_dir))))
        os.chdir(original_dir)
        print(exec_cmd(("rm -r {}".format(working_dir))))
        print("File saved to output.pdf")

    elif cmd.isdigit() and (n := int(cmd)) > 0:
        i = n

    # Any other command is ignored
    else:
        print("Unknown command '{}'".format(cmd))
