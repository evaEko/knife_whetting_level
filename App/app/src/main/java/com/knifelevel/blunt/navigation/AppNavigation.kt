package com.knifelevel.blunt.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.knifelevel.blunt.ui.screen.CalibrationScreen
import com.knifelevel.blunt.ui.screen.ConnectScreen
import com.knifelevel.blunt.ui.screen.LiveScreen
import com.knifelevel.blunt.ui.screen.PresetScreen
import com.knifelevel.blunt.ui.screen.SettingsScreen
import com.knifelevel.blunt.viewmodel.AppSettingsViewModel
import com.knifelevel.blunt.viewmodel.DeviceViewModel

enum class Route { CONNECT, LIVE, SETTINGS, CALIBRATE, PRESETS }

@Composable
fun AppNavigation(
    deviceVm: DeviceViewModel,
    settingsVm: AppSettingsViewModel,
    navController: NavHostController = rememberNavController(),
) {
    NavHost(navController = navController, startDestination = Route.CONNECT.name) {
        composable(Route.CONNECT.name) {
            ConnectScreen(
                deviceVm    = deviceVm,
                onConnected = { navController.navigate(Route.LIVE.name) {
                    popUpTo(Route.CONNECT.name) { inclusive = true }
                }},
                onSettings  = { navController.navigate(Route.SETTINGS.name) },
            )
        }
        composable(Route.LIVE.name) {
            LiveScreen(
                deviceVm    = deviceVm,
                settingsVm  = settingsVm,
                onSettings  = { navController.navigate(Route.SETTINGS.name) },
                onPresets   = { navController.navigate(Route.PRESETS.name) },
                onCalibrate = { navController.navigate(Route.CALIBRATE.name) },
                onDisconnect = {
                    navController.navigate(Route.CONNECT.name) {
                        popUpTo(Route.CONNECT.name) { inclusive = true }
                    }
                },
            )
        }
        composable(Route.SETTINGS.name) {
            SettingsScreen(
                deviceVm   = deviceVm,
                settingsVm = settingsVm,
                onBack     = { navController.popBackStack() },
            )
        }
        composable(Route.CALIBRATE.name) {
            CalibrationScreen(
                deviceVm = deviceVm,
                onBack   = { navController.popBackStack() },
            )
        }
        composable(Route.PRESETS.name) {
            PresetScreen(
                deviceVm = deviceVm,
                onBack   = { navController.popBackStack() },
            )
        }
    }
}
