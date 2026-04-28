package com.knifelevel.hello

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

@Composable
fun PresetScreen(
    presets: List<PresetEntry>,
    presetsLoaded: Boolean,
    settingsLoaded: Boolean,
    status: String,
    waitingForReconnect: Boolean,
    backupAvailable: Boolean,
    onAddPreset: (String, String) -> Unit,
    onUpdatePreset: (Int, String, String) -> Unit,
    onDeletePreset: (Int) -> Unit,
    onSelectPreset: (String) -> Unit,
    onSaveToDevice: () -> Unit,
    onSaveBackup: () -> Unit,
    onRestoreBackup: () -> Unit,
    onBack: () -> Unit,
) {
    val editorState = remember { mutableStateOf<PresetEditorState?>(null) }

    if (editorState.value != null) {
        PresetEditorDialog(
            state = editorState.value!!,
            onDismiss = { editorState.value = null }
        ) { name, angle ->
            val index = editorState.value!!.index
            if (index == null) {
                onAddPreset(name, angle)
            } else {
                onUpdatePreset(index, name, angle)
            }
            editorState.value = null
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp)
    ) {
        Spacer(modifier = Modifier.height(16.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            TextButton(onClick = onBack, enabled = !waitingForReconnect) { Text("← Back") }
            Text("Preset Angles", style = MaterialTheme.typography.titleLarge)
            Button(
                onClick = { editorState.value = PresetEditorState() },
                enabled = presetsLoaded && !waitingForReconnect
            ) { Text("Add") }
        }

        if (status.isNotEmpty()) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = status,
                style = MaterialTheme.typography.bodySmall,
                color = if (status.startsWith("err") || status.startsWith("Err")) {
                    MaterialTheme.colorScheme.error
                } else {
                    MaterialTheme.colorScheme.primary
                }
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (!presetsLoaded || !settingsLoaded) {
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

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = onSaveToDevice,
                modifier = Modifier.weight(1f)
            ) { Text("Save To Device") }
            OutlinedButton(
                onClick = onSaveBackup,
                modifier = Modifier.weight(1f)
            ) { Text("Save Backup") }
        }

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedButton(
            onClick = onRestoreBackup,
            enabled = backupAvailable,
            modifier = Modifier.fillMaxWidth()
        ) { Text("Restore Backup") }

        Spacer(modifier = Modifier.height(12.dp))

        if (presets.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No preset angles yet.")
            }
            return@Column
        }

        LazyColumn {
            itemsIndexed(presets) { index, preset ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(preset.name, style = MaterialTheme.typography.bodyLarge)
                        Spacer(modifier = Modifier.height(2.dp))
                        Text("${preset.angle}°", style = MaterialTheme.typography.bodySmall)
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton(onClick = { onSelectPreset(preset.angle) }) {
                            Text("Select")
                        }
                        TextButton(onClick = {
                            editorState.value = PresetEditorState(index, preset.name, preset.angle)
                        }) {
                            Text("Edit")
                        }
                        TextButton(onClick = { onDeletePreset(index) }) {
                            Text("Delete")
                        }
                    }
                }
                HorizontalDivider()
            }
        }
    }
}

data class PresetEditorState(
    val index: Int? = null,
    val name: String = "",
    val angle: String = ""
)

@Composable
fun PresetEditorDialog(
    state: PresetEditorState,
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit
) {
    var name by remember(state) { mutableStateOf(state.name) }
    var angle by remember(state) { mutableStateOf(state.angle) }
    val validName = name.isNotBlank() && !name.contains(',') && !name.contains(':')
    val valid = validName && (angle.toFloatOrNull() != null)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (state.index == null) "Add Preset" else "Edit Preset") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Name") },
                    singleLine = true,
                    supportingText = { Text("No commas or colons") },
                    isError = !validName && name.isNotEmpty()
                )
                OutlinedTextField(
                    value = angle,
                    onValueChange = { angle = it },
                    label = { Text("Angle") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal)
                )
            }
        },
        confirmButton = {
            Button(onClick = { onConfirm(name.trim(), angle.trim()) }, enabled = valid) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}