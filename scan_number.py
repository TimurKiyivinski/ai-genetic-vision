#!/usr/bin/env python3
import os
import sys
import png
import glob
import copy
import random
import argparse
from multiprocessing import Process, Queue

# Mutation rate out of 10; n % 10 == 1
MUTRATE = 8
# Number of possible mutations added
ADDRATE = 6
# Number of children generated
GENRATE = 6
# Similarity rate required for bitmap comparisons
SIMRATE = 0.5
# Maximum number of generations
RECRATE = 20

# Class to contain the X and Y coordinates
class Coordinates:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def get(self):
        return self.x, self.y

# Main PNG Bitmap class, stores all the bitmaps
class PNGMap:
    def __init__(self, PNGName, PNGArray = [[]], PNGWhite = 1):
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
        if x > 0 and y in range(0, self.dim):
            if self.bitmap[x - 1][y] != self.white:
                sim += 1
        if x < len(self.bitmap) - 1 and y in range(0, self.dim):
            if self.bitmap[x + 1][y] != self.white:
                sim += 1
        if y > 0 and x in range(0, self.dim):
            if self.bitmap[x][y - 1] != self.white:
                sim += 1
        if y < len(self.bitmap[0]) - 1 and x in range(0, self.dim):
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
        for i in range(splitLine, self.dim):
            babyArray.append(partnerMap.bitmap[i])
        babyMap = PNGMap(self.name, babyArray)
        return babyMap
    def lmost(self):
        leftMost = self.dim
        for row in self.bitmap:
            for i in range(0, self.dim):
                if row[i] != self.white:
                    if i < leftMost:
                        leftMost = i
        return leftMost
    def rmost(self):
        rightMost = 0
        for row in self.bitmap:
            for i in range(0, self.dim):
                if row[i] != self.white:
                    if i > rightMost:
                        rightMost = i
        return rightMost
    def umost(self):
        for i in range(0, self.dim):
            for ii in range(0, self.dim):
                if self.bitmap[i][ii] != self.white:
                    return i
    def dmost(self):
        downMost = 0
        for i in range(0, self.dim):
            for ii in range(0, self.dim):
                if self.bitmap[i][ii] != self.white:
                    if i > downMost:
                        downMost = i
        return downMost
    def zone(self):
        zoneBitmap = self.bitmap
        for i in range(self.umost(), self.dmost()):
            for ii in range(self.lmost(), self.rmost() + 1):
                if zoneBitmap[i][ii] != self.white:
                    zoneBitmap[i][ii] = self.white
                    break
            for ii in reversed(range(self.lmost(), self.rmost() + 1)):
                if zoneBitmap[i][ii] != self.white:
                    zoneBitmap[i][ii] = self.white
                    break
    # Mutates the current bitmap, vital part of a genetic algorithm
    def mutate(self):
        # need to improve this for user detection.. most probable culprit
        mutationType = random.randrange(0, 10)
        if mutationType < 6:
            charCo = []
            for i in range(0, self.dim):
                for ii in range(0, self.dim):
                    if self.bitmap[i][ii] != self.white:
                        charCo.append(Coordinates(i, ii))
            noAdds = random.randrange(1, ADDRATE)
            for i in range(0, noAdds):
                addAt = random.randrange(0, len(charCo))
                addFriend = charCo[addAt]
                addX, addY = addFriend.get()
                added = False
                tries = []
                while not added:
                    if len(set([0, 1, 2, 3]) & set(tries)) == 4:
                        i -= 1
                        break
                    addDir = random.randrange(0, 4)
                    if addDir in range(0, 2):
                        if addX in range(1, self.dim):
                            if addDir == 0 and addX > 0:
                                if not self.surrounded(addX - 1, addY):
                                    self.bitmap[addX - 1][addY] = self.inverse(self.bitmap[addX - 1][addY])
                                else:
                                    tries.append(0)
                                    continue
                            elif addDir == 1 and addX < self.dim - 1:
                                if not self.surrounded(addX + 1, addY):
                                    self.bitmap[addX + 1][addY] = self.inverse(self.bitmap[addX + 1][addY])
                                else:
                                    tries.append(1)
                                    continue
                            added = True
                        else:
                            continue
                    elif addDir in range(2, 4):
                        if addY in range(1, self.dim):
                            if addDir == 2 and addY > 0:
                                if not self.surrounded(addX, addY - 1):
                                    self.bitmap[addX][addY - 1] = self.inverse(self.bitmap[addX][addY - 1])
                                else:
                                    tries.append(2)
                                    continue
                            elif addDir == 3 and addY < self.dim - 1:
                                if not self.surrounded(addX, addY + 1):
                                    self.bitmap[addX][addY + 1] = self.inverse(self.bitmap[addX][addY + 1])
                                else:
                                    tries.append(3)
                                    continue
                            added = True
                        else:
                            continue
        elif mutationType > 8:
            noAdds = random.randrange(1, ADDRATE)
            for row in self.bitmap:
                for i in range(0, len(row) - 1):
                    if row[i] != self.white:
                        if row[i + 1] == self.white:
                            row[i + 1] = row[i]
                            break
    # Checks how similar another bitmap is compared
    # to the current bitmap
    def like(self, comparePNG):
        if self.size != comparePNG.size:
            return 0
        thisPNGLine = self.line()
        comparePNGLine = comparePNG.line()
        similarities = 0
        encounters = 0
        for i in range(0, len(thisPNGLine)):
            for ii in range(0, len(thisPNGLine) - i):
                if thisPNGLine[ii] != self.white:
                    if thisPNGLine[ii] == comparePNGLine[ii]:
                        similarities += 1
                    encounters += 1
        return float(float(similarities) / float(encounters))
    def similar(self, comparePNGs):
        return sum(float(self.like(comparePNG)) for comparePNG in comparePNGs)
        
#TODO: This function may or may not find a partner
def randPair(PNGMaps, compareMaps, totalFitness, threadQueue):
    roulette = random.uniform(0, totalFitness)
    for listMap in PNGMaps:
        roulette -= listMap.similar(compareMaps)
        if roulette <= 0:
            threadQueue.put(listMap)
            return
    print('Error')
    return PNGMaps[random.randint(0, len(PNGMaps) - 1)]

def genPairs(PNGMaps, compareMaps):
    pairA = []
    pairB = []
    totalFitness = len(compareMaps)
    threadsA = []
    threadsB = []
    queueA = Queue()
    queueB = Queue()
    for listMap in PNGMaps:
        threadA = Process(target=randPair , args=(PNGMaps, compareMaps, totalFitness, queueA))
        threadB = Process(target=randPair , args=(PNGMaps, compareMaps, totalFitness, queueB))
        threadA.start()
        threadB.start()
        threadsA.append(threadA)
        threadsB.append(threadB)
    while not len(pairA) == len(PNGMaps):
        pairA.append(queueA.get())
    while not len(pairB) == len(PNGMaps):
        pairB.append(queueB.get())
    for thread in threadsA:
        thread.join()
    for thread in threadsB:
        thread.join()
    return pairA, pairB

def evolutionGen(userMutations, resourceBitmaps, recursionDepth, bestMap, resMap = PNGMap('Default')):
    recursionDepth += 1
    print('Currently at generation: %i' % recursionDepth)
    for userChild in userMutations:
        finalRes = False
        for resourceBitmap in resourceBitmaps:
            if userChild.like(resourceBitmap) > bestMap.like(resMap):
                bestMap = copy.deepcopy(userChild)
                resMap = resourceBitmap
    print('Last similarity is %f' % bestMap.like(resMap))
    if bestMap.like(resMap) >= SIMRATE:
        return bestMap, resMap
    if recursionDepth < RECRATE:
        parentsA, parentsB = genPairs(userMutations, resourceBitmaps)
        newChildren = []
        for i in range(0, len(parentsA)):
            newChild = copy.deepcopy(parentsA[i].breed(parentsB[i]))
            if random.randint(0, 10) % MUTRATE >= 1:
                newChild.mutate()
            newChildren.append(newChild)
        return evolutionGen(newChildren, resourceBitmaps, recursionDepth, bestMap, resMap)
    else:
        print('Evolution ended at generation: %i' % recursionDepth)
        return bestMap, resMap

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
        PNGBitmap = PNGMap(PNGFile, PNGArray)
        PNGList.append(PNGBitmap)
    return PNGList

def printPNGArray(bitmapArr):
    for row in bitmapArr:
        for bit in row:
            sys.stdout.write(str(bit))
        print('')

def main(args):
    # Read the command line arguments and set default values
    setVerbose = args.verbose
    bitmapFile = args.file
    compareFile = args.compare
    resourceDir = args.resources
    saveDir = args.save
    mutateCount = int(args.mutate)
    print('Reading bitmap %s' % bitmapFile)
    bitmapArr = getPNGArray(bitmapFile)
    userMap = PNGMap('User', bitmapArr)
    # Compare Operation
    if compareFile != '':
        compareArr = getPNGArray(compareFile)
        compareMap = PNGMap('Compare', compareArr)
        for i in range(0, mutateCount):
            userMap.mutate()
        if setVerbose:
            print('User bitmap:')
            printPNGArray(userMap.bitmap)
            print('Compare bitmap:')
            printPNGArray(compareMap.bitmap)
        print('Similarity between %s and %s is:' % (userMap.name, compareMap.name))
        print(userMap.like(compareMap))
        return
    # Normal operation
    # Load all the resources into an array
    resourcePNG = getPNGResource(resourceDir)
    if setVerbose:
        print('User bitmap:')
        printPNGArray(bitmapArr)
        print('Resource bitmaps:')
        for resourceBitmap in resourcePNG:
            print('Resource file (%s):' % resourceBitmap.name)
            printPNGArray(resourceBitmap.bitmap)
    userMutations = []
    userMutations.append(copy.deepcopy(userMap))
    for i in range(0, GENRATE - 1):
        if setVerbose:
            print('Generating user mutation no (%i)' % i)
        mutationNext = copy.deepcopy(userMap)
        mutationNext.mutate()
        userMutations.append(mutationNext)
        if setVerbose:
            printPNGArray(mutationNext.bitmap)
    threads = []
    finalMutation = Queue()
    bestMutation = Queue()
    finalUser, finalResource = evolutionGen(userMutations, resourcePNG, 0, userMap)
    # Results
    print('The detected value is: %s' % finalResource.name)
    if setVerbose:
        printPNGArray(finalUser.bitmap)
    if saveDir != False:
        saveImage = png.from_array(finalUser.bitmap, 'L;1')
        saveFile = open(saveDir, 'wb')
        saveImage.save(saveFile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-c', '--compare', help='Compare only a single file', default='', required=False)
    parser.add_argument('-m', '--mutate', help='Comparison mutate count ', default=0, required=False)
    parser.add_argument('-r', '--resources', help='Resource directory name', default='resources', required=False)
    parser.add_argument('-s', '--save', help='Save solution image', default=False, required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    quit(main(args))
