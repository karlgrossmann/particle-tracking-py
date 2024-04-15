import numpy as np
from timeit import default_timer as timer
from datetime import timedelta
from skimage.measure import label, regionprops

def _frames_to_black_and_white(frames, threshold=200):
    """Converts all frames to black (0) and white (255) pixels only.

    If the argument `threshold` isn't passed in, the default threshold
    of 200 is used.

    Parameters
    ----------
    frames : array
        Array of frames which should be converted.
    threshold : int, optional
        The cutoff brightness of pixels. Everything below will be turned black (0), everything above white (255).
    """
    start_time = timer()

    for frame in frames:
        threshold_indices = frame < threshold
        frame[threshold_indices] = 0

        threshold_indices = frame >= threshold
        frame[threshold_indices] = 255

    end_time = timer()

    print(f"[INFO] Converted all frames to black and white pixels only. [Execution Time: {timedelta(seconds=end_time-start_time)}]")

    return frames


def _extract_particle_centers(frames):
    """Generates coordinates of centers of particles in the image sequence.

    Parameters
    ----------
    frames : array
        Array of frames from which to extract the particle centers.
    """
    start_time = timer()

    particle_sequence = []
    max_num_particles = 0

    for frame in frames:
        particles = []

        labeled_components = label(frame)
        regions = regionprops(labeled_components)
        if len(regions) > max_num_particles: max_num_particles = len(regions)
   
        for blob in regions:
            y, x = blob.centroid
            particles.append([x,y])
        
        particle_sequence.append(particles)

    end_time = timer()

    print(f"[INFO] Calculated coordinates of particles. [Execution Time: {timedelta(seconds=end_time-start_time)}]")
    print(f"[INFO] Maximal particle number in the frame sequence is {max_num_particles}.")
    
    return particle_sequence, max_num_particles


def _calc_dist(point1, point2):
    """Calculates the distance between two points in 2D space.

    Parameters
    ----------
    point1 : array
        Array with x and y coordinate of first point.
    point2 : array
        Array with x and y coordinate of second point.
    """
    return (np.sqrt((point2[0] - point1[0] )**2 + (point2[1] - point1[1]) ** 2))


def calculate_trajectories(frames, pixel_micrometer_ratio, max_distance=50):
    """Calculates the particle trajectories starting from the first frame. Also extracts the 
       distance and squared displacements of the particles from frame to frame.

        If the argument `max_distance` isn't passed in, the default distance of 50 is used.

        Note: This algorithm is not efficient! It is just a quick and dirty implementation, enough for the original purpose.

    Parameters
    ----------
    frames : array
        Array of frames from which to extract the information from.
    pixel_micrometer_ratio : float
        The ratio of pixels to micrometers. Says how many micrometers are displayed by one pixel. 
        Used to calculate the distances and MSD in micrometers.
    max_distance : int, optional
        The maximum distance a particle will move during one timestep (between two frames).
    """
    frames = _frames_to_black_and_white(frames)
    particle_sequence, max_num_particles = _extract_particle_centers(frames)

    start_time = timer()

    # Get number of particles in first frame
    num_particles = len(particle_sequence[0])
    # Get sequence length
    sequence_length = len(particle_sequence)
    # Create array for distances and trajectories
    distances = np.zeros(shape=(num_particles, sequence_length - 2))
    trajectories = np.zeros(shape=(num_particles, sequence_length - 1, 2))
    squared_displacements = np.zeros(shape=(num_particles, sequence_length - 2))

    # Iterate over the number of particles
    for i in range(0, num_particles):
        # Get current coordinates of particle
        current_coordinates = particle_sequence[0][i]
        # Go through all the images
        for image_idx in range(1, sequence_length):
            #print(f"[INFO] Particle {i}: {current_coordinates} [{image_idx}]")
            trajectories[i][image_idx - 1] = current_coordinates
            # Check for array out of bounce
            if (image_idx + 1) >= sequence_length:
                break
            # Reset minimum distance
            min_distance = 99999
            # Reset next coordinates
            next_coords = []
            # Go through all particles of the next image
            for j in range(0, len(particle_sequence[image_idx + 1])):
                # Calculate the distance between both particles
                distance = _calc_dist(current_coordinates, particle_sequence[image_idx + 1][j])
                # If it lower than the current min distance, overwrite distance and next_coords
                if distance < min_distance:
                    min_distance = distance
                    next_coords = particle_sequence[image_idx + 1][j]
                
            if min_distance < max_distance:
                # Save distance in an array
                distances[i][image_idx - 1] = min_distance * pixel_micrometer_ratio
                # Override current coordinate of particle
                current_coordinates = next_coords
                # Save squared displacement of particle
                squared_displacements[i][image_idx - 1] = (_calc_dist(current_coordinates, particle_sequence[0][i]) * pixel_micrometer_ratio) ** 2
            else:
                # Particle migth be out of the image, save None and don't overrite coordinates
                distances[i][image_idx - 1] = None
    
    end_time = timer() 
    print(f"[INFO] Calculated all {num_particles} particle trajectories. [Execution Time: {timedelta(seconds=end_time-start_time)}]")
    
    if max_num_particles > num_particles:
        print(f"[WARNING] There are {max_num_particles - num_particles} particles which are not tracked. They do not appear in the first frame.")

    return trajectories, distances, squared_displacements


def _celsius_to_kelvin(celcius_temp):
    """Converts the unit degree celsius to Kelvin.

    Parameters
    ----------
    celcius_temp : int / float
        Temperature of the sample in Degree Celsius.
    """
    return 273.15 + celcius_temp

def calculate_particle_radii(
        squared_displacements, 
        video_fps=10,
        temperature=25, 
        dynamic_viscosity=(8.90 * (10 ** (-4))), 
        boltzmann_constant=(1.380649 * (10 ** (-23)))):
    """Calculates the particle radii of the particles present in the time series.

        If the argument `video_fps` isn't passed in, the default framerate of 10 is used.
        If the argument `temperature` isn't passed in, the default temperature of 25 is used.
        If the argument `dynamic_viscosity` isn't passed in, the default value for water at 25 degree will be used.
        If the argument `boltzmann_constant` isn't passed in, the default Boltzmann constant will be used. 

    Parameters
    ----------
    squared_displacements : array
        Array containing the squared displacements of all particles over time.
    video_fps : int
        The framerate of the video used to obtain the squared displacements. 
        Used to calculate the time in seconds.
    temperature : int / float
        Temperature of the sample in Degree Celsius.
    dynamic_viscosity : float
        The value of the dynamic viscosity of the solution.
    boltzmann_constant : float
        The value for the Boltzmann constant.
    """
    times_in_s = np.array(range(1, len(squared_displacements[0]) + 1)) / video_fps
    msd_in_micrometer = np.mean(squared_displacements, axis=0)  # Unit: µm^2
    msd_in_meter = msd_in_micrometer * (10 ** (-12))            # Unit: m^2
    diffusion_coefficient = msd_in_meter / (times_in_s * 4)     # Unit: m^2 / s
    temperature_in_kelvin = _celsius_to_kelvin(temperature)      # Unit: K

    radii = ((boltzmann_constant * temperature_in_kelvin) / (6 * np.pi * dynamic_viscosity * diffusion_coefficient))
    mean_radius = np.mean(radii) * (10 ** 6)
    print(f"[INFO] Mean radius of particles of sample: {mean_radius} µm")

    return radii

def approximate_avogadros_number(
        squared_displacements, 
        radii, 
        video_fps=10, 
        temperature=25, 
        ideal_gas_constant=8.31446261815324,
        dynamic_viscosity=(8.90 * (10 ** (-4)))):
    """Approximates Avogadro's Number using the data present in the time series.

        If the argument `video_fps` isn't passed in, the default framerate of 10 is used.
        If the argument `temperature` isn't passed in, the default temperature of 25 is used.
        If the argument `dynamic_viscosity` isn't passed in, the default value for water at 25 degree will be used.
        If the argument `ideal_gas_constant` isn't passed in, the default constant will be used. 

    Parameters
    ----------
    squared_displacements : array
        Array containing the squared displacements of all particles over time.
    radii : array
        Array containing the radii of the particles in the time series.
    video_fps : int, optional
        The framerate of the video used to obtain the squared displacements. 
        Used to calculate the time in seconds.
    temperature : int / float
        Temperature of the sample in Degree Celsius.
    ideal_gas_constant : float
        The value of the ideal gas constant.
    boltzmann_constant : float
        The value for the Boltzmann constant.
    """

    times_in_s = np.array(range(1, len(squared_displacements[0]) + 1)) / video_fps
    temperature_in_kelvin = _celsius_to_kelvin(temperature)      # Unit: K
    msd_in_micrometer = np.mean(squared_displacements, axis=0)  # Unit: µm^2
    msd_in_meter = msd_in_micrometer * (10 ** (-12))            # Unit: m^2

    avogadros_number = ((ideal_gas_constant * temperature_in_kelvin * times_in_s) / (3 * np.pi * dynamic_viscosity * radii * msd_in_meter))
    approx_avogadros_number = np.mean(avogadros_number)

    print(f"[INFO] Avogadro's Number (approximation): {approx_avogadros_number} mol-1")

    return approx_avogadros_number