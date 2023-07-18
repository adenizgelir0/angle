# angle
A program that can solve euclidian geometry questions
## How does it work?
The restrictions and measurements recieved via the ui are first transformed into a set of equations and inequalies in the cartasien plane. Then a cost function measuring the deviatiaon from these restrictors is constructed from the equations. Then the local minimum of the cost function is found in the bounds specified by the inequalities. This process is expected to yield a numeric answer very close to the actual answer up to 4-5 decimal places. After this approximation is found, Ries is used to guess the closed form of the decimal answer.
## Sample Video
[![test](http://img.youtube.com/vi/OOwJQDwlM3U/0.jpg)](http://www.youtube.com/watch?v=OOwJQDwlM3U "9")
