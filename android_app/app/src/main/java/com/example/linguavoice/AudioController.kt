package com.example.linguavoice

import android.content.Context
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import android.util.Base64
import java.io.File
import java.io.FileOutputStream

class AudioController(private val context: Context) {
    private var recorder: MediaRecorder? = null
    private var player: MediaPlayer? = null
    var currentAudioFile: File? = null
        private set

    fun startRecording() {
        val file = File(context.cacheDir, "user_voice.m4a")
        currentAudioFile = file

        recorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }
    }

    fun stopRecording(): File? {
        return try {
            recorder?.apply {
                stop()
                release()
            }
            recorder = null
            currentAudioFile
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    fun playAudioFromBase64(base64Audio: String) {
        try {
            val audioBytes = Base64.decode(base64Audio, Base64.DEFAULT)
            val tempMp3 = File.createTempFile("ai_voice", ".mp3", context.cacheDir)
            FileOutputStream(tempMp3).use { it.write(audioBytes) }

            player?.release()
            player = MediaPlayer().apply {
                setDataSource(tempMp3.absolutePath)
                prepare()
                start()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun release() {
        recorder?.release()
        player?.release()
    }
}