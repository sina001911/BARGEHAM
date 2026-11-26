package com.bargeham.app.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface DocumentDao {
    @Insert
    suspend fun insert(document: DocumentEntity): Long

    @Update
    suspend fun update(document: DocumentEntity)

    @Query("SELECT * FROM documents ORDER BY createdAt DESC")
    suspend fun getAll(): List<DocumentEntity>

    @Query("SELECT * FROM documents WHERE id = :id")
    suspend fun getById(id: Int): DocumentEntity?

    @Query("DELETE FROM documents WHERE id = :id")
    suspend fun delete(id: Int)

    @Query("SELECT * FROM documents WHERE status = :status ORDER BY createdAt DESC")
    suspend fun getByStatus(status: String): List<DocumentEntity>

    @Query("SELECT COUNT(*) FROM documents")
    suspend fun count(): Int
}