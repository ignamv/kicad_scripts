from matplotlib import pyplot as plt
import spiral

data = list(spiral.ellipticalspiral(10, 20, 1, 5, 80))
plt.plot([d[0] for d in data], [d[1] for d in data])
plt.show()
