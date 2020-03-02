import numpy as np
import scipy as scipy
from numpy.random import uniform
import scipy.stats


# 3 numbers while the array is too big
# suppress printing of small floating point values using scientific notation
np.set_printoptions(threshold=3)
np.set_printoptions(suppress=True)
import cv2


# the line of monse
def drawLines(img, points, r, g, b):
    cv2.polylines(img, [np.int32(points)], isClosed=False, color=(r, g, b))

def drawCross(img, center, r, g, b):
    d = 5
    t = 2
    LINE_AA = cv2.LINE_AA if cv2.__version__[0] == '3' else cv2.CV_AA
    color = (r, g, b)
    ctrx = center[0,0]
    ctry = center[0,1]
    cv2.line(img, (ctrx - d, ctry - d), (ctrx + d, ctry + d), color, t, LINE_AA)
    cv2.line(img, (ctrx + d, ctry - d), (ctrx - d, ctry + d), color, t, LINE_AA)


# supposed to update
def getRobotPosition(particles, weights):
    x = np.average(particles[:, 0], weights=weights)
    y = np.average(particles[:, 1], weights=weights)
    return x, y


def mouseCallback(event, x, y, flags,null):
    global center
    global trajectory
    global robot_pos
    global previous_x
    global previous_y
    global zs
    
    center=np.array([[x,y]])
    # make 2 arrays together
    trajectory=np.vstack((trajectory,np.array([x,y])))
    #noise=sensorSigma * np.random.randn(1,2) + sensorMu

    if previous_x >0:
        heading=np.arctan2(np.array([y-previous_y]), np.array([previous_x-x ]))

        if heading>0:
            heading=-(heading-np.pi)
        else:
            heading=-(np.pi+heading)
            
        distance=np.linalg.norm(np.array([[previous_x,previous_y]])-np.array([[x,y]]) ,axis=1)
        
        std=np.array([2,4])
        u=np.array([heading,distance])
        predict(particles, u, std, dt=1.)
        zs = (np.linalg.norm(landmarks - center, axis=1) + (np.random.randn(NL) * sensor_std_err))
        update(particles, weights, z=zs, R=50, landmarks=landmarks)
        
        robot_x, robot_y = getRobotPosition(particles, weights)
        robot_pos = np.vstack((robot_pos,np.array([robot_x, robot_y])))
        
        indexes = systematic_resample(weights)
        resample_from_index(particles, weights, indexes)
 
    previous_x=x
    previous_y=y
    

# size of window
WIDTH=800
HEIGHT=600
WINDOW_NAME="Particle Filter"

#sensorMu=0
#sensorSigma=3

sensor_std_err=5


def create_uniform_particles(x_range, y_range, N):
    # a random N*2 array
    particles = np.empty((N, 2))    
    particles[:, 0] = uniform(x_range[0], x_range[1], size=N)
    particles[:, 1] = uniform(y_range[0], y_range[1], size=N)
    return particles


def predict(particles, u, std, dt=1.):
    N = len(particles)
    dist = (u[1] * dt) + (np.random.randn(N) * std[1])
    particles[:, 0] += np.cos(u[0]) * dist
    particles[:, 1] += np.sin(u[0]) * dist
   

def update(particles, weights, z, R, landmarks):
    weights.fill(1.)
    for i, landmark in enumerate(landmarks):
        distance=np.power((particles[:,0] - landmark[0])**2 +(particles[:,1] - landmark[1])**2,0.5)

        # change norm to petato
        # perato.pdf(x, b, loc, scale)
        # weights *= scipy.stats.pareto.pdf(z[i], 0.3, distance, R) 
        weights *= scipy.stats.genpareto.pdf(z[i], 10, distance, R) 

    weights += 1.e-300 # avoid round-off to zero
    weights /= sum(weights)


def neff(weights):
    return 1. / np.sum(np.square(weights))


def systematic_resample(weights):
    N = len(weights)
    positions = (np.arange(N) + np.random.random()) / N

    indexes = np.zeros(N, 'i')
    cumulative_sum = np.cumsum(weights)
    i, j = 0, 0
    while i < N and j<N:
        if positions[i] < cumulative_sum[j]:
            indexes[i] = j
            i += 1
        else:
            j += 1
    return indexes


def estimate(particles, weights):
    pos = particles[:, 0:1]
    mean = np.average(pos, weights=weights, axis=0)
    var = np.average((pos - mean)**2, weights=weights, axis=0)
    return mean, var


def resample_from_index(particles, weights, indexes):
    particles[:] = particles[indexes]
    weights[:] = weights[indexes]
    weights /= np.sum(weights)

    
x_range=np.array([0,800])
y_range=np.array([0,600])

# Number of partciles
N=400

landmarks=np.array([ [144,73], [410,13], [336,175], [718,159], [178,484], [665,464] ])
NL = len(landmarks)
particles=create_uniform_particles(x_range, y_range, N)

# 1*N
weights = np.array([1.0]*N)

# Create a black image, a window and bind the function to window
img = np.zeros((HEIGHT,WIDTH,3), np.uint8)
cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME,mouseCallback)

center=np.array([[-10,-10]])

trajectory=np.zeros(shape=(0,2))
robot_pos=np.zeros(shape=(0,2))
previous_x=-1
previous_y=-1
DELAY_MSEC=50

while(1):

    cv2.imshow(WINDOW_NAME,img)
    img = np.zeros((HEIGHT,WIDTH,3), np.uint8)
    drawLines(img, trajectory,   0,   255, 0)
    drawLines(img, robot_pos,   0,   0, 255)
    drawCross(img, center, r=255, g=0, b=0)
    
    #landmarks
    for landmark in landmarks:
        cv2.circle(img,tuple(landmark),10,(255,0,0),-1)
    
    
    #draw_particles:
    for particle in particles:
        cv2.circle(img,tuple((int(particle[0]),int(particle[1]))),1,(255,255,255),-1)

    if cv2.waitKey(DELAY_MSEC) & 0xFF == 27:
        break
    
    cv2.circle(img,(10,10),10,(255,0,0),-1)
    cv2.circle(img,(10,30),3,(255,255,255),-1)
    cv2.putText(img,"Landmarks",(30,20),1,1.0,(255,0,0))
    cv2.putText(img,"Particles",(30,40),1,1.0,(255,255,255))
    cv2.putText(img,"Robot Trajectory(Ground truth)",(30,60),1,1.0,(0,255,0))
    cv2.putText(img,"Robot Trajectory(Predict)",(30,80),1,1.0,(0,0,255))
    cv2.putText(img,"sensor_std_err="+str(sensor_std_err), (30,100),1,1.0,(255,255,255))
    cv2.putText(img,"N="+str(N),(30,120),1,1.0,(255,255,255))
    
    
    drawLines(img, np.array([[10,55],[25,55]]), 0, 255, 0)
    drawLines(img, np.array([[10,75],[25,75]]), 0, 0, 255)


cv2.destroyAllWindows()