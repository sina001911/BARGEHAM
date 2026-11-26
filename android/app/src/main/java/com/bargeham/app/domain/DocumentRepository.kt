package com.bargeham.app.domain

import android.content.Context
import com.bargeham.app.data.AppDatabase
import com.bargeham.app.data.DocumentDao
import com.bargeham.app.data.DocumentEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class DocumentRepository(private val database: AppDatabase) {
    private val dao: DocumentDao = database.documentDao()

    suspend fun insert(document: DocumentEntity): Long = dao.insert(document)

    suspend fun getAll(): List<DocumentEntity> = dao.getAll()

    suspend fun getById(id: Int): DocumentEntity? = dao.getById(id)

    suspend fun delete(id: Int) = dao.delete(id)

    suspend fun getByStatus(status: String): List<DocumentEntity> = dao.getByStatus(status)

    fun getAllFlow(): Flow<List<DocumentEntity>> = flow {
        emit(dao.getAll())
    }
}