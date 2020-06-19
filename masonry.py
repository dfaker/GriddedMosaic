from math import floor

"""

#Build walls of rectangles that will retain their aspect ratios and resize themselves to fill a wider rectangle specified by width or height.
Example with three 'bricks':

#Three 'bricks' one square, two rectangular

b1 = Brick('img_b1.png',100,100)
b2 = Brick('img_b2.png',100,50)
b3 = Brick('img_b3.png',100,50)

#Put them into two vertical columns, the left containing the square, the right containing the two rectangles

leftColumn  = Stack([b1],orientation='vertical')
rightColumn = Stack([b2,b3],orientation='vertical')

#And put those into a horizontal row:

outerRow    = Stack([leftColumn,rightColumn],orientation='horizontal')

#Initialise a logger to store the cordinates and sizes when they're asked to pack with a constraint

logger = {}

#The origin to place the bricks at

xorigin = 0
yorigin = 0

#What size would the bricks need to be if I wanted the outer row to be 200 pixels high starting at xorigin,yorigin
outerRow.getSizeWithContstraint('height',200,logger,xorigin,yorigin)

print(logger)

# img_b1 is at 0,0 : 200px by 200px, doube it's original size of 100x100
# img_b2 is at 200,0 : 50px by 100px, it has kept its original size of 50x100
# img_b3 is at 200,100 : 50px by 100px, it has kept its original size of 50x100

{ 'img_b1.png': (0, 0, 200, 200, 2.0, 100, 100), 
  'img_b2.png': (200, 0, 50, 100, 1.0, 50, 100), 
  'img_b3.png': (200, 100, 50, 100, 1.0, 50, 100)
}

"""


class Brick:

  def __init__(self,identifier,width,height):
    self.identifier=identifier
    self.height=height*1.0
    self.width=width*1.0

  def __repr__(self):
    return "<b{} {}x{}>".format(self.identifier,self.width,self.height)

  def getSize(self):
    return self.width,self.height





  def getSizeWithContstraint(self,constrainedDirection,constraint,logger=None,xo=None,yo=None):
    if constraint is None:
      if logger is not None:
        logger[self.identifier]=(floor(xo),
                                 floor(yo),
                                 floor(self.width),
                                 floor(self.height),
                                 1.0,
                                 floor(self.width),
                                 floor(self.height))

      return floor(self.width),floor(self.height)
    else:
      if constrainedDirection=='height':
        ar = constraint/self.height
        if logger is not None:
          logger[self.identifier]=(floor(xo),
                                   floor(yo),
                                   floor(self.width*ar),
                                   floor(constraint),
                                   ar,
                                   floor(self.width),
                                   floor(self.height))

        return floor(self.width*ar),floor(constraint)

      elif constrainedDirection=='width':
        ar = constraint/self.width
        if logger is not None:
          logger[self.identifier]=(floor(xo),
                                   floor(yo),
                                   floor(constraint),
                                   floor(self.height*ar),
                                   ar,
                                   floor(self.width),
                                   floor(self.height))
        return floor(constraint),floor(self.height*ar)
      else:
        raise Exception('Invalid direction {}'.format(constrainedDirection))

class Stack:

  def __init__(self,bricks,orientation='vertical'):
    if orientation not in ('vertical','horizontal'):
      raise Exception('Invalid orientation')
    self.bricks=bricks
    self.orientation=orientation

  def __init__(self,bricks,orientation='vertical'):
    if orientation not in ('vertical','horizontal'):
      raise Exception('Invalid orientation')
    self.bricks=bricks
    self.orientation=orientation

  def append(self,brick):
    self.bricks.append(brick)

  def insert(self,pos,brick):
    self.bricks.insert(pos,brick)

  def __repr__(self):
    return "<s{} {}>".format(self.orientation,len(self.bricks))


  def getSizeWithContstraint(self,direction,constraint,logger=None,xo=None,yo=None):
    if direction=='height':
      if self.orientation=='vertical':
        heights=[]
        for brick in self.bricks:
          _,h = brick.getSizeWithContstraint('width',1000)
          heights.append(h)
        sumheights=sum(heights)

        finalwidth=0
        finalheight=0
        heights = [(h/sumheights)*constraint for h in heights]
        for requestedHeight,brick in zip(heights,self.bricks):
          w,h = brick.getSizeWithContstraint('height',requestedHeight,logger,xo,None if yo is None else yo+finalheight)
          finalwidth=w
          finalheight+=h

        return floor(finalwidth),floor(finalheight)
      elif self.orientation=='horizontal':
        finalwidth=0
        finalheight=0
        for brick in self.bricks:
          w,h = brick.getSizeWithContstraint('height',constraint,logger,None if xo is None else xo+finalwidth,yo)
          finalwidth+=w
          finalheight=h
        return floor(finalwidth),floor(finalheight)
    elif direction=='width':
      if self.orientation=='horizontal':
        widths=[]
        for brick in self.bricks:
          w,_ = brick.getSizeWithContstraint('height',1000)
          widths.append(w)
        sumwidths=sum(widths)

        finalwidth=0
        finalheight=0
        widths = [(w/sumwidths)*constraint for w in widths]

        for requestedWidth,brick in zip(widths,self.bricks):
          w,h = brick.getSizeWithContstraint('width',requestedWidth,logger,None if xo is None else xo+finalwidth,yo)
          finalwidth+=w
          finalheight=h
        return floor(finalwidth),floor(finalheight)
      elif self.orientation=='vertical':
        finalwidth=0
        finalheight=0
        for brick in self.bricks:
          w,h = brick.getSizeWithContstraint('width',constraint,logger,xo,None if yo is None else yo+finalheight)
          finalwidth=w
          finalheight+=h
        return floor(finalwidth),floor(finalheight)
    else:
      raise Exception('Invalid direction')
