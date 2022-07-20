#!/bin/sh
filename=$(basename -- "$1")
extension="${filename##*.}"
filename="${filename%.*}"

magick -density 300 $2 -quality 95 $filename.jpg
tesseract -l fra $filename.jpg $filename hocr
python hocr2djvu.py -f $filename.hocr
c44 -slice 80,85 $filename.jpg $filename.djvu
djvused -e "select 1; set-txt $filename.djvutxt; save" $filename.djvu

gio trash $filename.hocr
gio trash $filename.djvutxt
