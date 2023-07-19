# angle
A program that can solve euclidian geometry questions
## How does it work?
The restrictions and measurements received via the ui are first transformed into sets of equations and inequalities in the cartesian plane. Then a cost function measuring the deviations from these restrictions is constructed from the equations. Then the local minimum of the cost function is found in the bounds specified by the inequalities. This process is expected to yield a numeric answer very close to the actual answer up to 4-5 decimal places. After this approximation is found, [Ries](http://www.mrob.com/pub/ries/) is used to guess the closed form of the decimal answer.
## Sample Video
[![test](http://img.youtube.com/vi/OOwJQDwlM3U/0.jpg)](http://www.youtube.com/watch?v=OOwJQDwlM3U "9")
