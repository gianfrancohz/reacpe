import numpy as np

# Array con las constantes del reactor
# beta nuclear
# bi (beta_i/beta)
# lambda_i

Keepin = np.array([ [0.0065],
					[0.033, 0.219, 0.196, 0.395, 0.115, 0.042],
					[0.0124, 0.0305, 0.1110, 0.3010,1.1400, 3.0100]])

Tutle = np.array([  [0.006853],
					[0.038, 0.213, 0.188, 0.407, 0.128, 0.026],
					[0.0127, 0.0317, 0.1150, 0.3110, 1.4000, 3.8700]])

#N08B 28/10/20
Serpent = np.array([  [0.00754],
					[0.03130116, 0.1651111, 0.16215381, 0.45749985, 0.13810823, 0.04582558],
					[0.0124906, 0.0317909, 0.10945, 0.317502, 1.35274, 8.66641]])

np.save('Keepin.npy', Keepin, allow_pickle=True)
np.save('Tutle.npy', Tutle, allow_pickle=True)
np.save('Serpent.npy', Serpent, allow_pickle=True)
