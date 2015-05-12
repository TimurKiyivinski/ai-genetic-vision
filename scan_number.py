#!/usr/bin/env python3
import png
import argparse

def getPNGArray(bitmapFile):
    userFile = open(bitmapFile, 'rb')
    userPNG = png.Reader(userFile)
    width, height, pixels, lol = userPNG.read()
    arrRow = 0
    bitmapArr = []
    for row in pixels:
        bitmapArr.append([])
        bitmapArr[arrRow] = list(row)
        arrRow += 1
    return bitmapArr

def printPNGArray(bitmapArr):
    for row in bitmapArr:
        print(row)

def main(args):
    setVerbose = args.verbose
    bitmapFile = args.file
    if setVerbose:
        print('Reading bitmap %s' % bitmapFile)
    bitmapArr = getPNGArray(bitmapFile)
    if setVerbose:
        printPNGArray(bitmapArr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    main(args)
