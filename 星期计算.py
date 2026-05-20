def leap(year):
  return year%4==0 and year%100!=0 or year%400==0
mon=[0,31,28,31,30,31,30,31,31,30,31,30,31]
y,m,d=map(int,input().split())
total=0
for year in range(2000,y):
  total+=366 if leap(year) else 365
for month in range(1,m):
  total+=mon[month]
if m>2 and leap(year):
  total+=1
total+=d-1
week=["星期六","星期日","星期一","星期二","星期三","星期四","星期五"]
print(week[total%7])