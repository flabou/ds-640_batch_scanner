# Batch image scanning for DS-640
Simple script for brother DS-640, to scan files in a batch. Sane's scanimage has
a batch mode command, but it doesn't work with this printer because the batch 
scan stops when the feeder is empty, and the DS-640 doesn't have a real feeder
(only one document is present in the "feeder").
The output format is bitonal djvu file with OCR content. 
I like djvu bitonal because it has a very high compression ratio.
It shouldn't be too difficult to change the output file type though as this is 
a very basic script.

The scanning occurs in the following steps:
1. Scan images as long as the user asks for it, in 300dpi resolution in separate 
tiff image files.
2. For each page, perform OCR on the document using tesseract in hocr format,
       then convert hocr file to djvu compatible hidden text format.
3. If the output config is set to bitonal (currently the only mode implemented),
convert the file to .pbm image format which is expected by cjb2 for djvu 
conversion.
4. Convert files to djvu, and merge them with respective ocr
5. Merge all djvu files to a single multipage file.
6. Remove temporary files.

To add:
metadata (scan date in djvu hidden text)

# Usage
Simply run `./batch_scan.py`. Then place a sheet in the "feeder" and once the 
scanner has grabbed it, press enter. Type `s` then `enter` when the last page has
been scanned. The merged file will be 0.djvu. Due to the fact that I am sometimes
unhappy with the result and want to change the processing, all scanned files
remain in the folder and have to be manually deleted. This must be done before 
the next file to scan otherwise the older, not overwritten files may be merged 
in the new file as well.
Finally there is also a bug, where the files are merged in incorrect order when
there is more than 9 files. So you may have to remerge them manually through 
terminal. 

# Dependencies
- sane and the scanimage command to perform the scan
- tesseract to perform ocr on the pdf file
- magick to convert image from one format to another
- beautifulsoup to parse hocr file and convert it to djvu txt file
