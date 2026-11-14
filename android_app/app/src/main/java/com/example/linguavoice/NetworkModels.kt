package com.example.linguavoice

import com.google.gson.annotations.SerializedName

data class Correction(
    @SerializedName("original") val original: String,
    @SerializedName("correction") val correction: String,
    @SerializedName("explanation") val explanation: String
)

data class VoiceTurnResponse(
    @SerializedName("status") val status: String,
    @SerializedName("user_transcript") val userTranscript: String,
    @SerializedName("ai_response") val aiResponse: String,
    @SerializedName("corrections") val corrections: List<Correction>,
    @SerializedName("audio_base64") val audioBase64: String?
)

data class UiMessage(
    val text: String,
    val isUser: Boolean,
    val corrections: List<Correction> = emptyList()
)