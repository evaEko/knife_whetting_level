package com.knifelevel.blunt.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.knifelevel.blunt.model.PresetEntry
import com.knifelevel.blunt.viewmodel.DeviceViewModel

@Composable
fun PresetScreen(
    deviceVm: DeviceViewModel,
    onBack: () -> Unit,
) {
    val presets        by deviceVm.presets.collectAsState()
    val presetsReady   by deviceVm.presetsReady.collectAsState()
    val settingsReady  by deviceVm.settingsReady.collectAsState()
    val targetAngle    by deviceVm.targetAngle.collectAsState()
    val angle          by deviceVm.angle.collectAsState()

    val currentTargetStr = targetAngle?.let { "%.2f".format(it) } ?: ""
    val currentAngleStr  = angle?.let { "%.2f".format(it) } ?: "--"

    val captureCountdown by deviceVm.captureCountdown.collectAsState()
    var localPresets by remember { mutableStateOf(presets) }
    var status       by remember { mutableStateOf("") }
    val editorState = remember { mutableStateOf<PresetEditorState?>(null) }

    LaunchedEffect(Unit) { deviceVm.refreshPresetsAndSettings() }
    LaunchedEffect(presetsReady) { if (presetsReady) localPresets = presets }

    if (editorState.value != null) {
        PresetEditorDialog(
            state = editorState.value!!,
            onDismiss = { editorState.value = null }
        ) { name, angleStr ->
            val idx = editorState.value!!.index
            localPresets = if (idx == null) localPresets + PresetEntry(name, angleStr)
                           else localPresets.toMutableList().also { it[idx] = PresetEntry(name, angleStr) }
            editorState.value = null
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        Spacer(modifier = Modifier.height(48.dp))
        if (status.isNotEmpty()) {
            Text(
                text = status,
                style = MaterialTheme.typography.bodySmall,
                color = if (status.startsWith("err") || status.startsWith("Err")) MaterialTheme.colorScheme.error
                        else MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(4.dp))
        }
        if (!presetsReady || !settingsReady) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            return@Column
        }
        HorizontalDivider()
        Row(
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Set current reading as target", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.secondary)
            Button(
                onClick = {
                    angle?.let { deviceVm.captureAngle(it) }
                    onBack()
                },
                enabled = currentAngleStr != "--" && captureCountdown < 0,
            ) { Text(if (captureCountdown > 0) "${captureCountdown}s…" else "CAPTURE") }
        }
        HorizontalDivider()
        Spacer(modifier = Modifier.height(8.dp))
        if (localPresets.isEmpty()) {
            Box(modifier = Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                Text("No preset angles yet.")
            }
        } else {
            LazyColumn(modifier = Modifier.weight(1f)) {
                itemsIndexed(localPresets) { index, preset ->
                    val isActive = targetAngle?.let { t -> preset.angle.toFloatOrNull()?.let { p -> kotlin.math.abs(p - t) < 0.01f } } == true
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(
                            modifier = Modifier.weight(1f).clickable { deviceVm.setTargetAngle(preset.angle.toFloatOrNull() ?: 0f) }.padding(vertical = 4.dp)
                        ) {
                            Text(preset.name, style = MaterialTheme.typography.bodyLarge, fontWeight = if (isActive) FontWeight.Bold else null)
                            Spacer(modifier = Modifier.height(2.dp))
                            Text("${preset.angle}°", style = MaterialTheme.typography.bodySmall)
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TextButton(onClick = { editorState.value = PresetEditorState(index, preset.name, preset.angle) }) { Text("✏", fontSize = 20.sp) }
                            TextButton(onClick = { localPresets = localPresets.toMutableList().also { it.removeAt(index) } }) { Text("🗑") }
                        }
                    }
                    HorizontalDivider()
                }
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 32.dp, top = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                if (currentTargetStr.toFloatOrNull()?.let { it > 0f } == true) {
                    TextButton(onClick = { deviceVm.clearTarget() }) {
                        Text("Clear", color = MaterialTheme.colorScheme.error)
                    }
                }
                OutlinedButton(onClick = { editorState.value = PresetEditorState() }, enabled = presetsReady) { Text("+") }
                Button(
                    onClick = {
                        status = "Saving presets..."
                        deviceVm.savePresets(localPresets) { status = "Presets saved." }
                        onBack()
                    },
                    enabled = presetsReady
                ) { Text("OK") }
            }
        }
    }
}

private data class PresetEditorState(val index: Int? = null, val name: String = "", val angle: String = "")

@Composable
private fun PresetEditorDialog(state: PresetEditorState, onDismiss: () -> Unit, onConfirm: (String, String) -> Unit) {
    var name  by remember(state) { mutableStateOf(state.name) }
    var angle by remember(state) { mutableStateOf(state.angle) }
    val validName = name.isNotBlank() && !name.contains(',') && !name.contains(':')
    val valid = validName && (angle.toFloatOrNull() != null)
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (state.index == null) "Add Preset" else "Edit Preset") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name") }, singleLine = true,
                    supportingText = { Text("No commas or colons") }, isError = !validName && name.isNotEmpty())
                OutlinedTextField(value = angle, onValueChange = { angle = it }, label = { Text("Angle") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal))
            }
        },
        confirmButton = { Button(onClick = { onConfirm(name.trim(), angle.trim()) }, enabled = valid) { Text("Save") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
