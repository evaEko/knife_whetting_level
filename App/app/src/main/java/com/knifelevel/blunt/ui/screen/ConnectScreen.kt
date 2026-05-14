package com.knifelevel.blunt.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.knifelevel.blunt.model.ConnectionState
import com.knifelevel.blunt.model.FoundDevice
import com.knifelevel.blunt.viewmodel.DeviceViewModel

@Composable
fun ConnectScreen(
    deviceVm: DeviceViewModel,
    onConnected: () -> Unit,
    onSettings: () -> Unit,
) {
    val connectionState by deviceVm.connectionState.collectAsState()
    val foundDevices    by deviceVm.foundDevices.collectAsState()

    LaunchedEffect(connectionState) {
        if (connectionState == ConnectionState.CONNECTED) onConnected()
    }

    val isScanning = connectionState == ConnectionState.SCANNING

    Box(modifier = Modifier.fillMaxSize().padding(top = 48.dp, start = 24.dp, end = 24.dp, bottom = 24.dp)) {
        TextButton(
            onClick = onSettings,
            modifier = Modifier.align(Alignment.TopEnd)
        ) { Text("⚙", style = MaterialTheme.typography.headlineMedium) }

        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.weight(1f))
            Text("Blunt", style = MaterialTheme.typography.headlineLarge, color = MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(48.dp))
            Button(
                onClick = { deviceVm.scan() },
                enabled = !isScanning,
                modifier = Modifier.fillMaxWidth().height(56.dp)
            ) { Text("Scan for Levels", style = MaterialTheme.typography.labelLarge) }
            Spacer(modifier = Modifier.weight(1f))

            if (isScanning || foundDevices.isNotEmpty()) {
                Column(modifier = Modifier.fillMaxWidth()) {
                    if (isScanning) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.padding(bottom = 8.dp)
                        ) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            Text("Scanning…", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                        }
                    }
                    foundDevices.forEach { device ->
                        DeviceRow(device = device, onConnect = { deviceVm.connect(it) })
                    }
                    if (!isScanning && foundDevices.isEmpty()) {
                        HorizontalDivider()
                        Text("No devices found.", style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.secondary,
                            modifier = Modifier.padding(vertical = 16.dp))
                    }
                }
            }
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun DeviceRow(device: FoundDevice, onConnect: (FoundDevice) -> Unit) {
    HorizontalDivider()
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            Text("Knife Level", style = MaterialTheme.typography.bodyLarge)
            Text(device.shortId, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(device.signalBars, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
            Button(onClick = { onConnect(device) }) { Text("Connect") }
        }
    }
}
