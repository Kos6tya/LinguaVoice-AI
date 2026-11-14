package com.example.linguavoice

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import java.util.concurrent.TimeUnit
import okhttp3.OkHttpClient

interface ApiService {
    @Multipart
    @POST("api/v1/chat/voice-turn")
    suspend fun sendVoiceTurn(
        @Part audio: MultipartBody.Part,
        @Part("chat_history") history: RequestBody
    ): Response<VoiceTurnResponse>

    companion object {
        private const val BASE_URL = "http://127.0.0.1:8000/"

        fun create(): ApiService {
            val client = OkHttpClient.Builder()
                .connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(60, TimeUnit.SECONDS)
                .build()

            return Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService::class.java)
        }
    }
}