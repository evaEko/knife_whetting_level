package com.knifelevel.blunt.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.knifelevel.blunt.AppSettingsContent
import com.knifelevel.blunt.LevelSettingsContent
import com.knifelevel.blunt.viewmodel.AppSettingsViewModel
import com.knifelevel.blunt.viewmodel.DeviceViewModel

@Composable
fun SettingsScreen(
    deviceVm: DeviceViewModel,
    settingsVm: AppSettingsViewModel,
    onBack: () -> Unit,
) {
    val appSettings   by settingsVm.settings.collectAsState()
    val deviceSettings by deviceVm.deviceSettings.collectAsState()
    val settingsReady  by deviceVm.settingsReady.collectAsState()

    var selectedTab by remember { mutableStateOf(0) }
    var saveStatus  by remember { mutableStateOf("") }

    LaunchedEffect(Unit) { deviceVm.refreshPresetsAndSettings() }

    val draft = remember { mutableStateMapOf<String, String>() }
    LaunchedEffect(settingsReady) {
        if (settingsReady) { draft.clear(); draft.putAll(deviceSettings) }
    }
    LaunchedEffect(deviceSettings["deviation_threshold"]) {
        deviceSettings["deviation_threshold"]?.let { draft["deviation_threshold"] = it }
    }
    LaunchedEffect(deviceSettings["capture_delay_sec"]) {
        deviceSettings["capture_delay_sec"]?.let { draft["capture_delay_sec"] = it }
    }

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        Spacer(modifier = Modifier.height(48.dp))
        TabRow(selectedTabIndex = selectedTab) {
            Tab(selected = selectedTab == 0, onClick = { selectedTab = 0 },
                text = { Text("Application", style = MaterialTheme.typography.titleLarge) })
            Tab(selected = selectedTab == 1, onClick = { selectedTab = 1 },
                text = { Text("Level", style = MaterialTheme.typography.titleLarge) })
        }
        when (selectedTab) {
            0 -> AppSettingsContent(
                modifier                 = Modifier.weight(1f),
                angleFormat              = appSettings.angleFormat,
                deviationBackgroundEnabled = appSettings.deviationBackgroundEnabled,
                displayArrow             = appSettings.displayArrow,
                soundTooHighEnabled      = appSettings.soundTooHighEnabled,
                soundTooLowEnabled       = appSettings.soundTooLowEnabled,
                highToneFreq             = appSettings.highToneFreq,
                lowToneFreq              = appSettings.lowToneFreq,
                showTargetName           = appSettings.showTargetName,
                showTargetAngle          = appSettings.showTargetAngle,
                showDelta                = appSettings.showDelta,
                customAngleCountdownSec  = appSettings.customAngleCountdownSec,
                tooHighColorLabel        = appSettings.tooHighColorLabel,
                tooLowColorLabel         = appSettings.tooLowColorLabel,
                arrowSize                = appSettings.arrowSize,
                customSmallAudioUri      = appSettings.customSmallAudioUri,
                customBigAudioUri        = appSettings.customBigAudioUri,
                onTargetSoundEnabled     = appSettings.onTargetSoundEnabled,
                onTargetContinueOnLifted = appSettings.onTargetContinueOnLifted,
                customOnTargetAudioUri   = appSettings.customOnTargetAudioUri,
                showDeviationRange       = appSettings.showDeviationRange,
                liftedDetectionEnabled   = appSettings.liftedDetectionEnabled,
                liftedVelThreshold       = appSettings.liftedVelThreshold,
                liftedDebounceMs         = appSettings.liftedDebounceMs,
                onSave                   = { settingsVm.save(it) },
            )
            1 -> when {
                !settingsReady -> Box(modifier = Modifier.weight(1f).fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
                else -> LevelSettingsContent(draft = draft, modifier = Modifier.weight(1f))
            }
        }
        if (selectedTab == 1 && saveStatus.isNotEmpty()) {
            Text(text = saveStatus, style = MaterialTheme.typography.bodySmall,
                color = if (saveStatus.startsWith("err") || saveStatus.startsWith("Err")) MaterialTheme.colorScheme.error
                        else MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(4.dp))
        }
        Row(modifier = Modifier.fillMaxWidth().padding(bottom = 32.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("← Back") }
            if (selectedTab == 1) {
                Button(
                    onClick = {
                        saveStatus = "Saving..."
                        deviceVm.saveLevelSettings(draft.toMap()) { saveStatus = "Saved." }
                    },
                    enabled = settingsReady && saveStatus != "Saving..."
                ) { Text("Apply") }
            }
        }
    }
}
