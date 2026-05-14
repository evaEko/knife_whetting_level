package com.knifelevel.blunt.model

data class FoundDevice(val address: String, val rssi: Int) {
    val shortId: String get() = address.takeLast(5)
    val signalBars: String get() = when {
        rssi >= -60 -> "▂▄▆█"
        rssi >= -70 -> "▂▄▆·"
        rssi >= -80 -> "▂▄··"
        else        -> "▂···"
    }
}

data class PresetEntry(val name: String, val angle: String)
