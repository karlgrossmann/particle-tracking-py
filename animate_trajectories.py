import argparse
from skimage import io
from src.particle_tracking import calculate_trajectories
from src.plotting import animate_trajectories

def main():
    parser = argparse.ArgumentParser("Animating Trajectories of Brownian Motion")
    parser.add_argument("-p", "--path", help="path of video file", type=str)
    parser.add_argument("-m", "--max_distance", help="maximal movement distance of particles in px", type=int, default=50)
    parser.add_argument("-b", "--video_as_background", help="enable original video as background", default=False, action='store_true')
    parser.add_argument("-f", "--output_filename", help="filename of the output", default="animated_trajectory.gif", type=str)
    args = parser.parse_args()

    video = args.path
    max_distance = args.max_distance        
    enable_background = args.video_as_background
    output_filename = args.output_filename

    print("[INFO] Animating trajectories of particles with the following parameters: ")
    print(f"""
            - video: {video}, 
            - max_distance: {max_distance}, 
            - enable_background: {enable_background},
            - output_filename: {output_filename}
            """)

    frames = io.imread(video)
    image_size = frames[0].shape

    trajectories, _, _ = calculate_trajectories(frames, 1, max_distance=max_distance)
    animate_trajectories(trajectories, frames, video, image_size, background=enable_background, filename=output_filename)

if __name__ == "__main__":
   main()