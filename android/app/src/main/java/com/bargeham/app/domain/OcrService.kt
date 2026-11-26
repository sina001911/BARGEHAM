package com.bargeham.app.domain

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.TextRecognizer
import java.io.File

class OcrService(private val context: Context) {

    private val recognizer = TextRecognition.getClient()

    suspend fun recognizeText(filePath: String): String {
        val file = File(filePath)
        val bitmap = BitmapFactory.decodeFile(file.absolutePath)
        if (bitmap == null) {
            throw IllegalArgumentException("Cannot decode image from $filePath")
        }

        val inputImage = InputImage.fromBitmap(bitmap, 0)
        val result = recognizer.process(inputImage)
        return result.text
    }

    suspend fun recognizeTextFromBitmap(bitmap: Bitmap): String {
        val inputImage = InputImage.fromBitmap(bitmap, 0)
        val result = recognizer.process(inputImage)
        return result.text
    }
}