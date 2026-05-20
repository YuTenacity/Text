import turtle as t

def drawLine(draw):
    t.pendown() if draw else t.penup()
    t.fd(40)
    t.right(90)

def drawDigit(d):
    drawLine(True) if d in [2,3,4,5,6,8,9,'A','B','D','E','F'] else drawLine(False)
    drawLine(True) if d in [0,1,3,4,5,6,7,8,9,'A','B','D'] else drawLine(False)
    drawLine(True) if d in [0,2,3,5,6,8,9,'B','C','D','E'] else drawLine(False)
    drawLine(True) if d in [0,2,6,8,'A','B','C','D','E','F'] else drawLine(False)
    t.left(90)  
    drawLine(True) if d in [0,4,5,6,8,9,'A','B','C','E','F'] else drawLine(False)
    drawLine(True) if d in [0,2,3,5,6,7,8,9,'A','C','E','F'] else drawLine(False)
    drawLine(True) if d in [0,1,2,3,4,7,8,9,'A','D'] else drawLine(False)
    t.left(180) 
    t.penup()
    t.fd(20)     

def drawDate(date):
    for char in date:
        d = int(char) if char.isdigit() else char
        drawDigit(d)

def main():
    t.setup(1000, 350, 200, 200)  
    t.speed(0)                    
    t.penup()
    t.goto(-450, 0)              
    t.pensize(5)
    t.hideturtle()
    drawDate("0123456789ABCDEF")
    t.done()
main()    
