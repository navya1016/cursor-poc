from youtube_transcript_api import YouTubeTranscriptApi

"""Example script for downloading YouTube transcripts."""

def download_transcript(video_id: str, output_path: str) -> None:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in transcript:
            f.write(row["text"] + "\n")


if __name__ == "__main__":
    example_video_id = "VIDEO_ID"
    output_md = "../research/youtube-transcripts/example-video-1.md"
    download_transcript(example_video_id, output_md)
