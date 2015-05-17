#!/usr/bin/env python3
import os
import sys
import png
import glob
import copy
import random
import argparse
from multiprocessing import Process, Queue

MUTRATE = 1/9
ADDRATE = 3
GENRATE = 6

class Coordinates:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def get(self):
        return self.x, self.y

class PNGMap:
    def __init__(self, PNGName, PNGArray = [], PNGWhite = 1):
        self.name = PNGName
        self.bitmap = PNGArray
        self.white = PNGWhite
        self.dim = len(PNGArray)
        self.size = len(PNGArray) * len(PNGArray[0])
    def inverse(self, bit):
        if bit == self.white:
            return 0
        else:
            return self.white
    def surrounded(self, x, y):
        sim = 0
        if self.bitmap[x - 1][y] != self.white:
            sim += 1
        if self.bitmap[x + 1][y] != self.white:
            sim += 1
        if self.bitmap[x][y - 1] != self.white:
            sim += 1
        if self.bitmap[x][y + 1] != self.white:
            sim += 1
        return sim == 4
    def line(self):
        bitmapLine = []
        for row in self.bitmap:
            bitmapLine += row
        return bitmapLine
    def breed(self, partnerMap):
        babyArray = []
        splitLine = random.randrange(1, self.dim)
        for i in range(0, splitLine):
            babyArray.append(self.bitmap[i])
        for i in range(splitLine + 1, self.dim):
            babyArray.append(partnerMap.bitmap[i])
        babyMap = PNGMap(self.name, babyArray)
        return babyMap
    def mutate(self):
        mutationType = 0
        if mutationType == 0:
            charCo = []
            for i in range(0, self.dim):
                for ii in range(0, self.dim):
                    if self.bitmap[i][ii] != self.white:
                        charCo.append(Coordinates(i, ii))
            noAdds = random.randrange(1, ADDRATE)
            print('Number of mutations: %i' % noAdds)
            for i in range(0, noAdds):
                print('Addition number: %i' % i)
                addAt = random.randrange(0, len(charCo))
                addFriend = charCo[addAt]
                addX, addY = addFriend.get()
                added = False
                while not added:
                    addDir = random.randrange(0, 4)
                    if addDir in range(0, 2):
                        if addX in range(1, self.dim):
                            if addDir == 0:
                                if not self.surrounded(addX - 1, addY):
                                    self.bitmap[addX - 1][addY] = self.inverse(self.bitmap[addX - 1][addY])
                                else:
                                    continue
                            elif addDir == 1:
                                if not self.surrounded(addX + 1, addY):
                                    self.bitmap[addX + 1][addY] = self.inverse(self.bitmap[addX + 1][addY])
                                else:
                                    continue
                            added = True
                        else:
                            continue
                    elif addDir in range(2, 4):
                        if addY in range(1, self.dim):
                            if addDir == 2:
                                if not self.surrounded(addX, addY - 1):
                                    self.bitmap[addX][addY - 1] = self.inverse(self.bitmap[addX][addY - 1])
                                else:
                                    continue
                            elif addDir == 3:
                                if not self.surrounded(addX, addY + 1):
                                    self.bitmap[addX][addY + 1] = self.inverse(self.bitmap[addX][addY + 1])
                                else:
                                    continue
                            added = True
                        else:
                            continue
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

def randParent(PNGMaps, totalFitness, compareMap, threadQueue):
    roulette = random.uniform(0, totalFitness)
    for listMap in PNGMaps:
        roulette -= listMap.like(compareMap)
        if roulette < 0:
            threadQueue.put(listMap)
            break

def genParents(PNGMaps, compareMap):
    parentsA = []
    parentsB = []
    totalFitness = sum(listMap.like(compareMap) for listMap in PNGMaps)
    threadsA = []
    threadsB = []
    queueA = Queue()
    queueB = Queue()
    for listMap in PNGMaps:
        threadA = Process(target=randParent, args=(PNGMaps, totalFitness, compareMap, queueA))
        threadB = Process(target=randParent, args=(PNGMaps, totalFitness, compareMap, queueB))
        threadA.start()
        threadB.start()
        threadsA.append(threadA)
        threadsB.append(threadB)
    for thread in threadsA:
        if not queueA.empty():
            parentsA.append(queueA.get())
        thread.join()
    for thread in threadsB:
        if not queueB.empty():
            parentsB.append(queueB.get())
        thread.join()
    return parentsA, parentsB

def createGenerations(userMutations, resourceBitmap, finalMutation):
    if not finalMutation.empty():
        return
    for userChild in userMutations:
        if resourceBitmap.like(userChild) >= 0.98:
            finalMutation.put(resourceBitmap)
            finalMutation.put(userChild)
            return
    parentsA, parentsB = genParents(userMutations, resourceBitmap)
    newChildren = []
    for i in range(0, len(parentsA)):
        newChild = parentsA[i].breed(parentsB[i])
        newChildren.append(newChild)
    createGenerations(newChildren, resourceBitmap, finalMutation)

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
        for bit in row:
            sys.stdout.write(str(bit))
        print('')

def main(args):
    setVerbose = args.verbose
    bitmapFile = args.file
    resourceDir = args.resources
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
    userMutations = []
    for i in range(0, GENRATE):
        if setVerbose:
            print('Generating user mutation no (%i)' % i)
        mutationNext = copy.deepcopy(userMap)
        mutationNext.mutate()
        userMutations.append(mutationNext)
    threads = []
    finalMutation = Queue()
    for resourceBitmap in resourcePNG:
        if resourceBitmap.like(userMap) >= 0.98:
            finalMutation.put(resourceBitmap)
            finalMutation.put(userMap)
            break
        thread = Process(target=createGenerations , args=(userMutations, resourceBitmap, finalMutation))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    valueMap = finalMutation.get()
    print('The detected value is %s.' % valueMap.name)
    valueMap = finalMutation.get()
    print('The final mutation is:')
    printPNGArray(valueMap.bitmap)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-r', '--resources', help='Resource directory name', default='resources', required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    main(args)
