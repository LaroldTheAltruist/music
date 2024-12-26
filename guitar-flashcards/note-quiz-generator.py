import random
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
# import numpy as np
from moviepy import AudioFileClip, CompositeAudioClip, CompositeVideoClip
from moviepy import concatenate_videoclips, concatenate_audioclips
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.fx import MultiplyVolume

SHARP_SIGN = '\u266F'
FLAT_SIGN = '\u266D'
FONT_FILE = './NotoMusic-Regular.ttf'
CLICK_SOUND_PATH = './click.wav'

# Step 1: Generate Random Notes
'''
NOTES = [
    'Ab', 'A', 'A#',
    'Bb', 'B', 'B#',
    'Cb', 'C', 'C#',
    'Db', 'D', 'D#',
    'Eb', 'E', 'E#',
    'Fb', 'F', 'F#',
    'Gb', 'G', 'G#',
]
'''
NOTES = ['B#', 'C', 'D', 'E']

def generate_note_sequence(num_notes):
    sequence = []
    # Manually drop in first two notes. Prevents having to constantly check to
    # see if we're far enough in that it's safe to reference -x as an index.
    unique_pair = random.sample(NOTES, 2)
    sequence.append(unique_pair[0])
    if num_notes == 1:
        return sequence

    sequence.append(unique_pair[1])
    for _ in range(num_notes - 2):
        # Avoid repeats within span of 2.
        # Construct list sans the most recent two notes.
        #avoid_notes = [sequence[-1], sequence[-2]]
        avoid_notes = [sequence[-1]]
        possible_notes = [note for note in NOTES if note not in avoid_notes]
        note = random.choice(possible_notes)
        sequence.append(note)
    return sequence

# Step 2: Generate Image Frames for each possible note
# One time use: We now have all the images (21 notes)
def create_note_images():
    img_size = (1920, 1080)
    for note in NOTES:
        img = Image.new('RGB', img_size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT_FILE, 600)
        
        # Translate sharps and flats for both display and file paths
        filepath = note.replace('#', '_sharp').replace('b', '_flat') + '.png'
        drawn_note = note.replace('#', SHARP_SIGN).replace('b', FLAT_SIGN)
        
        # Draw the note excluding the sharp sign
        base_note = drawn_note.replace(SHARP_SIGN, "").replace(FLAT_SIGN, "")
        bbox = draw.textbbox((0, 0), base_note, font=font)
        text_width = bbox[2] - bbox[0]  # Calculate width from bbox
        text_height = bbox[3] - bbox[1]  # Calculate height from bbox
        position = ((img_size[0] - text_width) // 2,
                    -100)
#                    (img_size[1] - text_height) // 5)
        
        # Draw the base note
        draw.text(position, base_note, fill="black", font=font)

        # If note has a sharp sign, render it separately with vertical offset
        if '#' in note:
            # Draw sharp sign with offset
            sharp_pos = (position[0] + text_width, position[1] - 240)
            draw.text(sharp_pos, SHARP_SIGN, fill="black", font=font)
        
        # If the note has a flat sign, render it normally
        if 'b' in note:
            flat_pos = (position[0] + text_width, position[1] - 105)
            draw.text(flat_pos, FLAT_SIGN, fill="black", font=font)

        img.save('./images/' + filepath)

# Step 3: Generate Spoken Audio
# One time use: We now have all 21 audio files of spoken note names
def generate_audio():
    notes = [
        'A flat', 'A', 'A sharp',
        'B flat', 'B', 'B sharp',
        'C flat', 'C', 'C sharp',
        'D flat', 'D', 'D sharp',
        'E flat', 'E', 'E sharp',
        'F flat', 'F', 'F sharp',
        'G flat', 'G', 'G sharp',
    ]
    for note in notes:
        filename = note.replace(' ', '_')
        output_path = f'./audio/{filename}.mp3'

        # Generate and save the audio
        tts = gTTS(text=note, lang='en')
        tts.save(output_path)
        print(f'{note} generated')
        
# Step 4: Combine Frames and Audio into a Video
def create_video(note_sequence, output_video, frame_duration=2.0):
    # Turns out, easier to specify frame duration. BPM gets more
    # restrictive, and we usually end up needing to reverse
    # engineer the math back to frame duration.
    # FWIW:
    # BPM    Seconds per frame
    #  60 -> 4
    # 120 -> 2
    # 240 -> 1
    clips = []
    for note in note_sequence:
        filename = note.replace('#', '_sharp').replace('b', '_flat')
        img_path = f'./images/{filename}.png'
        audio_path = f'./trimmed_audio/{filename}.wav'
        # Create Image Clip
        img_clip = ImageClip(img_path, duration=frame_duration)

        ### Construct all audio for a single flashcard...
        # Load spoken name of note.
        note_audio = AudioFileClip(audio_path)

        # Load a metronome click, then shorten it to 0.1 seconds
        tmp_audio = AudioFileClip(CLICK_SOUND_PATH).subclipped(0, 0.1)
        click_audio = tmp_audio.with_volume_scaled(0.1)
        click_under_voice = tmp_audio.with_volume_scaled(0.03)
        flashcard_audio = CompositeAudioClip(
            [
                note_audio,
                click_under_voice,
                click_audio.with_start(frame_duration / 4),
                click_audio.with_start(frame_duration / 2),
                click_audio.with_start(3 * (frame_duration / 4)),
            ]
        )

        # Add the audio we constructed to the image (video) clip
        img_clip.audio = flashcard_audio

        # Add to our array of flashcards
        clips.append(img_clip)

    # Debug here. How many clips do we have?
    print(f'Num of clips: {len(clips)}')
    # Concatenate all the image clips
    full_video = concatenate_videoclips(clips)
    # Write the video file
    full_video.write_videofile(output_video, fps=24,
                          codec="libx264", audio_codec="aac")

# Step 5: Run the Program
if __name__ == "__main__":
    sequence = generate_note_sequence(30)
    with open('test-notes.txt', 'w') as f:
        f.write(', '.join(sequence))
    create_video(sequence, './test.mp4')
