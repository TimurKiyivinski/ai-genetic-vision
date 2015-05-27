#!/usr/bin/env python3
import os
import sys
import png
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
RECRATE = 10

# Class to contain the X and Y coordinates
class Coordinates:
    '''
    Constructor

    x           Int:        X coordinate
    y           Int:        Y coordinate

    self.x      X coordinate
    self.y      Y coordinate
    '''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    '''
    Coordinates.get

    returns:    Int, Int
    '''
    def get(self):
        return self.x, self.y

# Main PNG Bitmap class, stores all the bitmaps
class PNGMap:
    '''
    Constructor
    
    PNGName     String:     Name of the PNG
    PNGArray    List:       2D list bitmap
    PNGWhite    Int:        Background colour bitmap

    self.name    Name of the bitmap
    self.bitmap  A 2D list containing the image as a bitmap
    self.white   The background colour of a bitmap
    self.dim     The bitmap dimension
    self.size    The bitmap area
    '''
    def __init__(self, PNGName, PNGArray = [[]], PNGWhite = 1):
        self.name = PNGName
        self.bitmap = PNGArray
        self.white = PNGWhite
        self.dim = len(PNGArray)
        self.size = len(PNGArray) * len(PNGArray[0])
    '''
    PNGMap.inverse

    Returns the inverse token of the token at a given location
    
    bit         Int:        Value of token to inverse

    returns:    Void
    '''
    def inverse(self, bit):
        if bit == self.white:
            return 0
        else:
            return self.white
    '''
    PNGMap.surrounded
    
    Checks if a given map coordinate is surrounded
    
    x           Int:        X coordinate
    y           Int:        Y coordinate

    returns:    Boolean
    '''
    def surrounded(self, x, y):
        # Check all borders of a token and see if they are
        # not a wall
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
        # A token is surrounded if there are 4 other tokens around it
        return sim == 4
    '''
    PNGMap.line

    Squashes the 2D bitmap into one line
    
    returns:    List
    '''
    def line(self):
        bitmapLine = []
        for row in self.bitmap:
            bitmapLine += row
        return bitmapLine
    '''
    PNGMap.breed

    Creates a hybrid of both PNGMaps

    partnerMap  PNGMap:     PNGMap to breed with

    returns:    PNGMap
    '''
    def breed(self, partnerMap):
        babyArray = []
        # Split the two bitmaps at a random location and combine them
        splitLine = random.randrange(1, self.dim)
        for i in range(0, splitLine):
            babyArray.append(self.bitmap[i])
        for i in range(splitLine, self.dim):
            babyArray.append(partnerMap.bitmap[i])
        babyMap = PNGMap(self.name, babyArray)
        return babyMap
    '''
    PNGMap.mutate

    Slightly mutates the image bitmap

    returns:    Void
    '''
    def mutate(self):
        # Select a mutation type, and run them based on their weight
        mutationType = random.randrange(0, 10)
        # This mutation adds random artifacts
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
        # This mutation stretches a bitmap
        elif mutationType > 8:
            noAdds = random.randrange(1, ADDRATE)
            for row in self.bitmap:
                for i in range(0, len(row) - 1):
                    if row[i] != self.white:
                        if row[i + 1] == self.white:
                            row[i + 1] = row[i]
                            break
    '''
    PNGMap.like

    Compares a PNGMap with another

    returns:    Float
    '''
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
    '''
    PNGMap.similar

    Compares a PNGMap with an entire list of PNGMaps

    returns:    Float
    '''
    def similar(self, comparePNGs):
        return sum(float(self.like(comparePNG)) for comparePNG in comparePNGs)
        
'''
randPair

Fitness Function: Gets a weighted random PNGMap based on it's similarity

PNGMaps         List:       List of maps to select from 
compareMaps     List:       List of maps to compare to
totalFitness    Int:        Maximum fitness value
threadQueue     Processor.Queue

returns:        PNGMap
'''
def randPair(PNGMaps, compareMaps, totalFitness, threadQueue):
    # Create an evenly distributed random number
    roulette = random.uniform(0, totalFitness)
    # Iterate list until a solution is found, by testing similarity
    # This helps to create a weighted random and eliminate less
    # fit parents
    for listMap in PNGMaps:
        roulette -= listMap.similar(compareMaps)
        if roulette <= 0:
            threadQueue.put(listMap)
            return
    # As a last resort, return a non weighted parent
    return PNGMaps[random.randrange(0, len(PNGMaps))]

'''
genPairs

Parent Selection Function: Creates a set of parents to breed

PNGMaps         List:       List of maps to select from
compareMaps     List:       List of maps to compare to

returns:        List, List
'''
def genPairs(PNGMaps, compareMaps):
    pairA = []
    pairB = []
    # Maximum possible fitness
    totalFitness = len(compareMaps)
    threadsA = []
    threadsB = []
    # Thread safe way to get parent PNGMaps
    queueA = Queue()
    queueB = Queue()
    # Create a list of threads to get a PNGMap
    for listMap in PNGMaps:
        threadA = Process(target=randPair , args=(PNGMaps, compareMaps, totalFitness, queueA))
        threadB = Process(target=randPair , args=(PNGMaps, compareMaps, totalFitness, queueB))
        threadA.start()
        threadB.start()
        threadsA.append(threadA)
        threadsB.append(threadB)
    # Get the parents from the queues
    while not len(pairA) == len(PNGMaps):
        pairA.append(queueA.get())
    while not len(pairB) == len(PNGMaps):
        pairB.append(queueB.get())
    # Join the threads with the current one
    for thread in threadsA:
        thread.join()
    for thread in threadsB:
        thread.join()
    # Return the pair of PNGMaps
    return pairA, pairB

'''
evolutionGen

Evolution Function: Manages the selection of the best outcome,
                    evolution of the next generation and mutations
                    of them

userMutations   List:       List of user PNGMap mutations
resourceBitmaps List:       List of resource PNGMaps
recursionDepth  Int:        Depth of recursive calls, number of generations
bestMap         PNGMap:     Copy of best PNGMap
resMap          PNGMap:     Copy of best resource PNGMap

returns:        PNGMap, PNGMap
'''
def evolutionGen(userMutations, resourceBitmaps, recursionDepth, bestMap, resMap = PNGMap('Default')):
    recursionDepth += 1
    print('Currently at generation: %i' % recursionDepth)
    # Iterate list of PNGMaps and set the best as the current detected solution
    for userChild in userMutations:
        finalRes = False
        for resourceBitmap in resourceBitmaps:
            if userChild.like(resourceBitmap) + resourceBitmap.like(userChild) > bestMap.like(resMap) + resMap.like(bestMap):
                bestMap = copy.deepcopy(userChild)
                resMap = resourceBitmap
    print('Current comparison is: %f' % bestMap.like(resMap))
    # Return the best if their similarity is past the SIMRATE
    if bestMap.like(resMap) >= SIMRATE:
        return bestMap, resMap
    # Recursively call this function until RECRATE is reached
    if recursionDepth < RECRATE:
        # Create pairs of parents based on their fitness
        parentsA, parentsB = genPairs(userMutations, resourceBitmaps)
        # Iterate the parents and create children by breeding them
        newChildren = []
        for i in range(0, len(parentsA)):
            newChild = copy.deepcopy(parentsA[i].breed(parentsB[i]))
            # Mutate a few children, in hope that X-Men as awesome as
            # Wolverine and Rogue may be created. 
            if random.randint(0, 10) % MUTRATE >= 1:
                newChild.mutate()
            newChildren.append(newChild)
        # Recusively call this function with the new set of children, by returning it
        return evolutionGen(newChildren, resourceBitmaps, recursionDepth, bestMap, resMap)
    else:
        # As a last resort, return the best solutions detected until now
        print('Evolution ended at generation: %i' % recursionDepth)
        return bestMap, resMap

'''
getPNGArray

Creates a 2D bitmap from an image file

bitmapFile      String:     Path to iamge file

returns:        List
'''
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

'''
getPNGResource

Loads all the resources from the resource directory

resourceDir     String:     Directory to laod comparison bitmaps

returns:        List
'''
def getPNGResource(resourceDir):
    PNGList = []
    resourceList = os.listdir(resourceDir)
    for PNGFile in resourceList:
        PNGArray = getPNGArray(os.path.join(resourceDir, PNGFile))
        PNGBitmap = PNGMap(PNGFile, PNGArray)
        PNGList.append(PNGBitmap)
    return PNGList

'''
printPNGArray

Prints the entire bitmap

returns:        Void
'''
def printPNGArray(bitmapArr):
    for row in bitmapArr:
        for bit in row:
            sys.stdout.write(str(bit))
        print('')

# Main function
def main(args):
    # Read the command line arguments and set default values
    setVerbose = args.verbose
    bitmapFile = args.file
    compareFile = args.compare
    resourceDir = args.resources
    saveDir = args.save
    mutateCount = int(args.mutate)
    print('Reading bitmap %s' % bitmapFile)
    # Load the user bitmap
    bitmapArr = getPNGArray(bitmapFile)
    # Create a user PNGMap
    userMap = PNGMap('User', bitmapArr)
    
    # Compare Operation
    if compareFile != '':
        compareArr = getPNGArray(compareFile)
        compareMap = PNGMap('Compare', compareArr)
        # Optionally create user mutations
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
    # Create a list of user mutations
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
    print('Initial similarity is: %f' % userMap.similar(resourcePNG))
    # Get the final user mutation and detected value
    finalUser, finalResource = evolutionGen(userMutations, resourcePNG, 0, userMap)
    # Results
    print('The detected value is: %s' % finalResource.name)
    print('Final similarity is: %f' % finalUser.similar(resourcePNG))
    print('Initial comparison is: %f' % userMap.like(finalResource))
    print('Final comparison is: %f' % finalUser.like(finalResource))
    if setVerbose:
        printPNGArray(finalUser.bitmap)
    # Optionally save the last user mutation into a bitmap
    if saveDir != False:
        saveImage = png.from_array(finalUser.bitmap, 'L;1')
        saveFile = open(saveDir, 'wb')
        saveImage.save(saveFile)

# Run main if not loaded as a module
if __name__ == '__main__':
    # Create a parser to handle command line arguments
    parser = argparse.ArgumentParser(description='Converts a numerical bitmap into text.')
    parser.add_argument('-f', '--file', help='Bitmap file name', required=True)
    parser.add_argument('-c', '--compare', help='Compare only a single file', default='', required=False)
    parser.add_argument('-m', '--mutate', help='Comparison mutate count ', default=0, required=False)
    parser.add_argument('-r', '--resources', help='Resource directory name', default='resources', required=False)
    parser.add_argument('-s', '--save', help='Save solution image', default=False, required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', action='store_true')
    args = parser.parse_args()
    # Call the main
    quit(main(args))
