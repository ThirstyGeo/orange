#
# OWScatterPlotGraph.py
#
# the base for scatterplot

import sys
import math
import orange
import os.path
from OWGraph import *
from OWDistributions import *
from qt import *
from OWTools import *
from qwt import *
from Numeric import *


###########################################################################################
##### CLASS : OWSCATTERPLOTGRAPH
###########################################################################################
class OWScatterPlotGraph(OWGraph):
    def __init__(self, parent = None, name = None):
        "Constructs the graph"
        OWGraph.__init__(self, parent, name)

        self.pointWidth = 4
        self.scaledData = []
        self.scaledDataAttributes = []
        self.jitteringType = 'none'
        self.jitterContinuous = 0
        self.jitterSize = 1
        self.graphCanvasColor = str(Qt.white.name())

        self.enableGridX(FALSE)
        self.enableGridY(FALSE)

        self.noneSymbol = QwtSymbol()
        self.noneSymbol.setStyle(QwtSymbol.None)

        self.enabledLegend = 0

    def setJitteringOption(self, jitteringType):
        self.jitteringType = jitteringType

    def setPointWidth(self, width):
        self.pointWidth = width

    def enableGraphLegend(self, enable):
        self.enabledLegend = enable

    def setJitterContinuous(self, enable):
        self.jitterContinuous = enable

    def setJitterSize(self, size):
        self.jitterSize = size
    #
    # scale data at index index to the interval 0 - 1
    #
    def scaleData(self, data, index, jitteringEnabled = 1):
        attr = data.domain[index]
        temp = [];
        # is the attribute discrete
        if attr.varType == orange.VarTypes.Discrete:
            # we create a hash table of variable values and their indices
            variableValueIndices = {}
            for i in range(len(attr.values)):
                variableValueIndices[attr.values[i]] = i

            count = float(len(attr.values))
            for i in range(len(data)):
                #val = (1.0 + 2.0*float(variableValueIndices[data[i][index].value])) / float(2*count)
                val = float(variableValueIndices[data[i][index].value]) / float(count)
                temp.append(val)
            return (temp, (0, count-1))

                    
        # is the attribute continuous
        else:
            # first find min and max value
            i = 0
            while data[i][attr].isSpecial() == 1: i+=1
            min = data[i][attr].value
            max = data[i][attr].value
            for item in data:
                if item[attr].isSpecial() == 1: continue
                if item[attr].value < min:
                    min = item[attr].value
                elif item[attr].value > max:
                    max = item[attr].value

            diff = max - min
            # create new list with values scaled from 0 to 1
            for i in range(len(data)):
                temp.append((data[i][attr].value - min) / diff)

            return (temp, (min, max))

    #
    # set new data and scale its values
    #
    def setData(self, data):
        self.rawdata = data
        self.scaledData = []
        self.scaledDataAttributes = []
        
        if data == None: return

        self.attrVariance = []
        for index in range(len(data.domain)):
            attr = data.domain[index]
            self.scaledDataAttributes.append(attr.name)
            (scaled, variance)= self.scaleData(data, index)
            self.scaledData.append(scaled)
            self.attrVariance.append(variance)

    #
    # update shown data. Set labels, coloring by className ....
    #
    def updateData(self, xAttr, yAttr, colorAttr, shapeAttr, sizeShapeAttr):
        self.removeCurves()

        if len(self.scaledData) == 0: self.updateLayout(); return

        if self.rawdata.domain[xAttr].varType == orange.VarTypes.Continuous:
            self.setXlabels(None)
        else:   self.setXlabels(self.rawdata.domain[xAttr].values)

        if self.rawdata.domain[yAttr].varType == orange.VarTypes.Continuous: self.setYLlabels(None)
        else:   self.setYLlabels(self.rawdata.domain[xAttr].values)

        if self.showXaxisTitle == 1: self.setXaxisTitle(xAttr)
        if self.showYLaxisTitle == 1: self.setYLaxisTitle(yAttr)


        (xVarMin, xVarMax) = self.attrVariance[self.scaledDataAttributes.index(xAttr)]
        (yVarMin, yVarMax) = self.attrVariance[self.scaledDataAttributes.index(yAttr)]
        xVar = xVarMax - xVarMin
        yVar = yVarMax - yVarMin
        
        self.setAxisScale(QwtPlot.xBottom, xVarMin - (self.jitterSize * xVar / 80.0), xVarMax + (self.jitterSize * xVar / 80.0), 1)
        self.setAxisScale(QwtPlot.yLeft, yVarMin - (self.jitterSize * yVar / 80.0), yVarMax + (self.jitterSize * yVar / 80.0), 1)

        colorIndex = -1
        if colorAttr != "" and colorAttr != "(One color)":
            colorIndex = self.scaledDataAttributes.index(colorAttr)

        shapeIndex = -1
        shapeIndices = {}
        if shapeAttr != "" and shapeAttr != "(One shape)" and len(self.rawdata.domain[shapeAttr].values) < 11:
            shapeIndex = self.scaledDataAttributes.index(shapeAttr)
            attr = self.rawdata.domain[shapeAttr]
            for i in range(len(attr.values)):
                shapeIndices[attr.values[i]] = i


        sizeShapeIndex = -1
        if sizeShapeAttr != "" and sizeShapeAttr != "(One size)":
            sizeShapeIndex = self.scaledDataAttributes.index(sizeShapeAttr)

        shapeList = [QwtSymbol.Ellipse, QwtSymbol.Rect, QwtSymbol.Diamond, QwtSymbol.Triangle, QwtSymbol.DTriangle, QwtSymbol.UTriangle, QwtSymbol.LTriangle, QwtSymbol.RTriangle, QwtSymbol.Cross, QwtSymbol.XCross, QwtSymbol.StyleCnt]


        # create hash tables in case of discrete X axis attribute
        attrXIndices = {}
        discreteX = 0
        if self.rawdata.domain[xAttr].varType == orange.VarTypes.Discrete:
            discreteX = 1
            attr = self.rawdata.domain[xAttr]
            for i in range(len(attr.values)):
                attrXIndices[attr.values[i]] = i

        # create hash tables in case of discrete Y axis attribute
        attrYIndices = {}
        discreteY = 0
        if self.rawdata.domain[yAttr].varType == orange.VarTypes.Discrete:
            discreteY = 1
            attr = self.rawdata.domain[yAttr]
            for i in range(len(attr.values)):
                attrYIndices[attr.values[i]] = i

        self.curveKeys = []
        for i in range(len(self.rawdata)):
            if discreteX == 1:
                x = attrXIndices[self.rawdata[i][xAttr].value] + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
            elif self.jitterContinuous == 1:
                x = self.rawdata[i][xAttr].value + self.rndCorrection(float(self.jitterSize * xVar) / 100.0)
            else:
                x = self.rawdata[i][xAttr].value

            if discreteY == 1:
                y = attrYIndices[self.rawdata[i][yAttr].value] + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
            elif self.jitterContinuous == 1:
                y = self.rawdata[i][yAttr].value + self.rndCorrection(float(self.jitterSize * yVar) / 100.0)
            else:
                y = self.rawdata[i][yAttr].value

            newColor = QColor(0,0,0)
            if colorIndex != -1:
                newColor.setHsv(self.scaledData[colorIndex][i]*360, 255, 255)

            symbol = shapeList[0]
            if shapeIndex != -1:
                symbol = shapeList[shapeIndices[self.rawdata[i][shapeIndex].value]]

            size = self.pointWidth
            if sizeShapeIndex != -1:
                size = 4 + round(self.scaledData[sizeShapeIndex][i] * 20)

            newCurveKey = self.insertCurve(str(i))
            newSymbol = QwtSymbol(symbol, QBrush(QBrush.NoBrush), QPen(newColor), QSize(size, size))
            self.setCurveSymbol(newCurveKey, newSymbol)
            self.setCurveData(newCurveKey, [x], [y])
            self.curveKeys.append(newCurveKey)

        # show legend if necessary
        self.enableLegend(0)
        if self.enabledLegend == 1:
            if colorIndex != -1 and self.rawdata.domain[colorIndex].varType == orange.VarTypes.Discrete:
                numColors = len(self.rawdata.domain[colorIndex].values)
                varName = self.rawdata.domain[colorIndex].name
                for ind in range(numColors):
                    newCurveKey = self.insertCurve(varName + "=" + self.rawdata.domain[colorIndex].values[ind])
                    newColor = QColor()
                    newColor.setHsv(float(ind) / float(numColors) * 360, 255, 255)
                    newSymbol = QwtSymbol(QwtSymbol.Ellipse, QBrush(newColor), QPen(newColor), QSize(self.pointWidth, self.pointWidth))
                    self.setCurveSymbol(newCurveKey, newSymbol)
                    self.enableLegend(1, newCurveKey)

            if shapeIndex != -1 and self.rawdata.domain[shapeIndex].varType == orange.VarTypes.Discrete:
                numShapes = len(self.rawdata.domain[shapeIndex].values)
                varName = self.rawdata.domain[shapeIndex].name
                for ind in range(numShapes):
                    newCurveKey = self.insertCurve(varName + "=" + self.rawdata.domain[shapeIndex].values[ind])
                    newSymbol = QwtSymbol(shapeList[ind], QBrush(QColor(0,0,0)), QPen(QColor(0,0,0)), QSize(self.pointWidth, self.pointWidth))
                    self.setCurveSymbol(newCurveKey, newSymbol)
                    self.enableLegend(1, newCurveKey)

            if sizeShapeIndex != -1 and self.rawdata.domain[sizeShapeIndex].varType == orange.VarTypes.Discrete:
                sizeShapes = len(self.rawdata.domain[sizeShapeIndex].values)
                varName = self.rawdata.domain[sizeShapeIndex].name
                for ind in range(sizeShapes):
                    newCurveKey = self.insertCurve(varName + "=" + self.rawdata.domain[sizeShapeIndex].values[ind])
                    size = 4 + round(float(ind)/float(sizeShapes) * 20)
                    newSymbol = QwtSymbol(QwtSymbol.Ellipse, QBrush(QColor(0,0,0)), QPen(QColor(0,0,0)), QSize(size, size))
                    self.setCurveSymbol(newCurveKey, newSymbol)
                    self.enableLegend(1, newCurveKey)

        # -----------------------------------------------------------
        # -----------------------------------------------------------
        

    def rndCorrection(self, max):
        """
        returns a number from -max to max, self.jitteringType defines which distribution is to be used.
        function is used to plot data points for categorical variables
        """    
        if self.jitteringType == 'none': 
            return 0.0
        elif self.jitteringType  == 'uniform': 
            return (random() - 0.5)*2*max
        elif self.jitteringType  == 'triangle': 
            b = (1 - betavariate(1,1)) ; return choice((-b,b))*max
        elif self.jitteringType  == 'beta': 
            b = (1 - betavariate(1,2)) ; return choice((-b,b))*max

    
if __name__== "__main__":
    #Draw a simple graph
    a = QApplication(sys.argv)        
    c = OWRadvizGraph()
        
    a.setMainWidget(c)
    c.show()
    a.exec_loop()
