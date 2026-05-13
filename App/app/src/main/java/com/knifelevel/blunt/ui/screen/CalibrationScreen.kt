package com.knifelevel.blunt.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.knifelevel.blunt.viewmodel.DeviceViewModel

@Composable
fun CalibrationScreen(
    deviceVm: DeviceViewModel,
    onBack: () -> Unit,
) {
    val angle            by deviceVm.angle.collectAsState()
    val calibrationAngle by deviceVm.calibrationAngle.collectAsState()

    var status by remember { mutableStateOf("") }

    Column(
        modifier = Modifier.fillMaxSize().padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("CALIBRATION", style = MaterialTheme.typography.labelLarge)
        Spacer(modifier = Modifier.height(64.dp))
        Text("CURRENT READING", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.secondary)
        Text(
            text = if (angle != null) "${"%.2f".format(angle)}°" else "--°",
            style = MaterialTheme.typography.displayLarge,
            color = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.weight(1f))
        if (status.isNotEmpty()) {
            Text(text = status, modifier = Modifier.padding(bottom = 8.dp), style = MaterialTheme.typography.bodySmall)
        }
        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack) { Text("← Back") }
            Button(onClick = {
                deviceVm.calibrate()
            }) { Text("Apply") }
        }
    }
}
