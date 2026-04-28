package com.knifelevel.hello

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import kotlin.math.PI
import kotlin.math.sin

data class TonePreset(val label: String, val freq: Float)

val HIGH_TONE_OPTIONS = listOf(
    TonePreset("Soft",  523f),   // C5
    TonePreset("Mid",   660f),   // E5  ← default
    TonePreset("High",  784f),   // G5
    TonePreset("Sharp", 1047f),  // C6
)

val LOW_TONE_OPTIONS = listOf(
    TonePreset("Deep",  220f),   // A3
    TonePreset("Low",   330f),   // E4
    TonePreset("Warm",  440f),   // A4  ← default
    TonePreset("Clear", 523f),   // C5
)

fun defaultHighToneFreq() = HIGH_TONE_OPTIONS[1].freq  // 660 Hz
fun defaultLowToneFreq()  = LOW_TONE_OPTIONS[2].freq   // 440 Hz

/**
 * Plays a continuous looped sine-wave tone. Mellow: low amplitude, pure sine, no harmonics.
 * Integer Hz frequencies → 1-second buffer contains exact cycles, loop is seamless.
 */
class TonePlayer {
    private var audioTrack: AudioTrack? = null
    private var currentFreq: Float = 0f

    fun play(frequency: Float) {
        if (currentFreq == frequency && audioTrack?.playState == AudioTrack.PLAYSTATE_PLAYING) return
        stop()
        currentFreq = frequency

        val sampleRate = 44100
        val numSamples = sampleRate  // 1 second
        val amplitude = (Short.MAX_VALUE * 0.18).toInt()
        val buffer = ShortArray(numSamples) { i ->
            (amplitude * sin(2.0 * PI * frequency * i / sampleRate)).toInt().toShort()
        }

        val track = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build()
            )
            .setBufferSizeInBytes(numSamples * 2)
            .setTransferMode(AudioTrack.MODE_STATIC)
            .build()

        track.write(buffer, 0, numSamples)
        track.setLoopPoints(0, numSamples, -1)
        track.play()
        audioTrack = track
    }

    fun stop() {
        audioTrack?.stop()
        audioTrack?.release()
        audioTrack = null
        currentFreq = 0f
    }
}
