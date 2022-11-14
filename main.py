import os
import time
from typing import Dict

from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np

# Allow for some margin of error between when a clip is written to disk and when its
# actual end-time is in real-time / game-time
SLOP_TIME = 1.1


class ClipConcatter:
    def __init__(self, clip_dir: str):
        print(f"Initialize ClipConcatter with dir {clip_dir}")
        self.clip_dir = clip_dir
        self.clips: Dict[str, VideoFileClip] = {}

        # Create moviepy clips of all mp4 files in directory
        for filename in os.listdir(clip_dir):
            if filename.startswith("Fortnite") and filename.endswith("mp4"):
                self.clips[filename] = VideoFileClip(
                    os.path.join(self.clip_dir, filename)
                )

        self.time_saved = 0.0

    def clip_abspath(self, clip: VideoFileClip):
        return os.path.join(self.clip_dir, clip.filename)

    def timestamp_endpoints_of_clip(self, clip: VideoFileClip):
        end = os.path.getmtime(self.clip_abspath(clip))
        start = end - clip.duration

        return start, end

    def clip_is_complete_subset(
        self, former_clip: VideoFileClip, latter_clip: VideoFileClip
    ):
        former_start, former_end = self.timestamp_endpoints_of_clip(former_clip)
        latter_start, latter_end = self.timestamp_endpoints_of_clip(latter_clip)

        end_inside = former_end < (latter_end + SLOP_TIME)
        start_inside = former_start > (latter_start - SLOP_TIME)

        return start_inside and end_inside

    def get_start_inspection_timestamp(
        self, former_clip: VideoFileClip, latter_clip: VideoFileClip
    ):
        former_start, former_end = self.timestamp_endpoints_of_clip(former_clip)
        latter_start, latter_end = self.timestamp_endpoints_of_clip(latter_clip)

        print(
            f"Former clip runs from {time.ctime(former_start)} to "
            f"{time.ctime(former_end)}"
        )
        print(
            f"Latter clip runs from {time.ctime(latter_start)} to "
            f"{time.ctime(latter_end)}"
        )

        if latter_start >= (former_end + SLOP_TIME):
            return None

        print(f"Overlap size around {former_end - latter_start} seconds")
        return (latter_start - former_start) - SLOP_TIME

    def trim_clip(self, clip_a: VideoFileClip, clip_b: VideoFileClip) -> VideoFileClip:
        """
        Use clip_b to see if there's an overlap in clip_a
        - assumes clip_b is chronologically later than clip_a
        - if there's an overlap, trim the overlapping end off of clip_a and return it

        Overlap is found by comparing the first frame of the second clip (clip_b) to
        frames in first clip (clip_a)
        """
        print(f"Try trim:\n\tclip_a = {clip_a.filename}\n\tclip_b = {clip_b.filename}")

        # We can reduce the amount frames we need to look at by approximating
        # the location of the first overlapping frame using duration and start/end times
        # of the clips
        overlap_start = self.get_start_inspection_timestamp(clip_a, clip_b)
        if overlap_start is None:
            print("No overlap between clips")
            return clip_a

        num_frames_not_under_inspection = int(clip_a.fps * overlap_start)
        print(
            f"Overlap starts near {overlap_start}: skipping inspection of "
            f"{num_frames_not_under_inspection} frames"
        )

        clip_b_frames = clip_b.iter_frames()
        clip_b_first_frame = next(clip_b_frames)

        for inspection_frame_index, frame in enumerate(clip_a.iter_frames()):
            if inspection_frame_index <= num_frames_not_under_inspection:
                continue
            if np.array_equal(frame, clip_b_first_frame, equal_nan=True):
                print(
                    f"clip_a frame #{inspection_frame_index} is the same as first "
                    "frame of clip_b"
                )
                break
        else:
            print("Could not find a matching frame during inspection")
            return clip_a

        first_overlapping_frame_index = inspection_frame_index
        print(f"{first_overlapping_frame_index=}")

        clip_a_stop_time = first_overlapping_frame_index / clip_a.fps
        print(f"{clip_a_stop_time=}")

        self.time_saved += clip_a.duration - clip_a_stop_time
        return clip_a.subclip(0, clip_a_stop_time)

    def create_concatenation(self):
        print("Concatenating clips...")
        if not self.clips:
            print("No mp4 fortnite files in folder!")
            return

        completed_clips = []
        prev_filename = None
        for filename, clip in self.clips.items():
            print(
                f"----- Looking at {filename}; {clip.duration} seconds; "
                f"{clip.fps} fps ------"
            )
            if prev_filename is None:
                print("This is the first clip, doing nothing")
                prev_filename = filename
                continue

            previous_clip = self.clips[prev_filename]
            if self.clip_is_complete_subset(previous_clip, clip):
                # there is no unique content in the previous_clip, don't include it
                continue

            completed_clips.append(self.trim_clip(previous_clip, clip))

            prev_filename = filename
            print()

        # add final clip in folder to concat list
        completed_clips.append(clip)

        final_clip = concatenate_videoclips(completed_clips)
        print(f"Creating concatenated clip; {final_clip.duration} @ {final_clip.fps}")
        final_clip.write_videofile(os.path.join(self.clip_dir, "concatenation.mp4"))

        # cleanup
        for _, clip in self.clips.items():
            clip.close()

        final_clip.close()

    def list_info(self):
        for filename, clip in self.clips.items():
            print(
                f"----- Looking at {filename}; {clip.duration} seconds; "
                f"{clip.fps} fps ------"
            )

        # cleanup
        for _, clip in self.clips.items():
            clip.close()


def create(dir: str):
    concatter = ClipConcatter(os.path.abspath(dir))
    concatter.create_concatenation()

    print(f"Trimmed a total of {concatter.time_saved} seconds!")


def list_clips(dir: str):
    concatter = ClipConcatter(os.path.abspath(dir))
    concatter.list_info()


if __name__ == "__main__":
    print("You can ignore the 'File Not Found' message")
    from fire import Fire

    Fire({"create": create, "list": list_clips})
