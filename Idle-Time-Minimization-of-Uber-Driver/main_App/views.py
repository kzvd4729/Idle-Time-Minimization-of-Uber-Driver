from django.shortcuts import render
import json
import pandas as pd
from django.http import HttpResponse
from django.http import JsonResponse


from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
from rtree import index as ID


a=[[],[]]
cluster=[[],[]]
pCluster=[[],[]]
rt=[[],[]]
radiusThreshold=0.02 # 2.6 km


'''
This function will take two parameter
a is the data point in pair format
label is the cluster label of corresponding data point

Will return a list of tuple containg cluster center and cluster size
'''
def processCluster(a,label):
  mx=0 # maximum cluster label
  for x in label:
    if x>mx:
      mx=x
  
  mx+=1
  b=[] # b[i] will hold all the point having label i
  for i in range(0,mx):
    b.append([])


  for i in range(0,len(a)):
    b[label[i]].append(a[i])
  

  ret=[]
  for i in range(0,mx):
    totalX=0
    totalY=0
    for z in b[i]:
      totalX+=z[0]
      totalY+=z[1]
    
    n=len(b[i])
    ret.append((totalX/n,totalY/n,n))
  
  return ret





def makeCluster():
  '''
  Important parameter for sklearn.cluster.KMeans:
  n_clusters = Number of cluster we want. default = 8
  n_init = Number of times KMeans will run. Will return best ruslt out of this
           n_init times. default = 10
  max_iter = Miximum number of times centroid will change. default = 300

  random_state = Used for randomly selecting the initial centroid. An integer is
                 used to fix the randomness.


  

  Important attributes for sklearn.cluster.KMeans:
  cluster_centers_ = Returns a list of cluster center
  labels_ = Returns cluster label for each point
  '''
  for i in range(0,2):
    for j in range(0,24):
      cluster[i][j]=KMeans(n_clusters=int(len(a[i][j])/10), random_state=0).fit(a[i][j])


  #scatterplot(a[0][0],cluster[0][0])

  for i in range(0,2):
    for j in range(0,24):
      pCluster[i][j]=processCluster(a[i][j],cluster[i][j].labels_)





def makeRtree():
  '''
  Insert a point by insert(id,(left,bottom,right,top))
  Query a rectangle by intersection(left,bottom,right,top)
  '''
  for i in range(0,2):
    for j in range(0,24):
      rt[i][j]=ID.Index() # constructor
      for k in range(0,len(pCluster[i][j])):
        x=pCluster[i][j][k][0]
        y=pCluster[i][j][k][1]
        rt[i][j].insert(k,(x,y,x,y))




from math import pi,sqrt,sin,cos,atan2
def distance(pos1, pos2):
    lat1 = float(pos1[0])
    long1 = float(pos1[1])
    lat2 = float(pos2[0])
    long2 = float(pos2[1])

    degree_to_rad = float(pi / 180.0)

    d_lat = (lat2 - lat1) * degree_to_rad
    d_long = (long2 - long1) * degree_to_rad

    a = pow(sin(d_lat / 2), 2) + cos(lat1 * degree_to_rad) * cos(lat2 * degree_to_rad) * pow(sin(d_long / 2), 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    km = 6367 * c

    return km

def score(d,s):
  return (1.0/d) * s

def queryAnswer(lat, lon, hour, hol):
  r=radiusThreshold
  numberOfPoints=50
  if(len(pCluster[hol][hour])<numberOfPoints):
    numberOfPoints=len(pCluster[hol][hour])

  points=list(rt[hol][hour].nearest((lat-r,lon-r,lat+r,lon+r),numberOfPoints))
  mn=0.0
  pointX = 0
  pointY = 0
  for x in points:
    d=distance((lat,lon),(pCluster[hol][hour][x][0],pCluster[hol][hour][x][1]))
    sc=score(d,float(pCluster[hol][hour][x][2]))
    if sc>mn:
      mn=sc
      pointX=pCluster[hol][hour][x][0]
      pointY=pCluster[hol][hour][x][1]

    #print(pCluster[hol][hour][x], distance((lat,lon),(pCluster[hol][hour][x][0],pCluster[hol][hour][x][1])),sc)
  
  #print('\n')
  #print(point)
  return pointX, pointY


"""
  For now working with small data set, if our algorithm works efficently
  we will increase the dataset
  """
#df=pd.read_csv('F:/wamp64/www/driver_scheduling_optimization/finalData(120000).csv')
df=pd.read_csv('C:/Users/Araf/djangoProjects/IdleTimeMinimization/templates/finalData(6000).csv')
"""
  Creating an array so that we can use holiday and hour as index
  """
  
for i in range(0,2):
  for j in range(0,24):
    a[i].append([])
    cluster[i].append([])
    pCluster[i].append([])
    rt[i].append([])

for i in range(0,len(df)):
  a[int(df.loc[i][3])][int(df.loc[i][2])].append((df.loc[i][0],df.loc[i][1]))


makeCluster()
makeRtree()


def index(request):
    
    sourceLat = df['Lat'].iloc[0]
    sourceLon = df['Lon'].iloc[0]

    if request.is_ajax():
        lat = request.GET.get('sourceLat')
        lon = request.GET.get('sourceLon')
        hour = None
        holiday = None
        if request.GET.get('hour'):
            hour = int(request.GET.get('hour'))
        if request.GET.get('holiday'):
            holiday = int(request.GET.get('holiday'))

        if lat != None:
            sourceLat = float(lat)
            sourceLon = float(lon)

            request.session['sourceLat'] = sourceLat
            request.session['sourceLon'] = sourceLon
            hour = request.session['Hour']
            holiday = request.session['Holiday']

            pointX, pointY = queryAnswer(sourceLat,sourceLon,hour,holiday)

            markers = df.loc[(df['Hour']==hour) & (df['Holiday']==holiday)].to_json(orient='records')
            context = {'markers': markers, "sourceLat": sourceLat, "sourceLon": sourceLon, "pointX": pointX, "pointY": pointY}

            return HttpResponse(json.dumps(context))
        elif hour != None:
            sourceLat = request.session['sourceLat']
            sourceLon = request.session['sourceLon']
            holiday = request.session['Holiday']
            if hour != -1:
                request.session['Hour'] = hour
            else:
                request.session['Hour'] = 0

            if hour==-1:
                hour=0

            request.session['Holiday'] = holiday
            pointX, pointY = queryAnswer(sourceLat,sourceLon,hour,holiday)
            markers = df.loc[(df['Hour']==hour) & (df['Holiday']==holiday)].to_json(orient='records')
            context = {'markers': markers, "sourceLat": sourceLat, "sourceLon": sourceLon, "pointX": pointX, "pointY": pointY}
            return HttpResponse(json.dumps(context))
        elif holiday != None:
            sourceLat = request.session['sourceLat']
            sourceLon = request.session['sourceLon']
            hour = request.session['Hour']
            request.session['Holiday'] = holiday

            if hour==None:
                hour = 0

            pointX, pointY = queryAnswer(sourceLat,sourceLon,hour,holiday)

            markers = df.loc[(df['Hour']==hour) & (df['Holiday']==holiday)].to_json(orient='records')
            context = {'markers': markers, "sourceLat": sourceLat, "sourceLon": sourceLon, "pointX": pointX, "pointY": pointY}
            return HttpResponse(json.dumps(context))
    
    request.session['sourceLat'] = sourceLat
    request.session['sourceLon'] = sourceLon
    request.session['Hour'] = 0
    request.session['Holiday'] = 0

    pointX, pointY = queryAnswer(sourceLat,sourceLon,0,0)
    markers = df.loc[(df['Hour']==0) & (df['Holiday']==0)].to_json(orient='records')
    context = {'markers': markers, "sourceLat": sourceLat, "sourceLon": sourceLon, "pointX": pointX, "pointY": pointY}
    return render(request,'index.html',context)
