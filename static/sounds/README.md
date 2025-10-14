# Notification Sound

The application uses a notification sound for new orders on the admin dashboard.

## Current Sound File

- `notification.wav` - WAV format notification sound (mixkit-positive-notification-951)

## How It Works

When a new order arrives on the admin dashboard:
1. The system attempts to play `notification.wav`
2. If playback fails, it falls back to a Web Audio API generated beep sound

## Changing the Sound

To use a different notification sound:
1. Replace `notification.wav` with your preferred sound file
2. Keep the filename as `notification.wav` OR
3. Update the audio source in `bufe/templates/bufe/admin/dashboard.html`

## Recommended Settings
- Duration: 0.5-2 seconds
- Volume: Clear but not jarring
- Format: WAV, MP3, or OGG

## Free Sound Resources
You can download free notification sounds from:
- https://freesound.org/
- https://notificationsounds.com/
- https://mixkit.co/free-sound-effects/notification/

