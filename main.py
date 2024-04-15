import argparse
from skimage import io
from src.particle_tracking import calculate_trajectories, calculate_particle_radii, approximate_avogadros_number
from src.plotting import plot_trajectories, plot_MSD

def main():
    parser = argparse.ArgumentParser("Particle Tracking of Brownian Motion")
    parser.add_argument("-p", "--path", help="path of video file", type=str)
    parser.add_argument("-f", "--framerate", help="FPS of video", type=int)
    parser.add_argument("-r", "--ratio", help="ratio of pixels to micrometer", type=float)
    parser.add_argument("-t", "--temperature", help="temperature of the sample (as degree celsius)", type=int)
    parser.add_argument("-v", "--viscosity", help="dynamic viscosity of the fluid the particles are in (as mPa*s)", type=float)
    parser.add_argument("-m", "--max_distance", help="maximal movement distance of particles in px", type=int, default=50)
    parser.add_argument("-s", "--save_plots", help="save plots instead of showing them", default=False, action='store_true')

    args = parser.parse_args()

    video = args.path
    framerate = args.framerate
    ratio = args.ratio
    save_plots = args.save_plots
    temperature = args.temperature
    max_distance = args.max_distance   
    dynamic_viscosity = args.viscosity * (10 ** (-3))

    BOLTZMANN_CONSTANT = 1.380649 * (10 ** (-23))
    IDEAL_GAS_CONSTANT = 8.31446261815324


    print("[INFO] Tracking trajectories of particles with the following parameters: ")
    print(f"""
          - video: {video},
          - framerate: {framerate},
          - ratio: {ratio},
          - temperature: {temperature},
          - viscosity: {args.viscosity},
          - max_distance: {max_distance},
          - save_plots: {save_plots}
        """)

    frames = io.imread(video)
    image_size = frames[0].shape

    trajectories, _, squared_displacements = calculate_trajectories(frames, ratio, max_distance=max_distance)
    plot_trajectories(trajectories, image_size, video, save_plot=save_plots)
    plot_MSD(squared_displacements, video, framerate, save_plot=save_plots)
    radii = calculate_particle_radii(squared_displacements, framerate, temperature, dynamic_viscosity, BOLTZMANN_CONSTANT)
    avogadro_approx = approximate_avogadros_number(squared_displacements, radii, framerate, temperature, IDEAL_GAS_CONSTANT, dynamic_viscosity)


if __name__ == "__main__":
   main()