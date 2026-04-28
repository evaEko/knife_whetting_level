package com.knifelevel.hello

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
    onSave: (Map<String, String>) -> Unit,
    onBack: () -> Unit,
) {
    // Local draft — edits stay here until Save is pressed
    val draft = remember { mutableStateMapOf<String, String>() }

    LaunchedEffect(settingsLoaded) {
        if (settingsLoaded) {
            draft.clear()
            draft.putAll(settings)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
    ) {
        Spacer(modifier = Modifier.height(16.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            TextButton(onClick = onBack, enabled = !waitingForReconnect) { Text("← Back") }
            Text("Settings", style = MaterialTheme.typography.titleLarge)
            Button(
                onClick = { onSave(draft.toMap()) },
                enabled = (settingsLoaded) && (saveStatus != "Saving...") && (!waitingForReconnect)
            ) { Text("Save") }
        }

        if (saveStatus.isNotEmpty()) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = saveStatus,
                style = MaterialTheme.typography.bodySmall,
                color = if (saveStatus.startsWith("err") || saveStatus.startsWith("Err"))
                    MaterialTheme.colorScheme.error
                else
                    MaterialTheme.colorScheme.primary
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        if (!settingsLoaded) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return@Column
        }

        if (waitingForReconnect) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Reconnecting to device...")
                }
            }
            return@Column
        }

        LazyColumn {
            item {
                BoolSetting(
                    label = "Show Preset Name",
                    value = draft["show_preset_name"] == "true"
                ) { draft["show_preset_name"] = it.toString() }
                HorizontalDivider()
            }
            item {
                BoolSetting(
                    label = "Show Target Angle",
                    value = draft["show_target_angle"] == "true"
                ) { draft["show_target_angle"] = it.toString() }
                HorizontalDivider()
            }
            item {
                BoolSetting(
                    label = "Load Target Angle on Boot",
                    value = draft["load_target_angle_from_eeprom"] == "true"
                ) { draft["load_target_angle_from_eeprom"] = it.toString() }
                HorizontalDivider()
            }
            item {
                EnumSetting(
                    label = "Angle Axis",
                    value = draft["angle_axis"] ?: "pitch",
                    options = listOf("pitch", "roll")
                ) { draft["angle_axis"] = it }
                HorizontalDivider()
            }
            item {
                EnumSetting(
                    label = "Angle Format",
                    value = draft["angle_format"] ?: "1d_half",
                    options = listOf("2d", "1d", "1d_half")
                ) { draft["angle_format"] = it }
                HorizontalDivider()
            }
            item {
                SliderSetting(
                    label = "Smoothing",
                    value = draft["smoothing"]?.toFloatOrNull() ?: 0.7f,
                    min = 0.3f,
                    max = 0.9f,
                    steps = 5
                ) { draft["smoothing"] = "%.1f".format(it) }
                HorizontalDivider()
            }
            item {
                StepperSetting(
                    label = "Deviation Threshold (°)",
                    value = draft["deviation_threshold"]?.toIntOrNull() ?: 1,
                    min = 1,
                    max = 10
                ) { draft["deviation_threshold"] = it.toString() }
            }
        }
    }
}

@Composable
fun BoolSetting(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label)
        Switch(checked = value, onCheckedChange = onChange)
    }
}

@Composable
fun EnumSetting(label: String, value: String, options: List<String>, onChange: (String) -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { option ->
                if (option == value) {
                    Button(onClick = {}) { Text(option) }
                } else {
                    OutlinedButton(onClick = { onChange(option) }) { Text(option) }
                }
            }
        }
    }
}

@Composable
fun SliderSetting(label: String, value: Float, min: Float, max: Float, steps: Int, onChange: (Float) -> Unit) {
    var current by remember(value) { mutableStateOf(value) }
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(label)
            Text("%.1f".format(current))
        }
        Slider(
            value = current,
            onValueChange = { current = it },
            onValueChangeFinished = { onChange(current) },
            valueRange = min..max,
            steps = steps
        )
    }
}

@Composable
fun StepperSetting(label: String, value: Int, min: Int, max: Int, onChange: (Int) -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label)
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(
                onClick = { if (value > min) onChange(value - 1) },
                enabled = value > min,
                modifier = Modifier.size(40.dp),
                contentPadding = PaddingValues(0.dp),
            ) { Text("-") }
            Text(
                value.toString(),
                modifier = Modifier.padding(horizontal = 12.dp),
                style = MaterialTheme.typography.bodyLarge
            )
            OutlinedButton(
                onClick = { if (value < max) onChange(value + 1) },
                enabled = value < max,
                modifier = Modifier.size(40.dp),
                contentPadding = PaddingValues(0.dp),
            ) { Text("+") }
        }
    }
}
