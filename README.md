# Parcticle-Filter

## Rerference
代码源自[__Robotics with ROS__](http://ros-developer.com/2019/04/10/parcticle-filter-explained-with-python-code-from-scratch/)

## Particle Filtering（粒子滤波）
一种在已知环境及运动的情境下，计算当前状态的算法。  
1.基于之前状态以及本次运动，预测当前状态。  
2.根据测量值（与landmark的距离）重新分配权重。  
3.重采样，更新粒子。  

***

## 代码改造
### 1.基于particles的位置，计算最终定位robot的唯一位置并输出到屏幕上  
直接在重新分配权重之后计算`particles`中心  
添加函数`getRobotPosition()`计算重心：  
```python
# "simple_particle_filter_norm.py" line:30
def getRobotPosition(particles):
    x = np.mean(particles[:, 0])
    y = np.mean(particles[:, 1])
    return x, y
```
函数`mouseCallBack()`调用`update()`后添加：  
```python
# "simple_particle_filter_norm.py" line:101
robot_x, robot_y = getRobotPosition(particles)
robot_pos = np.vstack((robot_pos,np.array([robot_x, robot_y])))
```  
在绘图部分添加代码以绘制预测轨迹（红色线条）：
```python
# "simple_particle_filter_norm.py" line:178
drawLines(img, robot_pos, 0, 0, 255)
cv2.putText(img,"Robot Trajectory(Predict)",(30,80),1,1.0,(0,0,255))
```
运行结果截图：  
![q-1.jpg](https://i.loli.net/2020/03/02/skPQBrxvhNMDwjW.jpg) 
#### 更多：  
+ 计算robot位置既可以在`update()`之后，也可以在重置权重之后
+ 由于最开始particles位置还未进行更新，所以第一次robot的预测值近与画面中央

***

### 2.修改weights的分布为帕累托分布  
在函数`update()`中将正态分布函数`scipy.stats.norm.pdf()`替换为帕累托函数`scipy.stats.pareto.pdf`
```python
# "simple_particle_filter_pareto.py" line:108
weights *= scipy.stats.pareto.pdf(z[i], 3, distance, R) 
```  
`scipy.stats.pareto.pdf(x, b, loc, scale)` : `b`为形状参数
运行结果截图：  
![q-2-1.jpg](https://i.loli.net/2020/03/02/zsnaM4vN1G35qiD.jpg) 
  
效果很不好，尝试替换为广义帕累托函数`scipy.stats.genpareto.pdf(x, b, loc, scale)`  
```python
# "simple_particle_filter_pareto.py" line:109
weights *= scipy.stats.genpareto.pdf(z[i], 3, distance, R) 
```
运行结果截图：  
![q-2-2.jpg](https://i.loli.net/2020/03/02/4vbrmDejlSiVyFz.jpg)

#### 更多：  
+ 直接采用帕累托分布，效果很差，猜想如下：帕累托分布中，随机变量在1的概率太大，导致权重更新时很多并没有有效地进行权重更新。
+ 这里采用`scipy.stats.genpareto.pdf`函数，因为对帕累托分布只有初步的了解，在经历`scipy.stats.pareto.pdf`测试情况很不理想的情况下，尝试了广义帕累托分布，其中原理有待进一步学习。
+ 在测试中，沿用了正态分布的`loc`与`scale`参数，参数都需要进一步测试。
+ 相较于正态分布，帕累托分布中，在`robot`水平或垂直移动时，`particle`的分布更加“细”。
![q-2-3.jpg](https://i.loli.net/2020/03/02/idH5SsNkmL1wGvx.jpg)
***

### 3.为`landmark`和`robot`之间的距离增加随机误差  
在原代码中，计算`landmark`与`robot`之间距离时，已经添加了随机误差  
```python
# "simple_particle_filter_norm.py" line:62
zs = (np.linalg.norm(landmarks - center, axis=1) + (np.random.randn(NL) * sensor_std_err))
```
将`sensor_std_err`分别设置为`5`, `25`, `50`进行对比（`weights`为正态分布）
![q-3-1.jpg](https://i.loli.net/2020/03/02/Bg9yc5LtdUfQZCH.jpg)
可以发现，误差越大，定位的轨迹越不稳定。

\* `paticles`和`landmark`之间的距离同样也可能产生误差，可以使用类似的代码进行模拟
***
### 4.尝试消除误差对结果的影响
#### 4.1 改变`paticle`个数
将`paticle`个数改为1600,4000个，测试  
![q-4-1.jpg](https://i.loli.net/2020/03/02/sqnVOvob4x9hDjT.jpg)
观察发现并没有显著提升，而且将`paticle`个数增加到4000个时，测试过程出现了明显卡顿。  
  
#### 4.2 其他想法  
多次测量`landmark`和`robot`之间的距离以减小误差。