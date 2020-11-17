import numpy as np

# Array con las constantes del reactor
# Beta_eff, Lambda*, form factor, Diven and efot
# Por ahora solo se usa los dos primeros

# N08B 28/10/20
constantes = np.array( [0.00754,
						0.0066048,
						1.0,
						0.7962,
						0.3]) 

np.save('RP10_N08.npy', constantes)