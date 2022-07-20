#!/bin/sh
filename=$(basename -- "$2")
extension="${filename##*.}"
filename="${filename%.*}"

magick -density 300 $2 -quality 95 $filename.jpg
tesseract -l fra $filename.jpg $filename hocr
python hocr2djvu.py -f $filename.hocr
magick $filename.jpg -threshold $1 $filename.pbm
cjb2 $filename{.pbm,.djvu} -losslevel 100 
djvused -e "select 1; set-txt $filename.djvutxt; save" $filename.djvu

gio trash $filename.hocr
gio trash $filename.djvutxt
gio trash $filename.pbm
