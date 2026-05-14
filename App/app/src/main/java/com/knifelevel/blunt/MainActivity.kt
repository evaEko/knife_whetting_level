package com.knifelevel.blunt

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.knifelevel.blunt.ble.BleManager
import com.knifelevel.blunt.navigation.AppNavigation
import com.knifelevel.blunt.repository.AppSettingsRepository
import com.knifelevel.blunt.repository.DeviceRepository
import com.knifelevel.blunt.ui.theme.MyApplicationTheme
import com.knifelevel.blunt.viewmodel.AppSettingsViewModelFactory
import com.knifelevel.blunt.viewmodel.DeviceViewModelFactory

class MainActivity : ComponentActivity() {

    private val bleManager      by lazy { BleManager(applicationContext) }
    private val deviceRepo      by lazy { DeviceRepository(bleManager) }
    private val appSettingsRepo by lazy { AppSettingsRepository(applicationContext) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    PermissionGate {
                        val deviceVm   = viewModel<com.knifelevel.blunt.viewmodel.DeviceViewModel>(factory = DeviceViewModelFactory(deviceRepo, appSettingsRepo))
                        val settingsVm = viewModel<com.knifelevel.blunt.viewmodel.AppSettingsViewModel>(factory = AppSettingsViewModelFactory(appSettingsRepo))
                        AppNavigation(deviceVm = deviceVm, settingsVm = settingsVm)
                    }
                }
            }
        }
    }
}

@Composable
private fun PermissionGate(content: @Composable () -> Unit) {
    var granted by remember { mutableStateOf(false) }
    val permissions = arrayOf(
        Manifest.permission.BLUETOOTH_SCAN,
        Manifest.permission.BLUETOOTH_CONNECT,
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION,
    )
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        granted = result.values.all { it }
    }
    val context = androidx.compose.ui.platform.LocalContext.current
    LaunchedEffect(Unit) {
        val allGranted = permissions.all {
            context.checkSelfPermission(it) == android.content.pm.PackageManager.PERMISSION_GRANTED
        }
        if (allGranted) granted = true else launcher.launch(permissions)
    }
    if (granted) content()
}
