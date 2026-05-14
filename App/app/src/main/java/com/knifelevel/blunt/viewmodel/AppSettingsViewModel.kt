package com.knifelevel.blunt.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.knifelevel.blunt.model.AppUiSettings
import com.knifelevel.blunt.repository.AppSettingsRepository
import kotlinx.coroutines.flow.StateFlow

class AppSettingsViewModel(private val repo: AppSettingsRepository) : ViewModel() {
    val settings: StateFlow<AppUiSettings> = repo.settings
    fun save(updated: AppUiSettings) = repo.save(updated)
}

class AppSettingsViewModelFactory(private val repo: AppSettingsRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return AppSettingsViewModel(repo) as T
    }
}
