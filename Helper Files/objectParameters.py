"""
This simulation has been adapted from https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-00sc-introduction-to-computer-science-and-programming-spring-2011/unit-2/lecture-14-sampling-and-monte-carlo-simulation/
"""

# Import Basic Modules
import sys
import math
import pylab
import random
import numpy as np
# Import Code to Simulate/Visualize the Boat's Movement
import simulateBoat
# Interpolation
from scipy import interpolate
from scipy.interpolate import LinearNDInterpolator
# Plotting
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import matplotlib.patheffects as pe
# Import Python Helper Files (And Their Location)
sys.path.append('./Helper Files/simulatedSource/')  # Folder with All the Helper Files
sys.path.append('./simulatedSource/')  # Folder with All the Helper Files
import extractSimulatedData

# --------------------------------------------------------------------------- #
#                            Basic Object Classes                             #
# --------------------------------------------------------------------------- #
class Position(object):
    """
    A Position represents a location in a two-dimensional tank.
    """
    def __init__(self, x, y):
        """
        Initializes a position with coordinates (x, y).
        """
        self.x = x
        self.y = y
        
    def getX(self):
        return self.x
    
    def getY(self):
        return self.y
    
    def getNewPosition(self, angle, boatSpeed):
        """
        Computes and returns the new Position after a single clock-tick has
        passed, with this object as the current position, and with the
        specified angle and speed.

        Does NOT test whether the returned position fits inside the tank.

        angle: float representing angle in degrees, 0 <= angle < 360
        boatSpeed: positive float representing boatSpeed

        Returns: a Position object representing the new position.
        """
        old_x, old_y = self.getX(), self.getY()
        # Compute the change in position
        delta_y = boatSpeed * math.sin(math.radians(angle))
        delta_x = boatSpeed * math.cos(math.radians(angle))
        # Add that to the existing position
        new_x = old_x + delta_x
        new_y = old_y + delta_y
        return Position(new_x, new_y)

    def __str__(self):  
        return "(%0.2f, %0.2f)" % (self.x, self.y)

class boatCollection(object):
    """
    A boatCollection represents a collection of boats inside the tank. It supports
    two operations:

    * You can add a boat to the collection with the add method.

    * You can iterate over the boats in the collection with
      "for boat in rc:". The iteration order is unspecified.
    """
    def __init__(self):
        """
        Initializes a boatCollection. The collection is initially empty.
        """
        self.boats = []
        
    def add(self, boat):
        """
        Add boat to the collection.

        boat: a boat object.
        """
        self.boats.append(boat)
        
    def __iter__(self):
        """
        Return an iterator over the boats in the collection.
        """
        return iter(self.boats)


class rectangularTank(object):
    """
    A rectangularTank represents a rectangular region containing water nodes (tiles)

    A tank has a tankWidth and a tankHeight and contains (tankWidth * tankHeight) tiles. At any
    particular time, each of these tiles are either visited or not visited
    """
    def __init__(self, tankWidth, tankHeight):
        """
        Initializes a rectangular tank with the specified tankWidth and tankHeight.

        Initially, no tiles in the tank have been visited.

        tankWidth: an integer > 0
        tankHeight: an integer > 0
        """
        # Define Basic Parameters
        self.tankWidth = int(tankWidth)
        self.tankHeight = int(tankHeight)
        self.tiles = {}
        
        # Initialize the Board
        self.initializeBoard()
    
    def initializeBoard(self):
        for x in range(self.tankWidth):
            for y in range(self.tankHeight):
                self.tiles[(x, y)] = False
            
    def markAsVisited(self, pos):
        """
        Mark the tile under the position POS as visited.
        Assumes that POS represents a valid position inside this tank.

        pos: a Position object
        """
        x = math.floor(pos.getX())
        y = math.floor(pos.getY())
        self.tiles[(x, y)] = True
        
    def hasVisited(self, m, n):
        """
        Return True if the tile (m, n) has been visited.
        Assumes that (m, n) represents a valid tile inside the tank.

        m: an integer
        n: an integer
        returns: True if (m, n) was visited, False otherwise
        """
        return self.tiles[(m, n)]
    
    def getNumTiles(self):
        """
        Return the total number of tiles in the tank.

        returns: an integer
        """
        return self.tankWidth * self.tankHeight
    
    def getNumVisitedTiles(self):
        """
        Return the total number of visited tiles in the tank.

        returns: an integer
        """
        return sum(self.tiles.values())
    
    def getRandomPosition(self):
        """
        Return a random position inside the tank.

        returns: a Position object.
        """
        return Position(random.random() * self.tankWidth,
                        random.random() * self.tankHeight)
    
    def isPositionIntank(self, pos, tankBuffer):
        """
        Return True if pos is inside the tank.

        pos: a Position object.
        returns: True if pos is in the tank, False otherwise.
        """
        return ((tankBuffer <= pos.getX() < self.tankWidth - tankBuffer)
                and (tankBuffer <= pos.getY() < self.tankHeight - tankBuffer))


class cosmolSimTank(rectangularTank):
        
    def __init__(self, sourceLocations, tankWidth, tankHeight, simFile):
        super().__init__(tankWidth, tankHeight)  # Get Variables Inherited from the helper_Files Class
        
        self.mapedTiles = {}        
        self.getSimData(simFile, tankWidth, tankHeight)
        
        # Initialize the Board
        self.plotSimData()
    
    def dataRound(self, array):
        return np.round(array, 5)
        
    def getSimData(self, simFile, tankWidth, tankHeight):
        # Extract the Data from the Excel File
        self.simX, self.simY, self.simZ = extractSimulatedData.processData().getData(simFile)
        # Shift to Start at Zero,Zero
        self.simX -= min(self.simX)
        self.simY -= min(self.simY)
        self.simZ = abs(self.simZ)
        # Reduce X,Y to Gameboard Positions
        self.simX = self.simX*tankWidth/max(self.simX)
        self.simY = self.simY*tankHeight/max(self.simY)
        # Round X,Y so its Discrete and Comparable
        self.simX = self.dataRound(self.simX)
        self.simY = self.dataRound(self.simY)
        # Find the Single Source Input
        maxIndex = np.argmax(self.simZ)
        self.sourceLocations = [(np.round(self.simX[maxIndex]), np.round(self.simY[maxIndex]))]
        # Interpolate the Space
        self.interp = LinearNDInterpolator(list(zip(self.simX, self.simY)), self.simZ)
                
        # Store Data in Mapped Tiles Data Structure
        positions = list(zip(self.simX, self.simY))
        self.mapedTiles = dict(zip(positions, self.simZ))
        
        # Reinitialize Tiles
        self.initializeBoard()
        #self.tiles = dict(zip(positions, len(self.simZ)*[False]))
        self.tiles[self.sourceLocations[0]] == True
    
    def plotSimData(self):  
        # Plot Model
        fig = plt.figure()
        ax = axes3d.Axes3D(fig)
        ax.scatter(self.simX, self.simY, self.simZ, c=self.simZ)
        plt.show()
    
    def posReading(self, currentPos, sensorType = ""):
        return max(0, self.interp(currentPos))
        #return max(0,interpolate.griddata((self.simX, self.simY), self.simZ, currentPos, method='linear'))

    def euclideanDist(self, P1, P2):
        return np.linalg.norm((P1[0]-P2[0], P1[1]-P2[1]))
    
    def sourceFound(self):
        for sourceLocation in self.sourceLocations:
            if self.tiles[sourceLocation] == True:
                return True
        return False
    
    def find2DSimMap(self, xVec, yVec):
        zData = []; xData = []; yData = []
        for x in xVec:
            for y in yVec:
                zData.append(float(self.posReading((x,y))))
                xData.append(x)
                yData.append(y)
        return xData, yData, zData

class diffusionModelTank(rectangularTank):
    
    def __init__(self, sourceLocations, tankWidth, tankHeight):
        super().__init__(tankWidth, tankHeight)  # Get Variables Inherited from the helper_Files Class
        
        self.mapedTiles = {}
        self.sourceLocations = sourceLocations
        self.scaleTiles = 10
        
        #self.diffuseSources()
    
    def initializeMap(self):
        for x in range(self.tankWidth*self.scaleTiles):
            x = x/self.scaleTiles
            for y in range(self.tankHeight*self.scaleTiles):
                y = y/self.scaleTiles
                self.mapedTiles[(x, y)] = 0
    
    def diffuseModel(self, delX, delY):
        return math.exp(-(delY**2 + delX**2)/2)
    
    def diffuseSources(self):
        self.initializeMap()
        
        for sourceLocation in self.sourceLocations:
            xSource = sourceLocation[0]
            ySource = sourceLocation[1]
            for x in range(self.tankWidth):
                delX = x - xSource
                for y in range(self.tankHeight):
                    delY = y - ySource
                    
                    self.mapedTiles[(x, y)] += self.diffuseModel(delX, delY)
    
    def plotDiffuseModel(self):
        # Unpack Tuples
        xy, z = zip(*self.mapedTiles)
        x,y = zip(*xy)
        
        # Plot Model
        fig = plt.figure()
        ax = axes3d.Axes3D(fig)
        ax.scatter(x,y,z,c=z)
    
    def posReading(self, currentPos, sensorType = ""):
        # Loop Through Each Source to Find its Contribution
        sensorReading = 0
        for sourceLocation in self.sourceLocations:
            xSource = sourceLocation[0]
            ySource = sourceLocation[1]
            
            delX = currentPos[0] - xSource
            delY = currentPos[1] - ySource
                    
            sensorReading += self.diffuseModel(delX, delY)
        
        return sensorReading
    
    def sourceFound(self):
        for sourceLocation in self.sourceLocations:
            if self.tiles[sourceLocation] == True:
                return True
        return False
    
class userInputModel(rectangularTank):
    
    def __init__(self, sourceLocations, tankWidth, tankHeight):
        super().__init__(tankWidth, tankHeight)  # Get Variables Inherited from the helper_Files Class
        
        self.mapedTiles = {}
        self.sourceLocations = sourceLocations
    
    def posReading(self, currentPos, sensorType = "Sensor"):
        return float(input("Enter " + sensorType + " Reading: "))
            
    def sourceFound(self):
        return bool(int(input("End the Simulation (Yes = 1; No = 0): ")))

class Boat(object):
    """
    Represents a boat finding the source

    At all times the boat has a particular position and direction in the tank.
    The boat also has a fixed speed.

    Subclasses of boat should provide movement strategies by implementing
    updatePosition(), which simulates a single time-step.
    """
    def __init__(self, tank, boatSpeed, boatLocation = Position(0,0)):
        """
        Initializes a boat with the given speed in the specified tank. The
        boat initially has a random direction and a random position in the
        tank. 

        tank:  a rectangularTank object.
        boatSpeed: a float (boatSpeed > 0)
        """
        # Initialize Boat Parameters
        self.boatSpeed = boatSpeed
        self.boatAngle = 90
        self.position = Position(boatLocation[0], boatLocation[1])
        self.boatDirection = np.array([0,1])
        
        # Initialize Place in Tank
        self.tank = tank
        self.tank.markAsVisited(self.position)
        
        # Initialize Sensor Parameters
        self.sensorAngle = 30;
        self.sensorDistance = 1.25;
        
        # Keep Track of Past Movements
        self.pastValues = {}
        
    def getBoatPosition(self):
        """
        Return the position of the boat.

        returns: a Position object giving the boat's position.
        """
        return self.position
    
    def getBoatAngle(self):
        """
        Return the direction of the boat.

        returns: an integer d giving the direction of the boat as an angle in
        degrees, 0 <= d < 360.
        """
        return self.boatAngle
    
    def setBoatPosition(self, position):
        """
        Set the position of the boat to POSITION.

        position: a Position object.
        """
        self.position = position
        
    def setBoatAngle(self, direction):
        """
        Set the direction of the boat to DIRECTION.

        direction: integer representing an angle in degrees
        """
        self.boatAngle = direction
        
    def setBoatDirectionVector(self, directionVec):
        """
        Set the direction of the boat to DIRECTION.

        direction: a Vector
        """
        self.boatDirection = directionVec
    
    def updatePastRecord(self, currentPosObj, currentVal):
        # Get the Current Position (Rounded to Current Square)
        x = math.floor(currentPosObj.getX())
        y = math.floor(currentPosObj.getY())
        currentPos = (x,y)
        # Get Previous Past Values at the Position
        pastVals = self.pastValues.get(currentPos, [])
        # Add the New Position's Value
        pastVals.append(currentVal)
        # Store the New Value in the Dictionary if No Position was There
        if len(pastVals) == 1:
            self.pastValues[currentPos] = pastVals
    
    def getSensorsPos(self, currentPosObj):
        # Get the Current Position
        x = currentPosObj.getX()
        y = currentPosObj.getY()
        # Find Location of the Front Sensor
        sensorFrontX = x;
        sensorFrontY = y + self.sensorDistance
        # Find the Location of the Left Sensor
        sensorLeftX = x + self.sensorDistance*math.cos(math.radians(180 + self.sensorAngle)); 
        sensorLeftY = y + self.sensorDistance*math.sin(math.radians(180 + self.sensorAngle)); 
        # Find the Location of the Right Sensor
        sensorRightX = x + self.sensorDistance*math.cos(math.radians(-self.sensorAngle)); 
        sensorRightY = y + self.sensorDistance*math.sin(math.radians(-self.sensorAngle)); 
        # Return the Three Sensor Positions
        return (sensorFrontX, sensorFrontY), (sensorLeftX, sensorLeftY), (sensorRightX, sensorRightY)
    
    def roundValues(self, array, toDigit = 60):
        return np.round(array, toDigit)
    
    def getAngle(self, newDirection, referenceDirection = [1,0]):
        # Find Angle Between Reference
        unitVectorDirection = newDirection/np.linalg.norm(newDirection)
        dot_product = np.dot(unitVectorDirection, referenceDirection)
        newAngle = np.degrees(np.arccos(dot_product))
        # Correction Factor to Angle as Cosine Repeats Values
        needCorrection = newDirection[1] < 0
        if needCorrection:
            newAngle = 360 - newAngle
        # Return the New Angle
        return newAngle
    
    def getDirection(self, angle):
        newDirection = [math.cos(math.radians(angle)), math.sin(math.radians(angle))]
        return self.roundValues(newDirection)
    
    def getSensorPoints(self):
        # Find the Location of Each of the Three Sensors
        frontSensorPos, leftSensorPos, rightSensorPos = self.getSensorsPos(self.position)
        # Find the Interpolated Values at the Sensor's Position
        frontSensorVal = self.tank.posReading(frontSensorPos, sensorType = "Front Sensor")
        leftSensorPosVal = self.tank.posReading(leftSensorPos, sensorType = "Left Sensor")
        rightSensorPosVal = self.tank.posReading(rightSensorPos, sensorType = "Right Sensor")
        # Define Each Sensor in 3D Space
        frontPoint = np.array([frontSensorPos[0], frontSensorPos[1], frontSensorVal])
        leftPoint = np.array([leftSensorPos[0], leftSensorPos[1], leftSensorPosVal])
        rightPoint = np.array([rightSensorPos[0], rightSensorPos[1], rightSensorPosVal])
        # Return Points
        return frontPoint, leftPoint, rightPoint

    def updateBoat(self, newDirection, printMovement = False):
        # Find the Angle
        newAngle = self.getAngle(newDirection)
        
        # Check to See if the Position is in the Tank
        candidatePosition = self.position.getNewPosition(newAngle, self.boatSpeed)
        while not self.tank.isPositionIntank(candidatePosition, self.sensorDistance):
            # If The Position is Not in the Tank, Bound the Position by the Tank
            boundaryVals = [self.tank.tankWidth, self.tank.tankHeight]
            potentialVals = [candidatePosition.getX(), candidatePosition.getY()]
            potentialPos = []
            for axisPos in range(len(newDirection)):
                potentialPos.append(max(self.sensorDistance, min(potentialVals[axisPos], boundaryVals[axisPos]-self.sensorDistance)))
            # If Going Outside of Tank, Turn Around
            if potentialPos[0] == potentialPos[1] == 0 or (candidatePosition.getX() == potentialPos[0] and candidatePosition.getY() == potentialPos[1]):
                newAngle = random.randrange(360)
                candidatePosition = self.position.getNewPosition(newAngle, self.boatSpeed)
            else:
                # Retrieve the New Position Object
                candidatePosition = Position(potentialPos[0], potentialPos[1])
                # Retrive New Direction and Angle
                newDirection = [candidatePosition.getX() - self.position.getX(), candidatePosition.getY() - self.position.getY()]
                newAngle = self.getAngle(newDirection)
        
        # Print Movement Results to the User
        if printMovement:
            moveDistance = self.boatSpeed*np.linalg.norm(newDirection)
            print("New Direction:", newDirection*self.boatSpeed)
            print("Distance:", moveDistance)
            print("Angle from (1,0):", newAngle)
            # Find Turn Parameters
            if np.round(newDirection[0], 10) == np.round(self.boatDirection[0], 10) and np.round(newDirection[1], 10) == np.round(self.boatDirection[1], 10):
                print("Go Straight")
            else:
                if self.boatDirection[0] != 0:
                    xCenter, yCenter, turnRadius = self.findMovementCircle(self.position.getX(), self.position.getY(), candidatePosition.getX(), candidatePosition.getY(), self.boatDirection[1]/self.boatDirection[0])
                    turnAngle = self.findAngle(turnRadius, moveDistance)
                else:
                    turnRadius = self.findRadius(moveDistance, self.position.getX() - candidatePosition.getX())
                    turnAngle = self.findAngle(turnRadius, moveDistance)
                    yCenter = self.position.getY()
                    xCenter = self.position.getX() + turnRadius*newDirection[0]/abs(newDirection[0])
                print("Turn Radius:", turnRadius)
                print("Angle Between Points in Circle:", turnAngle)
                self.plotResult(newDirection, self.position, candidatePosition, xCenter, yCenter, turnRadius)
                print("")
        
        # Move to the Position
        self.setBoatAngle(newAngle)
        self.setBoatPosition(candidatePosition)
        self.tank.markAsVisited(self.position)
        self.setBoatDirectionVector(newDirection)
    
    def findRadius(self, distance, delX):
        return distance*distance/(2*abs(delX))
    
    def findAngle(self, turnRadius, chordDist):
        sinAngle = chordDist/(2*turnRadius)
        return 2*np.degrees(np.arcsin(sinAngle))
    
    def findMovementCircle(self, x1, y1, x2, y2, dRatio):
        # Find Circle Center
        if y1 == y2:
            centerX = (x2+x1)/2
            centerY = (y1-y2)**2
        else:
            centerY = (2*dRatio*y1*(x2-x1) - (x1-x2)**2 - y2**2 + y1**2) / (2*(y1-y2 + dRatio*(x2-x1)))
            centerX = dRatio*(y1-centerY) + x1
        # Find Circle Radius
        radius = math.sqrt((x1-centerX)**2 + (y1-centerY)**2)
        # Return Circle Parameters
        return centerX, centerY, radius
    

# --------------------------------------------------------------------------- #
#                  Movement Strategies: Search Algorythms                     #
# --------------------------------------------------------------------------- #

class standardBoat(Boat):
    """
    A Standardboat is a boat with the standard movement strategy.

    At each time-step, a Standardboat attempts to move in its current direction; when
    it hits a wall, it chooses a new direction randomly.
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
    def updatePosition(self):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        candidatePosition = self.position.getNewPosition(self.boatAngle, self.boatSpeed)
        if self.tank.isPositionIntank(candidatePosition, self.sensorDistance):
            self.setBoatPosition(candidatePosition)
            self.tank.markAsVisited(self.position)
        else:
            self.boatAngle = random.randrange(360)
            self.boatDirection = self.getDirection(self.boatAngle)
            
            
class randomBoat(Boat):
    """
    A randomBoat is a boat with the random movement strategy.

    At each time-step, a randomBoat picks a direction and angle and moves there
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
    def updatePosition(self):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        # Get the Current Position
        currentPosition = self.getBoatPosition()
        # Randomly Select a New Angle/Direction
        newAngle = random.randrange(360)
        # Get New Position that is Inside the Tank
        new_pos = currentPosition.getNewPosition(newAngle, self.boatSpeed)
        while not self.tank.isPositionIntank(new_pos, self.sensorDistance):
            # If Not in Tank, Randonly Select New Angle Again
            newAngle = random.randrange(360)
            new_pos = currentPosition.getNewPosition(newAngle, self.boatSpeed)
        # Update the Boat Parameters
        self.setBoatPosition(new_pos)
        self.tank.markAsVisited(new_pos)
        self.setBoatAngle(newAngle)
        self.boatDirection = self.getDirection(self.boatAngle)

class AStar(Boat):
    """
    Move to the Highest Gradient
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
        # Hold Past Three Values
        self.recentVals = []    # List of Tuple of Recent Values
        self.numHold = 5        # Number of Past Values to Hold
        # Heursitci Information
        self.heuristicRadius = min(abs(self.sensorDistance*math.cos(math.radians(-self.sensorAngle))), abs(self.sensorDistance*math.sin(math.radians(-self.sensorAngle))))
        # Plotting Parameters
        self.ax = None
        
        
    def boatStuck(self, numConsider = 5, numSensors = 3):
        """
        If the boat keeps going back and forwards to same spot, return True
        """
        # Seperate X,Y,Z Sensor Data from the Recent Readings
        prevX, prevY, prevZ = self.getPastVals()
        if len(prevX) >= numSensors*numConsider:
            # Take Last numConsider Samples of First Sensor
            prevX = prevX[-numSensors*numConsider:len(prevX)][0::numSensors];
            prevY = prevY[-numSensors*numConsider:len(prevY)][0::numSensors];
            # Round Data
            prevX = np.round(prevX, 2); prevY = np.round(prevY, 2);
            # Check to See if the boat keeps returning to its old position
            for pointNum in range(2,len(prevX),2):
                if prevX[0] != prevX[pointNum] and prevY[0] != prevY[pointNum]:
                    return False
            return True
        else:
            return False
        
    def updatePastVals(self, threeSensorPoints):
        # Store Each Sensor's Value at the Current Position
        self.recentVals.append(threeSensorPoints)
        # Only Record the Last 'numHold' Positions
        if len(self.recentVals) > self.numHold:
            self.recentVals.pop(0)
    
    def getPastVals(self):
        # Seperate X,Y,Z Sensor Data from the Recent Readings
        prevX = []; prevY = []; prevZ = []
        for prevReading in self.recentVals:
            for prevPoint in prevReading:
                prevX.append(prevPoint[0])
                prevY.append(prevPoint[1])
                prevZ.append(prevPoint[2])
        return prevX, prevY, prevZ
            
    def getHeuristic(self, currentPos, plotDecisions = False):
        # Seperate X,Y,Z Sensor Data from the Recent Readings
        prevX, prevY, prevZ = self.getPastVals()
        # Interpolate the Space with the Recent Readings
        xSamples, ySamples = self.PointsInCircum(currentPos.getX(), currentPos.getY(), self.heuristicRadius)
        zSamples = self.roundValues(interpolate.griddata((prevX, prevY), prevZ, (xSamples, ySamples), method='linear'))
        
        # If No Heuristic Gradient, Keep Going Straight
        allSame = all(round(zVal,5) == round(zSamples[0],5) for zVal in zSamples)
        if allSame:
            newDirection = self.boatDirection#*self.heuristicRadius
        # Else, Find the Heuristic Direction
        else:
            # Find Max Point on the Circle
            directionIndex = np.argmax(zSamples)
            # Find the New Direction
            newDirection = np.array([xSamples[directionIndex] - currentPos.getX(), ySamples[directionIndex] - currentPos.getY()])
        # Plot the Results
        if plotDecisions:
            self.ax = self.plotHeurisitic(xSamples, ySamples, zSamples, currentPos, newDirection)
        return newDirection/np.linalg.norm(newDirection)
        
    
    def updatePosition(self, applyHeuristic = True, plotDecisions = False, printMovement = False, findTangetPlane = False):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        # Find the Current Sensor Locations/Values
        frontPoint, leftPoint, rightPoint = self.getSensorPoints()
        
        # If Apply A Star Heuristic
        if applyHeuristic:
            # Keep Track of Previous Results
            self.updatePastVals((frontPoint, leftPoint, rightPoint))
            # Find Heursitic Guess Direction
            guessDirection = self.getHeuristic(self.position, plotDecisions)
                
        # Find the Normal Vector to the 3-Point Plane
        normVector = np.cross(frontPoint - leftPoint, rightPoint - leftPoint)
        # Scale the Normal Vector to the Gradients Direction
        gradientVector = self.roundValues(normVector*(2*(normVector[2] < 0) - 1))
        
        if np.linalg.norm(gradientVector[0:2]) != 0:
            # Make Tangent Plane
            if findTangetPlane:
                d = np.dot(gradientVector, frontPoint)
                gradSensorPlane = -gradientVector/d
                print('The equation is {0}x + {1}y + {2}z = {3}'.format(gradSensorPlane[0], gradSensorPlane[1], gradSensorPlane[2], -1))
            
            # Get the Direction of Max Increase
            newDirection = gradientVector[0:2]
            newDirection = newDirection/np.linalg.norm(newDirection)
            # Apply Heuristic
            if applyHeuristic:
                newDirection = newDirection + guessDirection
                newDirection = newDirection/np.linalg.norm(newDirection)

        elif applyHeuristic and np.linalg.norm(guessDirection) != 0:
            print("The Gradient is Zero; Using the Heuristic")
            newDirection = guessDirection
        elif applyHeuristic:
            print("The Reading is Not Significant; Going in Max Weighted Direction")
            newDirection = [0,0]; currentPos = [self.position.getX(), self.position.getY()]
            for point in [frontPoint, leftPoint, rightPoint]:
                newDirection += (point[0:2] - currentPos)*point[-1]
            if np.linalg.norm(newDirection) != 0:
                newDirection = newDirection/np.linalg.norm(newDirection)
            else:
                newDirection = self.boatDirection
        else:
            newDirection = self.boatDirection
            
        # Check to See if You Are Stuck: Switching Back and Forwards
        if self.boatStuck():
            newDirection = self.getDirection(random.randrange(360))
        
        if plotDecisions:
            try:
                self.plotDecision(self.position, self.heuristicRadius*gradientVector[0:2]/np.linalg.norm(gradientVector[0:2]),  newDirection*self.heuristicRadius, self.ax)
            except:
                print("Cant Plot Decision")
        
        # Update Boat
        self.updateBoat(newDirection, printMovement)
    
    def PointsInCircum(self, startX, startY, circleRadius, n = 1000):
        # Find Largest Radius to Extrapolate
        x = []; y = []
        for i in range(0,n+1):
            x.append(startX + math.cos(2*math.pi/n*i)*circleRadius)
            y.append(startY + math.sin(2*math.pi/n*i)*circleRadius)
        return x,y
    
    def plotHeurisitic(self, x, y, z, currentPos, newDirection, figBuffer = 0.5):
        fig = plt.figure()
        ax = fig.add_subplot();
        # Plot Data
        ax.scatter(currentPos.getX(), currentPos.getY(), c = 'black')
        cm = ax.scatter(x, y, c = z)
        plt.arrow(currentPos.getX(), currentPos.getY(), newDirection[0], newDirection[1] , width=0.02, color="red")
        # Set Figure Limits
        ax.set_xlim(min(x) - figBuffer, max(x) + figBuffer)
        ax.set_ylim(min(y) - figBuffer, max(y) + figBuffer)
        # Set Figure Information
        ax.set_xlabel("X-Axis")
        ax.set_ylabel("Y-Axis")
        ax.set_title("Heuristic Map")
        # Add Colormap
        fig.colorbar(cm)
        return ax

    def plotDecision(self, currentPos, gradVec,  newDirection, ax = None):
        if ax == None:
            fig = plt.figure()
            ax = fig.add_subplot();
        # Plot Data
        plt.arrow(currentPos.getX(), currentPos.getY(), gradVec[0], gradVec[1] , width=0.02, color="black")
        plt.arrow(currentPos.getX(), currentPos.getY(), newDirection[0], newDirection[1] , width=0.02, color="green")
        # Set Figure Information
        ax.set_xlabel("X-Axis")
        ax.set_ylabel("Y-Axis")
        ax.set_title("Movement Decision Map")
        # Show Figure
        plt.show()
        # Clean Up
        self.ax = None
    
    def plotResult(self, newDirection, currentPos, finalPos, xCenter, yCenter, turnRadius, figBuffer = 1):
        fig = plt.figure()
        ax = fig.add_subplot();
        # Plot Future Movement
        plt.arrow(currentPos.getX(), currentPos.getY(), finalPos.getX() - currentPos.getX(), finalPos.getY() - currentPos.getY(), width=0.01, color="black")
        ax.scatter(currentPos.getX(), currentPos.getY(), c = 'green', s=30)
        ax.scatter(finalPos.getX(), finalPos.getY(), c = 'red',  s=30)
        # Plot Turning Information
        ax.scatter(xCenter, yCenter, c = 'black')
        circleX, circleY = self.PointsInCircum(xCenter, yCenter, turnRadius)
        ax.scatter(circleX, circleY, s=5)
        # Set Figure Information
        ax.set_xlabel("X-Axis")
        ax.set_ylabel("Y-Axis")
        ax.set_title("Movement Map")
        # Set Figure Aesthetics
        ax.set_xlim(min(circleX) - figBuffer, max(circleX) + figBuffer)
        ax.set_ylim(min(circleY) - figBuffer, max(circleY) + figBuffer)
        # Show Figure
        plt.show()
    

class gradientDescent(Boat):
    """
    Move to the Highest Gradient
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
        self.ParentClass = AStar(tank, boatSpeed, boatLocations)
        
    def updatePosition(self, applyHeuristic = False, plotDecisions = True, printMovement = False, findTangetPlane = False):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        self.ParentClass.updatePosition(applyHeuristic = False, plotDecisions = False, printMovement = False, findTangetPlane = False)
        
        # Move to the Position
        self.setBoatAngle(self.ParentClass.boatAngle)
        self.setBoatPosition(self.ParentClass.position)
        self.tank.markAsVisited(self.position)
        self.setBoatDirectionVector(self.ParentClass.boatDirection)
        
class maxDirection(Boat):
    """
    Move to the Highest Gradient
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
        
    def updatePosition(self, applyHeuristic = False, plotDecisions = True, printMovement = False, findTangetPlane = False):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        # Find Your Current Location Information
        frontPoint, leftPoint, rightPoint = self.getSensorPoints()

        # Find Max Direction
        allPoints = np.round([frontPoint, leftPoint, rightPoint], 10)
        newPosition = max(allPoints, key=lambda x:x[-1])[0:2]
        newDirection = newPosition - [self.position.getX(), self.position.getY()]
        if np.linalg.norm(newDirection) != 0:
            newDirection = newDirection/np.linalg.norm(newDirection)
        else:
            newDirection = self.boatDirection
        
        # Update Boat
        self.updateBoat(newDirection)

class weightedMaxDirection(Boat):
        
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
        
    def updatePosition(self, applyHeuristic = False, plotDecisions = True, printMovement = False, findTangetPlane = False):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        # Find Your Current Location Information
        frontPoint, leftPoint, rightPoint = self.getSensorPoints()
        
        # ----------- Algorythm -------- #
        # Find Weighted Max Direction
        newDirection = [0,0]; currentPos = [self.position.getX(), self.position.getY()]
        for point in [frontPoint, leftPoint, rightPoint]:
            newDirection += (point[0:2] - currentPos)*point[-1]
        if np.linalg.norm(newDirection) != 0:
            newDirection = newDirection/np.linalg.norm(newDirection)
        else:
            newDirection = self.boatDirection
        # ------------------------------ #
        
        # Update Boat
        self.updateBoat(newDirection)
        
        
class pureHeuristic(AStar):
    """
    Move to the Highest Gradient
    """
    
    def __init__(self, tank, boatSpeed, boatLocations):
        super().__init__(tank, boatSpeed, boatLocations)
        
        # Hold Past Three Values
        self.recentVals = []    # List of Tuple of Recent Values
        self.numHold = 3        # Number of Past Values to Hold
        # Heursitci Information
        self.heuristicRadius = min(abs(self.sensorDistance*math.cos(math.radians(-self.sensorAngle))), abs(self.sensorDistance*math.sin(math.radians(-self.sensorAngle))))
        
    def updatePosition(self, applyHeuristic = True, plotDecisions = False, printMovement = False, findTangetPlane = False):
        """
        Simulate the passage of a single time-step.

        Move the boat to a new position and mark the tile it is on as having
        been Visited.
        """
        # Find Your Current Location Information
        frontPoint, leftPoint, rightPoint = self.getSensorPoints()
        
        # Update Information
        self.updatePastVals((frontPoint, leftPoint, rightPoint))
        # Apply A Star Heuristic
        newDirection = self.getHeuristic(self.position)
                
        # Check to See if You Are Stuck
        if self.boatStuck():
            newDirection = self.getDirection(random.randrange(360))
        
        # Update Boat
        self.updateBoat(newDirection)


# --------------------------------------------------------------------------- #
#                             Run Boat Simulation                             #
# --------------------------------------------------------------------------- #

def runSimulation(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats = 1, simFile = "./", visualize = True):
    """
    Runs NUM_TRIALS trials of the simulation and returns the mean number of
    time-steps needed to clean the fraction MIN_COVERAGE of the tank.

    The simulation is run with numBoats boats of type boat_TYPE, each with
    speed SPEED, in a tank of dimensions tankWidth x tankHeight.

    sourceLocations: A list of tuples representing the x,y locations of the sources [(1,2),(3,4)]
    boatLocations: A list of tuples representing the x,y locations of the boats [(1,2),(3,4)]
    boatSpeed: a float (boatSpeed > 0)
    tankWidth: an int (tankWidth > 0)
    tankHeight: an int (tankHeight > 0)
    numBoats: an int (numBoats > 0)
    visualize: Boolean
    """
    # Initialize the Tank
    #waterTank = cosmolSimTank(sourceLocations, tankWidth, tankHeight, simFile)
    #waterTank = diffusionModelTank(sourceLocations, tankWidth, tankHeight)
    waterTank = userInputModel(sourceLocations, tankWidth, tankHeight)
    
    # Initialize the Boat
    boatType = AStar
    # Initialize Evaluation Oarameters
    total_time_steps = 0.0
    # Initialize Animation for Searching
    if visualize:
        anim = simulateBoat.boatVisualization(numBoats, waterTank.tankWidth, waterTank.tankHeight)
    
    # Add the Boats to the Tank
    boatCollection = []
    for boatNum in range(numBoats):
        boatCollection.append(boatType(waterTank, boatSpeed, boatLocations[boatNum]))
    if visualize:
        anim.update(waterTank, boatCollection)
    
    # Run the Search Algorythm Until the Boat Reaches the Source
    while not waterTank.sourceFound():
        # Move Each Boat
        for boat in boatCollection:
            boat.updatePosition()
        total_time_steps += 1
        # Update Animation with the Movement
        if visualize:
            anim.update(waterTank, boatCollection)
    if visualize:
        anim.done()
    
    #Return the Total Time Steps it Took
    return total_time_steps

def compareAlgorythms(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats = 1, simFile = "./"):
    """
    Runs NUM_TRIALS trials of the simulation and returns the mean number of
    time-steps needed to clean the fraction MIN_COVERAGE of the tank.

    The simulation is run with numBoats boats of type boat_TYPE, each with
    speed SPEED, in a tank of dimensions tankWidth x tankHeight.

    sourceLocations: A list of tuples representing the x,y locations of the sources [(1,2),(3,4)]
    boatLocations: A list of tuples representing the x,y locations of the boats [(1,2),(3,4)]
    boatSpeed: a float (boatSpeed > 0)
    tankWidth: an int (tankWidth > 0)
    tankHeight: an int (tankHeight > 0)
    numBoats: an int (numBoats > 0)
    visualize: Boolean
    """
    # Initialize the Boat
    boatTypes = [AStar, gradientDescent, pureHeuristic, weightedMaxDirection, maxDirection, randomBoat]
    labels = ['AStar', 'gradientDescent', 'pureHeuristic', 'weightedMaxDirection', 'maxDirection', 'randomDirection ']
    timeSteps = []
    #boatTypes = [AStar, gradientDescent, pureHeuristic]


    algPositions = {}
    for i, boatType in enumerate(boatTypes):
        waterTank = cosmolSimTank(sourceLocations, tankWidth, tankHeight, simFile)

        print(boatType)
        algPositions[i] = {'x':[], 'y':[]}
        # Add the Boats to the Tank
        boatCollection = []
        for boatNum in range(numBoats):
            boatCollection.append(boatType(waterTank, boatSpeed, boatLocations[boatNum]))
        
        algPositions[i]['x'].append(boatCollection[0].position.x)
        algPositions[i]['y'].append(boatCollection[0].position.y)
        
        total_time_steps = 0.0
        # Run the Search Algorythm Until the Boat Reaches the Source
        while not waterTank.sourceFound():
            # Move Each Boat
            for boat in boatCollection:
                boat.updatePosition()
                
            algPositions[i]['x'].append(boat.position.x)
            algPositions[i]['y'].append(boat.position.y)
            total_time_steps += 1
            if total_time_steps > 50:
                timeSteps.append(total_time_steps)
                break
            if waterTank.sourceFound():
                timeSteps.append(total_time_steps)
            
    fig = plt.figure()
    ax = fig.add_subplot(111, xlim=[0, tankWidth], ylim=[0, tankHeight], autoscale_on=False)
    ax.set_aspect('auto')
    
    xVec = np.linspace(0, tankWidth, 75)
    yVec = np.linspace(0, tankHeight, 75)
    xData, yData, zData = waterTank.find2DSimMap(xVec, yVec)
    fullData = np.stack((xData, yData, zData))
    sc = plt.scatter(fullData[0], fullData[1], c=fullData[2], cmap='jet', norm=matplotlib.colors.LogNorm())
    #plt.clim(10E-20,10)  # identical to caxis([-4,4]) in MATLAB
    plt.colorbar(sc)

    for i in range(len(boatTypes)):
        plt.plot(algPositions[i]['x'], algPositions[i]['y'], label=labels[i]+" Steps: "+str(timeSteps[i]), linewidth=2, path_effects=[pe.Stroke(linewidth=4, foreground='k'), pe.Normal()])
    
    plt.title("Search Algorithm Comparison")
    plt.xlabel("Tank Width")
    plt.ylabel("Tank Height")
    plt.legend(loc='upper left', bbox_to_anchor=(1.25, 1.02), fancybox=True, shadow=True)
    
    plt.show()
    
    return algPositions, fullData



def showPlot1(title, x_label, y_label, sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numActiveBoats):
    """
    Produces a plot comparing the two boat strategies in a 20x20 tank with 80%
    minimum coverage.
    """
    times1 = []
    times2 = []
    for numBoats in range(numActiveBoats):
        print("Plotting", numBoats, "boats...")        
        times1.append(runSimulation(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats))
        times2.append(runSimulation(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats))
    pylab.plot(range(numActiveBoats), times1) 
    pylab.plot(range(numActiveBoats), times2)
    pylab.title(title)
    pylab.legend(('Standardboat', 'RandomWalkboat'))
    pylab.xlabel(x_label)
    pylab.ylabel(y_label)
    pylab.show()

    
def showPlot2(title, x_label, y_label, sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats):
    """
    Produces a plot showing dependence of cleaning time on tank shape.
    """
    aspect_ratios = []
    times1 = []
    times2 = []
    for tankWidth in [10, 20, 25, 50]:
        tankHeight = 300/tankWidth
        print("Plotting cleaning time for a tank of Width:", tankWidth, "by Height:", tankHeight)
        aspect_ratios.append(float(tankWidth) / tankHeight)
        times1.append(runSimulation(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats))
        times2.append(runSimulation(sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats))
    pylab.plot(aspect_ratios, times1)
    pylab.plot(aspect_ratios, times2)
    pylab.title(title)
    pylab.legend(('Standardboat', 'RandomWalkboat'))
    pylab.xlabel(x_label)
    pylab.ylabel(y_label)
    pylab.show()


if __name__ == '__main__':
    sourceLocations = [(5,6)]
    boatLocations = [(0,0)]
    boatSpeed = 2
    tankWidth = 20
    tankHeight = 20
    numBoats = 1
    
    showPlot1('Time to clean 80% of a 20x20 tank, for various numbers of boats', 'Number of boats',
              'Time/ steps', sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats)
    showPlot2('Time to clean 80% of a 400-tile tank for various tank shapes', 'Aspect Ratio',
              'Time / steps', sourceLocations, boatLocations, boatSpeed, tankWidth, tankHeight, numBoats)
    
    
    
