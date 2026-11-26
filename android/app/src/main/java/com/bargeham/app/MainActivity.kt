package com.bargeham.app

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.bargeham.app.data.AppDatabase
import com.bargeham.app.domain.DocumentRepository
import com.bargeham.app.domain.DocumentService
import com.bargeham.app.domain.OcrService
import com.bargeham.app.ui.DocumentListScreen
import com.bargeham.app.ui.MainScreen
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {

    private val openDocumentTreeLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri != null) {
                takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
                val context = this
                val prefs = getSharedPreferences("bargeham_prefs", MODE_PRIVATE)
                prefs.edit().putString("selected_folder_uri", uri.toString()).apply()
                // Navigate to documents list
                currentScreen.value = Screen.Documents
            }
        }

    private val database = AppDatabase.getDatabase(applicationContext)
    private val documentRepository = DocumentRepository(database)
    private val ocrService = OcrService(applicationContext)
    private val documentService = DocumentService(applicationContext, documentRepository, ocrService)

    private val currentScreen = mutableStateOf<Screen>(Screen.Main)

    enum class Screen {
        Main, Documents, Search, Ask, DocumentDetail
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            when (currentScreen.value) {
                Screen.Main -> MainScreen(
                    onOpenFolderClicked = {
                        openDocumentTreeLauncher.launch(null)
                    },
                    onDocumentsClicked = {
                        currentScreen.value = Screen.Documents
                    },
                    onSearchClicked = {
                        currentScreen.value = Screen.Search
                    },
                    onAskClicked = {
                        currentScreen.value = Screen.Ask
                    }
                )
                Screen.Documents -> DocumentListScreen(
                    documents = emptyList(),
                    onDocumentClick = {
                        currentScreen.value = Screen.DocumentDetail
                    }
                )
                Screen.Search -> SearchScreen()
                Screen.Ask -> AskScreen()
                Screen.DocumentDetail -> DocumentDetailScreen()
            }
        }
    }

    @Composable
    fun SearchScreen() {
        Scaffold {
            TopAppBar(
                title = { Text(text = "Search Documents") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        } { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
            ) {
                Text(
                    text = "Search Documents",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }

    @Composable
    fun AskScreen() {
        Scaffold {
            TopAppBar(
                title = { Text(text = "Ask AI Assistant") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        } { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
            ) {
                Text(
                    text = "Ask AI Assistant",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }

    @Composable
    fun DocumentDetailScreen() {
        Scaffold {
            TopAppBar(
                title = { Text(text = "Document Detail") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        } { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
            ) {
                Text(
                    text = "Document Detail",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}