# clip-cat
This small project allows you to quickly create a single video from multiple Fortnite
clips created by Nvidia Shadowplay.

clip-cat will automagically trim out the overlapping portions from all the videos and
concatenate the clips together and write a new mp4 file with the combined audio/video.


## Install
1. Clone this github project
2. In the project folder, run:
    ```sh
    python -m venv venv
    pip install -r requirements.txt
    ```

## Run
1. In the project folder, activate the venv created during installation.
2. Run:
    ```sh
    python ./main.py <path to your fortnite highlights folder>
    ```
3. Script will take several minutes to complete based on how many videos are being
compiled.  Approximately 30 seconds per video.  Script will create `concatenation.mp4`
in the directory.
