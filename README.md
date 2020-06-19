# GriddedMosaic

![Low res output example](https://raw.githubusercontent.com/dfaker/GriddedMosaic/master/GridOutput.gif)
Makes packed video mosaics and tries to find the one with the lowest reative image resizing.

# Installation

Requires Python 3 with cv2+numpy along with ffmpeg adn mpv being installed on the system.

# Usage

Grid creation happens in multiple stages stages:

## Additon of video clips and parameter input
One or more video files or folders full of video files are passed to makeGrid.py on the command line, the user will them be prompted to input:

- **outputFormat** `webm` or `hqwebm` both .webm outputs but the `webm` option limits the file size to 4M
- **banner** Infomational text to be displayed at the bottom right of the grid on playback, this may be left blank
- **filename** Output filename prefix, this can be left blank and a filename prefix will not be used.
- **targetDuration** The number of seconds the output video grid is to last.
- **postMoveScrollBack** If you choose to cut the input videos this is the number of seconds prior to the scection end the playback will start from when the cut window is moved.
- **maxPerGrid** Maximum number of images to use in the initial grid creation run.

The user will then be prompted with `cut?` answering `n` will simply use the input videos directly in the grid, if the user answers with `y` each file will be shown to the user for scene selection

## Optional cur selection
  
## Layout viewing and selection
## Encoding of final grids
