#!/usr/bin/env python3
import os
import sys
import png
import glob
import copy
import random
import argparse
from multiprocessing import Process, Queue

MUTRATE = 8
ADDRATE = 6
GENRATE = 6
SIMRATE = 0.7
RECRATE = 40

class Coordinates:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def get(self):
        return self.x, self.y

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
        for i in range(splitLine + 1, self.dim):
            babyArray.append(partnerMap.bitmap[i])
        babyMap = PNGMap(self.name, babyArray)
        return babyMap
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
        elif mutationType < 8:
            moveDir = random.randrange(0, 4)
            noAdds = random.randrange(1, ADDRATE)
            for i in range(0, noAdds):
                if moveDir == 0:
                    self.bitmap.pop(0)
                    self.bitmap.append([self.white for i in range(0, self.dim)])
                elif moveDir == 1:
                    self.bitmap.pop(self.dim - 1)
                    bitmapClone = []
                    bitmapClone.append([self.white for i in range(0, self.dim)])
                    bitmapClone += self.bitmap
                    self.bitmap = bitmapClone
                elif moveDir == 2:
                    for row in self.bitmap:
                        row.pop(0)
                        row.append(self.white)
                elif moveDir == 3:
                    for row in self.bitmap:
                        row.pop(len(row) - 1)
                        row.insert(0, self.white)
        elif mutationType < 10:
            noAdds = random.randrange(1, ADDRATE)
            for row in self.bitmap:
                for i in range(0, len(row) - 1):
                    if row[i] != self.white:
                        if row[i + 1] == self.white:
                            row[i + 1] = row[i]
                            break
    def like(self, comparePNG):
        if self.size != comparePNG.size:
            return 0
        thisPNGLine = self.line()
        comparePNGLine = comparePNG.line()
        encounters = 0
        similarities = 0
        for i in range(0, len(thisPNGLine)):
            for ii in range(0, len(thisPNGLine) - i):
                if thisPNGLine[ii] != self.white:
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

def createGenerations(userMutations, resourceBitmap, finalMutation, bestMutation, recursionDepth = 0, bestMap = PNGMap('NA')):
    if not finalMutation.empty():
        return
    recursionDepth += 1
    for userChild in userMutations:
        #if resourceBitmap.like(userChild) > resourceBitmap.like(bestMap):
        if userChild.like(resourceBitmap) > bestMap.like(resourceBitmap) or resourceBitmap.like(userChild) > resourceBitmap.like(bestMap):
        #if userChild.like(resourceBitmap) > bestMap.like(resourceBitmap):
            bestMap = copy.deepcopy(userChild)
            bestMutation.put_nowait(bestMap)
        #if resourceBitmap.like(userChild) >= SIMRATE:
        if userChild.like(resourceBitmap) >= SIMRATE:
            finalMutation.put(resourceBitmap)
            finalMutation.put(userChild)
            print('Solution found at generation: %i' % recursionDepth)
            return
    if recursionDepth < RECRATE:
        parentsA, parentsB = genParents(userMutations, resourceBitmap)
        newChildren = []
        for i in range(0, len(parentsA)):
            newChild = copy.deepcopy(parentsA[i].breed(parentsB[i]))
            if random.randint(0, 10) % MUTRATE >= 1:
                newChild.mutate()
            newChildren.append(newChild)
        createGenerations(newChildren, resourceBitmap, finalMutation, bestMutation, recursionDepth, bestMap)
    else:
        return

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
        PNGBitmap = PNGMap(PNGFile[0], PNGArray)
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
    compareFile = args.compare
    resourceDir = args.resources
    mutateCount = int(args.mutate)
    print('Reading bitmap %s' % bitmapFile)
    bitmapArr = getPNGArray(bitmapFile)
    userMap = PNGMap('User', bitmapArr)
    if compareFile != '':
        compareArr = getPNGArray(compareFile)
        compareMap = PNGMap('Compare', compareArr)
        for i in range(0, mutateCount):
            userMap.mutate()
        print('User bitmap:')
        printPNGArray(userMap.bitmap)
        print('Compare bitmap:')
        printPNGArray(compareMap.bitmap)
        print('Similarity between %s and %s is:' % (userMap.name, compareMap.name))
        print(userMap.like(compareMap))
        return
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
    for resourceBitmap in resourcePNG:
        thread = Process(target=createGenerations , args=(userMutations, resourceBitmap, finalMutation, bestMutation))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join(1)
    if not finalMutation.empty():
        while not finalMutation.empty():
            resourceMap = finalMutation.get()
            print('The detected value is %s.' % resourceMap.name)
            valueMap = finalMutation.get()
            print('The final mutation is:')
            printPNGArray(valueMap.bitmap)
            print('Similarity:')
            print(valueMap.like(resourceMap))
            for thread in threads:
                thread.terminate()
        return 0
    elif not bestMutation.empty():
        bestList = []
        while not bestMutation.empty():
            nextBest = bestMutation.get()
            bestList.append(nextBest)
        allBest = bestList[0]
        resourceBest = resourcePNG[0]
        for resourceBitmap in resourcePNG:
            for bestBitmap in bestList:
                #if resourceBitmap.like(bestBitmap) > resourceBitmap.like(allBest):
                if bestBitmap.like(resourceBitmap) > allBest.like(resourceBitmap):
                    allBest = bestBitmap
                    resourceBest = resourceBitmap
        print('The closest detected value is %s.' % resourceBest.name)
        print('The final mutation is:')
        printPNGArray(allBest.bitmap)
        for thread in threads:
            thread.terminate()
        return 0
    else:
        print('No matches found.')
        return 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-c', '--compare', help='Compare only a single file', default='', required=False)
    parser.add_argument('-m', '--mutate', help='Comparison mutate count ', default=0, required=False)
    parser.add_argument('-r', '--resources', help='Resource directory name', default='resources', required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    quit(main(args))
