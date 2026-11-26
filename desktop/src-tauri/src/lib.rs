use serde::{Deserialize, Serialize};
use tauri_plugin_dialog::DialogExt;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DocumentMetadata {
    pub id: String,
    pub path: String,
    pub file_name: String,
    pub file_size: u64,
    pub mime_type: String,
    pub document_type: String,
    pub status: String,
    pub version: i32,
    pub page_count: Option<i32>,
    pub language: Option<String>,
    pub has_text_layer: bool,
    pub ocr_confidence: Option<f64>,
    pub created_at: String,
    pub updated_at: String,
    pub folder_id: Option<String>,
    pub owner_id: Option<String>,
}

#[tauri::command]
fn get_status() -> Result<String, String> {
    Ok("BARGEHAM desktop client ready".to_string())
}

/// باز کردن دایلاگ انتخاب پوشه در سیستم فایل میزبان و برگشت مسیر انتخاب‌شده
#[tauri::command]
async fn pick_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let folder_path = app.dialog().file().blocking_pick_folder();
    Ok(folder_path.map(|p| p.to_string()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![get_status, pick_folder])
        .run(tauri::generate_context!())
        .expect("error while building tauri application");
}