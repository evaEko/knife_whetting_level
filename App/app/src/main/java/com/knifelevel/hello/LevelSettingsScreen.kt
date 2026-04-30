package com.knifelevel.hello

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun LevelSettingsContent(
    draft: MutableMap<String, String>,
    modifier: Modifier = Modifier,
) {
    LazyColumn(modifier = modifier) {
        item {
            ExpandableSection("Displayed Data") {
                BoolSetting("Preset Name", draft["show_preset_name"] == "true") { draft["show_preset_name"] = it.toString() }
                BoolSetting("Target Angle", draft["show_target_angle"] == "true") { draft["show_target_angle"] = it.toString() }
                BoolSetting("Load Target Angle on Boot", draft["load_target_angle_from_eeprom"] == "true") { draft["load_target_angle_from_eeprom"] = it.toString() }
            }
        }
        item {
            ExpandableSection("Measurement") {
                EnumSetting("Axis", draft["angle_axis"] ?: "pitch", listOf("pitch", "roll"), compact = true) { draft["angle_axis"] = it }
                EnumSetting("Format", draft["angle_format"] ?: "1d_half", listOf("2d", "1d", "1d_half"), compact = true) { draft["angle_format"] = it }
                SliderSetting("Smoothing", draft["smoothing"]?.toFloatOrNull() ?: 0.7f, 0.3f, 0.9f, 5) { draft["smoothing"] = "%.1f".format(it) }
                StepperSetting("Deviation Threshold (°)", draft["deviation_threshold"]?.toIntOrNull() ?: 1, 1, 10) { draft["deviation_threshold"] = it.toString() }
            }
        }
    }
}

@Composable
fun SectionHeader(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.secondary,
        modifier = Modifier.padding(vertical = 8.dp)
    )
}

@Composable
fun BoolSetting(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label)
        Switch(checked = value, onCheckedChange = onChange)
    }
}

@Composable
fun EnumSetting(label: String, value: String, options: List<String>, compact: Boolean = false, onChange: (String) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val pad = if (compact) PaddingValues(horizontal = 10.dp, vertical = 4.dp) else PaddingValues(horizontal = 16.dp, vertical = 8.dp)
            val textStyle = if (compact) MaterialTheme.typography.labelSmall else MaterialTheme.typography.labelLarge
            options.forEach { option ->
                if (option == value) {
                    Button(onClick = {}, contentPadding = pad) { Text(option, style = textStyle) }
                } else {
                    OutlinedButton(onClick = { onChange(option) }, contentPadding = pad) { Text(option, style = textStyle) }
                }
            }
        }
    }
}

@Composable
fun SliderSetting(label: String, value: Float, min: Float, max: Float, steps: Int, onChange: (Float) -> Unit) {
    var current by remember(value) { mutableStateOf(value) }
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
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
        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
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
