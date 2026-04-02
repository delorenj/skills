---
name: fireflies
description: Fireflies.ai transcription API behavior, GraphQL schema, webhook patterns, and known quirks. Use when working with Fireflies uploads, webhooks, transcript fetching, or debugging transcription issues regardless of which pipeline or workflow is consuming the API.
---

# Fireflies.ai API Reference

## API Endpoint

`https://api.fireflies.ai/graphql` (GraphQL only, no REST)

Auth: `Authorization: Bearer <FIREFLIES_API_KEY>`

## Upload Flow

### `uploadAudio` Mutation

```graphql
mutation($input: AudioUploadInput) {
  uploadAudio(input: $input) { success title message }
}
```

Input fields:
- `url` (required): Publicly accessible audio/video URL (presigned S3/MinIO works)
- `title`: Display name in Fireflies dashboard
- `webhook`: URL to POST when transcription completes
- `client_reference_id`: Opaque string passed back in webhook callbacks. Use this for correlation.

Response only returns `{ success, title, message }`. **No meeting ID is returned.** You cannot poll by ID after upload. You must rely on webhooks.

## Webhook Behavior (Critical)

Fireflies sends **progressive webhooks** during transcription, not a single callback on completion.

For a 70-minute recording, expect 50-150+ webhook POSTs over several minutes. Each webhook:
- Has a **different `meetingId`** (not the same ID repeated)
- Represents an incrementally longer portion of the transcript
- Early webhooks: partial (e.g., 0.8 min, 9 sentences)
- Final webhook: complete transcript (e.g., 70 min, 600+ sentences)

Webhook payload shape:
```json
{
  "meetingId": "01KN2PQWPJYYAPVQD2FX8GVKCM",
  "clientReferenceId": "<your client_reference_id from upload>",
  "eventType": "Transcription completed"
}
```

**You must debounce webhooks by `clientReferenceId`.** Processing every webhook produces hundreds of duplicate/partial transcript files.

Recommended debounce: 2 minutes of no new webhooks for a given `clientReferenceId`, then fetch the transcript using the most recent `meetingId`.

## Transcript Query

```graphql
query Transcript($transcriptId: String!) {
  transcript(id: $transcriptId) {
    id title date dateString duration
    transcript_url audio_url video_url
    host_email organizer_email privacy
    meeting_link calendar_id calendar_type
    participants
    speakers { name }
    sentences {
      index speaker_name speaker_id
      text raw_text start_time end_time
      ai_filters { task pricing metric question date_and_time text_cleanup sentiment }
    }
    user { user_id email name num_transcripts minutes_consumed is_admin }
    meeting_attendees { displayName email }
    summary { overview short_summary }
    meeting_info { fred_joined silent_meeting summary_status }
  }
}
```

The `sentences` array is the authoritative transcript content. Each sentence has speaker attribution and timestamps.

## Known Quirks

- `duration` field is in **minutes** (float), not seconds
- `date` is a Unix timestamp in milliseconds
- Speaker names are generic (`0`, `1`, `2`) unless Fireflies has prior speaker data
- Long uploads (>30 min) trigger the progressive webhook storm described above
- Short uploads (<10 min) typically get 1-3 webhooks total
- The `summary` field may be null if Fireflies' AI summary isn't ready yet
- `meeting_info.summary_status` can indicate whether summary generation is complete
