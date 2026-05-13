package com.knifelevel.blunt

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
            SliderSetting("Deviation Threshold (°)", draft["deviation_threshold"]?.toFloatOrNull() ?: 1.0f, 0.0f, 4.0f, 15) { draft["deviation_threshold"] = "%.2f".format(it) }
        }
        item {
            StepperSetting("Capture delay (s)", draft["capture_delay_sec"]?.toIntOrNull() ?: 5, 1, 30) { draft["capture_delay_sec"] = it.toString() }
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
fun BoolSetting(label: String, value: Boolean, description: String? = null, onChange: (Boolean) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, modifier = Modifier.weight(1f))
            Switch(checked = value, onCheckedChange = onChange)
        }
        if (description != null) {
            Text(description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
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
fun StepperSetting(label: String, value: Int, min: Int, max: Int, step: Int = 1, description: String? = null, onChange: (Int) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, modifier = Modifier.weight(1f))
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(
                onClick = { if (value > min) onChange((value - step).coerceAtLeast(min)) },
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
                onClick = { if (value < max) onChange((value + step).coerceAtMost(max)) },
                enabled = value < max,
                modifier = Modifier.size(40.dp),
                contentPadding = PaddingValues(0.dp),
            ) { Text("+") }
        }
    }
    if (description != null) {
        Text(description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
    }
}
