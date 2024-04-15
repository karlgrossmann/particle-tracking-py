import numpy as np
import matplotlib.pyplot as plt
import os
import imageio
from tqdm import tqdm

def plot_MSD(squared_displacements, video_title, video_fps=10, time_cutoff=1, save_plot=False):
    """Plot the Mean Squared Displacement of all particles in a sequence.

        If the argument `video_fps` isn't passed in, the default framerate of 10 is used.
        If the argument `time_cutoff` isn't passed in, the default length of the time series is used.

    Parameters
    ----------
    squared_displacements : array
        Array containing the squared displacements of all particles over time.
    video_title : str
        The title of the video / frame sequence which was converted. Only used to distinguish various plots.
    video_fps : int
        The framerate of the video used to obtain the squared displacements. 
        Used to calculate the time in seconds.
    time_cutoff : float, optional
        Specifies what fraction of the time series should be used for plotting. 
        Used to cutoff the time series if needed.
    save_plot : bool, optional
        Defines if plot is saved in local folder or just displayed.
    """
    cutoff = int(len(squared_displacements[0]) * time_cutoff)
    squared_displacements = squared_displacements[:,:cutoff]

    msd_in_micrometer = np.mean(squared_displacements, axis=0)
    times = np.array(range(0, len(squared_displacements[0]))) / video_fps

    plt.plot(times, msd_in_micrometer)
    plt.xlabel('time in s')
    plt.ylabel('MSD in µm²')
    plt.title(f'Mean Squared Displacement over Time ({video_title})')

    m, b = np.polyfit(times, msd_in_micrometer, 1)
    plt.plot(times, m*times + b, linestyle='dashed')

    if save_plot:
        plt.savefig('mean_squared_displacement.png', bbox_inches='tight')
        plt.clf()
    else:
        plt.show()

    print(f"[INFO] Plotted mean squared displacement (MSD) for particles in given time series.")

def plot_trajectories(trajectories, image_size, video_title, save_plot=False):
    """Plot all trajectories of the particles in one plot.

    Parameters
    ----------
    trajectories : array
        Array containing the particle trajectories.
    image_size : array
        Array containing the image size as [height, width].
    video_title : str
        The title of the video / frame sequence which was converted. Only used to distinguish various plots.
    save_plot : bool, optional
        Defines if plot is saved in local folder or just displayed.
    """
    for trajectory in trajectories:
        x, y = np.array(trajectory).T
        plt.plot(x, y) 

    plt.xlim(0, image_size[1])
    plt.ylim(0, image_size[0])
    plt.xlabel('width in pixels')
    plt.ylabel('height in pixels')
    plt.title(f'Trajectories of tracked particles ({video_title})')
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')
    plt.gca().invert_yaxis()
    plt.draw()
    if save_plot:
        plt.savefig('particle_trajectories.png', bbox_inches='tight')
        plt.clf()
    else:
        plt.show()

    print(f"[INFO] Plotted trajectories for all tracked particles.")

def animate_trajectories(trajectories, frames, video_title, image_size, background=True, filename='animated_trajectory.gif', tmp_frame_folder='animated_frames'):
    """Animate the evolution of the particles trajectories in a gif file.

    Parameters
    ----------
    trajectories : array
        Array containing the particle trajectories.
    frames : array
        Array containing the frames of the original video file.
    video_title : str
        The title of the video / frame sequence which was converted. Only used to distinguish various plots.
    image_size : array
        Array containing the image size as [height, width].
    background : bool, optional
        Enables plotting the trajectories on the original frames. If disable it will be on white background only.
    filename : str, optional
        Filename of the resulting gif file.
    tmp_frame_folder : str, optional
        Path of a temporary folder containing all the created frame files.
    """
    # Setup folder for temporary files
    dir_path = os.getcwd()
    path = os.path.join(dir_path, tmp_frame_folder)
    if not os.path.isdir(path):
        os.mkdir(path)
    # Draw trajectories on frames and save them seperately
    for i in tqdm(range (len(trajectories[0])), desc='[INFO] Plotting...'):
        # Take frame of video as background if set to true
        if background:
            plt.imshow(frames[i], 'gray')
        for trajectory in trajectories:
            x, y = np.array(trajectory[0:i]).T
            plt.plot(x, y) 
        plt.xlim(0, image_size[1])
        plt.ylim(0, image_size[0])
        plt.xlabel('width in pixels')
        plt.ylabel('height in pixels')
        plt.title(f'Trajectories of tracked particles ({video_title})')
        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        plt.gca().invert_yaxis()
        # Save figure
        plt.savefig(f"{path}/frame_{i}.png", bbox_inches='tight')
        # Clear plot
        plt.clf()

    # Create gif file out of all created frames
    with imageio.get_writer(filename, mode='I') as writer:
        for i in tqdm(range (len(trajectories[0])), desc='[INFO] Creating GIF ...'):
            image = imageio.imread(f"{path}/frame_{i}.png")
            writer.append_data(image)

    print("[INFO] Successfully created an animation of the particles trajectories.")