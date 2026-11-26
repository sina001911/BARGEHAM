package com.bargeham.app.domain

import android.content.Context
import com.bargeham.app.data.AppDatabase
import com.bargeham.app.data.DocumentEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DocumentService(
    private val context: Context,
    private val documentRepository: DocumentRepository,
    private val ocrService: OcrService
) {

    suspend fun processDocument(filePath: String, fileName: String, mimeType: String, fileSize: Long): Long {
        // Run OCR
        val ocrText = ocrService.recognizeText(filePath)

        // Create document entity
        val document = DocumentEntity(
            title = fileName,
            fileName = fileName,
            filePath = filePath,
            fileSize = fileSize,
            mimeType = mimeType,
            status = "ready",
            language = detectLanguage(ocrText),
            ocrConfidence = null, // TODO: Get confidence from OCR result
            classification = null, // TODO: Classify document
            contentHash = null // TODO: Calculate content hash
        )

        return documentRepository.insert(document)
    }

    private suspend fun detectLanguage(text: String): String {
        // Simple language detection - can be improved
        val persianChars = setOf('ا', 'ب', 'پ', 'ت', 'ث', 'ج', 'چ', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'ژ', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'گ', 'ل', 'م', 'ن', 'و', 'ه', 'ی')
        val persianCount = text.count { c -> c in persianChars }
        return if (persianCount > 0) "fa" else "en"
    }
}