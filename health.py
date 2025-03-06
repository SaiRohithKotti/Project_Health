from flask import Flask, render_template, request, jsonify
import openai
import sounddevice as sd
import scipy.io.wavfile as wav
import os
import json
from datetime import datetime

app = Flask(__name__)

# Set up API keys
openai.api_key = "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"

# Step 1: Record Audio (Simulate Doctor-Patient Interaction)
def record_audio(duration=10, sample_rate=16000, filename="patient_interaction.wav"):
    print("Recording audio... Speak now.")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    wav.write(filename, sample_rate, audio)  # Save as WAV file
    print(f"Audio saved as {filename}")
    return filename

# Step 2: Transcribe Audio to Text (Speech-to-Text)
def transcribe_audio(filename):
    print("Transcribing audio...")
    # Use Whisper API or Google Speech-to-Text here
    # For simplicity, we'll use a mock transcription
    with open(filename, "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    return transcription['text']

# Step 3: Generate Structured Clinical Notes (LLM)
def generate_clinical_notes(transcript):
    print("Generating clinical notes...")
    prompt = f"""
    Convert the following doctor-patient conversation into structured SOAP notes:
    
    Conversation:
    {transcript}

    SOAP Notes:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a medical assistant. Generate structured SOAP notes from the conversation."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

# Step 4: Save Notes to EHR (Mock Integration)
def save_to_ehr(notes):
    print("Saving notes to EHR...")
    # Mock EHR integration (save to a JSON file)
    ehr_data = {
        "patient_id": "12345",
        "notes": notes,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    with open("ehr_record.json", "w") as f:
        json.dump(ehr_data, f, indent=4)
    print("Notes saved to EHR.")

# Flask Routes
@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Clinical Documentation Automation</title>
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #f8f9fa;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            textarea {
                width: 100%;
                height: 150px;
                margin-bottom: 20px;
                resize: none;
            }
            .btn-primary {
                background-color: #007bff;
                border: none;
            }
            .btn-primary:disabled {
                background-color: #6c757d;
            }
            .status {
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-4">Clinical Documentation Automation</h1>
            <div class="card shadow-sm">
                <div class="card-body">
                    <button id="recordBtn" class="btn btn-primary w-100">Record Conversation</button>
                    <div class="status text-center mt-3" id="status"></div>
                </div>
            </div>

            <div class="card shadow-sm mt-4">
                <div class="card-body">
                    <h2>Transcript</h2>
                    <textarea id="transcript" class="form-control" readonly></textarea>
                </div>
            </div>

            <div class="card shadow-sm mt-4">
                <div class="card-body">
                    <h2>Clinical Notes</h2>
                    <textarea id="clinicalNotes" class="form-control" readonly></textarea>
                </div>
            </div>
        </div>

        <!-- Bootstrap JS and dependencies -->
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.min.js"></script>
        <script>
            const recordBtn = document.getElementById("recordBtn");
            const transcriptTextarea = document.getElementById("transcript");
            const clinicalNotesTextarea = document.getElementById("clinicalNotes");
            const statusDiv = document.getElementById("status");

            recordBtn.addEventListener("click", async () => {
                recordBtn.disabled = true;
                recordBtn.textContent = "Recording...";
                statusDiv.textContent = "Recording audio...";

                try {
                    // Step 1: Record audio
                    const recordResponse = await fetch("/record", { method: "POST" });
                    const recordData = await recordResponse.json();
                    if (recordData.status === "success") {
                        statusDiv.textContent = "Transcribing audio...";

                        // Step 2: Transcribe audio
                        const transcribeResponse = await fetch("/transcribe", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ audio_file: recordData.audio_file })
                        });
                        const transcribeData = await transcribeResponse.json();
                        if (transcribeData.status === "success") {
                            transcriptTextarea.value = transcribeData.transcript;
                            statusDiv.textContent = "Generating clinical notes...";

                            // Step 3: Generate clinical notes
                            const notesResponse = await fetch("/generate_notes", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ transcript: transcribeData.transcript })
                            });
                            const notesData = await notesResponse.json();
                            if (notesData.status === "success") {
                                clinicalNotesTextarea.value = notesData.clinical_notes;
                                statusDiv.textContent = "Notes generated and saved to EHR!";
                            }
                        }
                    }
                } catch (error) {
                    console.error("Error:", error);
                    statusDiv.textContent = "An error occurred. Please try again.";
                } finally {
                    recordBtn.disabled = false;
                    recordBtn.textContent = "Record Conversation";
                }
            });
        </script>
    </body>
    </html>
    """

@app.route("/record", methods=["POST"])
def record():
    # Step 1: Record audio
    audio_file = record_audio(duration=10)  # Record 10 seconds of audio
    return jsonify({"status": "success", "audio_file": audio_file})

@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.json.get("audio_file")
    # Step 2: Transcribe audio to text
    transcript = transcribe_audio(audio_file)
    return jsonify({"status": "success", "transcript": transcript})

@app.route("/generate_notes", methods=["POST"])
def generate_notes():
    transcript = request.json.get("transcript")
    # Step 3: Generate clinical notes
    clinical_notes = generate_clinical_notes(transcript)
    # Step 4: Save notes to EHR
    save_to_ehr(clinical_notes)
    return jsonify({"status": "success", "clinical_notes": clinical_notes})

if __name__ == "__main__":
    app.run(debug=True)