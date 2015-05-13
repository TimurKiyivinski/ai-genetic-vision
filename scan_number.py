#!/usr/bin/env python3
import os
import png
import glob
import argparse

class PNGMap:
    def __init__(self, PNGName, PNGArray = []):
        self.name = PNGName
        self.bitmap = PNGArray
        self.dim = len(PNGArray)
        self.size = len(PNGArray) * len(PNGArray[0])
    def line(self):
        bitmapLine = []
        for row in self.bitmap:
            bitmapLine += row
        return bitmapLine
    def mutate(self):
        pass
    def like(self, comparePNG):
        if self.size != comparePNG.size:
            return 0
        thisPNGLine = self.line()
        comparePNGLine = comparePNG.line()
        encounters = 0
        similarities = 0
        for i in range(0, len(thisPNGLine)):
            for ii in range(0, len(thisPNGLine) - i):
                if thisPNGLine[ii] == comparePNGLine[ii]:
                    similarities += 1
                encounters += 1
        return similarities / encounters

def getPNGArray(bitmapFile):
    userFile = open(bitmapFile, 'rb')
    userPNG = png.Reader(userFile)
    width, height, pixels, metadata = userPNG.read()
    arrRow = 0
    bitmapArr = []
    for row in pixels:
        bitmapArr.append([])
        bitmapArr[arrRow] = list(row)
        arrRow += 1
    return bitmapArr

def getPNGResource(resourceDir):
    PNGList = []
    resourceList = os.listdir(resourceDir)
    for PNGFile in resourceList:
        PNGArray = getPNGArray(os.path.join(resourceDir, PNGFile))
        PNGBitmap = PNGMap(PNGFile[:-4], PNGArray)
        PNGList.append(PNGBitmap)
    return PNGList

def printPNGArray(bitmapArr):
    for row in bitmapArr:
        print(row)

def main(args):
    setVerbose = args.verbose
    bitmapFile = args.file
    resourceDir = args.resources
    print(resourceDir)
    if setVerbose:
        print('Reading bitmap %s' % bitmapFile)
    resourcePNG = getPNGResource(resourceDir)
    bitmapArr = getPNGArray(bitmapFile)
    userMap = PNGMap('User', bitmapArr)
    if setVerbose:
        print('User bitmap:')
        printPNGArray(bitmapArr)
        print('Resource bitmaps:')
        for resourceBitmap in resourcePNG:
            print('Resource file (%s):' % resourceBitmap.name)
            printPNGArray(resourceBitmap.bitmap)
    for i in range(0, len(resourcePNG)):
        print(resourcePNG[i].name)
        similarities = userMap.like(resourcePNG[i])
        print(similarities)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-r', '--resources', help='Resource directory name', default='resources', required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    main(args)
