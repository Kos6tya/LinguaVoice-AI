package com.example.linguavoice

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody

class MainActivity : ComponentActivity() {
    private lateinit var audioController: AudioController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        audioController = AudioController(this)

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ChatScreen(audioController)
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        audioController.release()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(audioController: AudioController) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val apiService = remember { ApiService.create() }

    val messages = remember { mutableStateListOf<UiMessage>() }
    val chatHistory = remember { mutableStateListOf<Map<String, String>>() }

    var isRecording by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (!isGranted) {
            Toast.makeText(context, "Потрібен дозвіл на мікрофон!", Toast.LENGTH_SHORT).show()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("LinguaVoice Tutor (Groq AI)") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages) { msg ->
                    MessageBubble(msg)
                }
            }

            if (isLoading) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp))
                    Spacer(modifier = Modifier.width(12.dp))
                    Text("ШІ перевіряє вимову та генерує відповідь...", fontSize = 14.sp)
                }
            }

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.White)
                    .padding(vertical = 16.dp),
                contentAlignment = Alignment.Center
            ) {
                IconButton(
                    onClick = {
                        val hasPermission = ContextCompat.checkSelfPermission(
                            context, Manifest.permission.RECORD_AUDIO
                        ) == PackageManager.PERMISSION_GRANTED

                        if (!hasPermission) {
                            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            return@IconButton
                        }

                        if (!isRecording) {
                            audioController.startRecording()
                            isRecording = true
                        } else {
                            isRecording = false
                            val file = audioController.stopRecording()
                            if (file != null && file.exists()) {
                                isLoading = true
                                coroutineScope.launch {
                                    try {
                                        val reqFile = file.asRequestBody("audio/m4a".toMediaTypeOrNull())
                                        val audioPart = MultipartBody.Part.createFormData("audio", file.name, reqFile)
                                        val historyJson = Gson().toJson(chatHistory)
                                        val historyBody = historyJson.toRequestBody("text/plain".toMediaTypeOrNull())

                                        val response = apiService.sendVoiceTurn(audioPart, historyBody)
                                        if (response.isSuccessful && response.body() != null) {
                                            val data = response.body()!!

                                            messages.add(UiMessage(data.userTranscript, true, data.corrections))
                                            messages.add(UiMessage(data.aiResponse, false))

                                            chatHistory.add(mapOf("role" to "user", "content" to data.userTranscript))
                                            chatHistory.add(mapOf("role" to "assistant", "content" to data.aiResponse))

                                            data.audioBase64?.let { base64 ->
                                                audioController.playAudioFromBase64(base64)
                                            }
                                        } else {
                                            Toast.makeText(context, "Помилка сервера: ${response.code()}", Toast.LENGTH_SHORT).show()
                                        }
                                    } catch (e: Exception) {
                                        Toast.makeText(context, "Збій зв'язку: ${e.message}", Toast.LENGTH_LONG).show()
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }
                        }
                    },
                    modifier = Modifier
                        .size(72.dp)
                        .clip(CircleShape)
                        .background(if (isRecording) Color.Red else MaterialTheme.colorScheme.primary)
                ) {
                    Icon(
                        imageVector = if (isRecording) Icons.Default.Stop else Icons.Default.Mic,
                        contentDescription = "Мікрофон",
                        tint = Color.White,
                        modifier = Modifier.size(36.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun MessageBubble(msg: UiMessage) {
    val alignment = if (msg.isUser) Alignment.End else Alignment.Start
    val bgColor = if (msg.isUser) Color(0xFFD1C4E9) else Color(0xFFEEEEEE)

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = alignment
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 280.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(bgColor)
                .padding(12.dp)
        ) {
            Column {
                Text(text = msg.text, fontSize = 16.sp, color = Color.Black)

                if (msg.corrections.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    HorizontalDivider(thickness = 1.dp, color = Color.Gray.copy(alpha = 0.5f))
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "🔍 Зауваження репетитора:",
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = Color(0xFFD84315)
                    )
                    msg.corrections.forEach { c ->
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "❌ ${c.original}\n✅ ${c.correction}\n💡 ${c.explanation}",
                            fontSize = 12.sp,
                            color = Color.Black
                        )
                    }
                }
            }
        }
    }
}