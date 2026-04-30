package com.knifelevel.hello

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SettingsScreen(
    settings: Map<String, String>,
    settingsLoaded: Boolean,
    saveStatus: String,
    waitingForReconnect: Boolean,
    onSaveLevel: (Map<String, String>) -> Unit,
    angleFormat: AppAngleFormat,
    deviationBackgroundEnabled: Boolean,
    displayArrow: Boolean,
    soundAlert: Boolean,
    highToneFreq: Float,
    lowToneFreq: Float,
    showTargetName: Boolean,
    showTargetAngle: Boolean,
    showDelta: Boolean,
    customAngleCountdownSec: Int,
    tooHighColorLabel: String,
    tooLowColorLabel: String,
    onSaveApp: (AppUiSettings) -> Unit,
    onBack: () -> Unit,
) {
    val draft = remember { mutableStateMapOf<String, String>() }
    LaunchedEffect(settingsLoaded) {
        if (settingsLoaded) {
            draft.clear()
            draft.putAll(settings)
        }
    }

    var selectedTab by remember { mutableStateOf(0) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
    ) {
        Spacer(modifier = Modifier.height(48.dp))

        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("Application", style = MaterialTheme.typography.titleLarge) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("Level", style = MaterialTheme.typography.titleLarge) }
            )
        }

        when (selectedTab) {
            0 -> AppSettingsContent(
                modifier = Modifier.weight(1f),
                angleFormat = angleFormat,
                deviationBackgroundEnabled = deviationBackgroundEnabled,
                displayArrow = displayArrow,
                soundAlert = soundAlert,
                highToneFreq = highToneFreq,
                lowToneFreq = lowToneFreq,
                showTargetName = showTargetName,
                showTargetAngle = showTargetAngle,
                showDelta = showDelta,
                customAngleCountdownSec = customAngleCountdownSec,
                tooHighColorLabel = tooHighColorLabel,
                tooLowColorLabel = tooLowColorLabel,
                onSave = onSaveApp,
            )
            1 -> when {
                !settingsLoaded -> Box(
                    modifier = Modifier.weight(1f).fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) { CircularProgressIndicator() }
                waitingForReconnect -> Box(
                    modifier = Modifier.weight(1f).fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Reconnecting to device...")
                    }
                }
                else -> LevelSettingsContent(draft = draft, modifier = Modifier.weight(1f))
            }
        }

        if (selectedTab == 1 && saveStatus.isNotEmpty()) {
            Text(
                text = saveStatus,
                style = MaterialTheme.typography.bodySmall,
                color = if (saveStatus.startsWith("err") || saveStatus.startsWith("Err"))
                    MaterialTheme.colorScheme.error
                else
                    MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(4.dp))
        }

        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 32.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack, enabled = !waitingForReconnect) { Text("← Back") }
            if (selectedTab == 1) {
                Button(
                    onClick = { onSaveLevel(draft.toMap()) },
                    enabled = settingsLoaded && saveStatus != "Saving..." && !waitingForReconnect
                ) { Text("Apply") }
            }
        }
    }
}
